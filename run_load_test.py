"""
Análisis de ensayo de carga con elementos elásticos lineales
"""

import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry
from materials import MaterialManager

def run_incremental_load_test():
    print("\n" + "="*70)
    print("ENSAYO DE CARGA INCREMENTAL")
    print("="*70)

    # 1. Inicializar OpenSees
    print("\n[1] Inicializando modelo OpenSees...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    # 2. Generar malla
    print("\n[2] Generando malla...")
    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()

    # 3. Aplicar condiciones de borde
    print("\n[3] Aplicando condiciones de borde...")
    mesh.apply_boundary_conditions()

    # 4. Definir materiales
    print("\n[4] Definiendo materiales...")
    materials = MaterialManager()
    materials.define_all_materials()

    # 5. Crear elementos
    print("\n[5] Creando elementos...")

    # Elementos de suelo
    for elem_tag, elem_info in mesh.soil_elements.items():
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']
        mat_tag = layer_idx + 1
        ops.element('stdBrick', elem_tag, *nodes, mat_tag)

    # Elementos de zapata
    elem_counter = max(mesh.soil_elements.keys()) + 1
    for elem_info in mesh.footing_elements:
        nodes = elem_info['nodes']
        ops.element('stdBrick', elem_counter, *nodes, 4)  # Material 4 = concreto
        elem_counter += 1

    print(f"  Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos de zapata: {len(mesh.footing_elements)}")

    # 6. Identificar nodos de carga (superficie superior de zapata)
    print("\n[6] Identificando nodos de carga...")
    z_top = -EMBEDMENT_DEPTH
    load_nodes = []

    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(z - z_top) < 0.01:
            if x >= FOOTING_START_X and x <= FOOTING_END_X:
                if y >= FOOTING_START_Y and y <= FOOTING_END_Y:
                    load_nodes.append(node_tag)

    print(f"  Nodos de carga: {len(load_nodes)}")

    # 7. Configurar análisis
    print("\n[7] Configurando análisis...")
    ops.constraints('Transformation')
    ops.numberer('RCM')
    ops.system('BandGeneral')
    ops.test('NormDispIncr', 1.0e-4, 25)  # Tolerancia más relajada
    ops.algorithm('Linear')  # Algoritmo lineal para material elástico
    ops.analysis('Static')

    # 8. Ensayo de carga incremental
    print("\n[8] Ejecutando ensayo de carga incremental...")

    # Usar carga del config pero para modelo 1/4
    max_load = LOAD_TEST['max_load'] / 4  # Dividir por 4 para modelo de simetría
    num_steps = 5  # Reducir pasos para análisis más rápido
    load_increment = max_load / num_steps

    print(f"  Carga máxima (1/4): {max_load:.1f} kN")
    print(f"  Incrementos: {num_steps}")
    print(f"  Incremento: {load_increment:.2f} kN/paso")

    # Almacenar resultados
    loads = []
    settlements = []

    print(f"\n{'Paso':<6} {'Carga (kN)':<12} {'Asentam. (mm)':<15} {'Estado':<12}")
    print("-" * 50)

    for step in range(1, num_steps + 1):
        # Limpiar patrón de carga anterior
        try:
            ops.remove('loadPattern', 1)
        except:
            pass

        try:
            ops.remove('timeSeries', 1)
        except:
            pass

        # Crear nuevo patrón de carga
        ops.timeSeries('Linear', 1)
        ops.pattern('Plain', 1, 1)

        # Carga acumulada
        current_load = step * load_increment
        load_per_node = -current_load / len(load_nodes)

        for node in load_nodes:
            ops.load(node, 0.0, 0.0, load_per_node)

        # Configurar integrador para este paso
        ops.integrator('LoadControl', 1.0)

        # Analizar
        ok = ops.analyze(1)

        if ok == 0:
            # Obtener asentamiento
            displacements = [ops.nodeDisp(node, 3) for node in load_nodes]
            settlement = -np.mean(displacements) * 1000  # mm (positivo hacia abajo)

            loads.append(current_load * 4)  # Multiplicar por 4 para carga total
            settlements.append(settlement)

            print(f"{step:<6} {current_load * 4:<12.2f} {settlement:<15.4f} {'CONVERGIÓ':<12}")
        else:
            print(f"{step:<6} {current_load * 4:<12.2f} {'N/A':<15} {'NO CONVERGIÓ':<12}")
            print("\n⚠ Análisis detenido")
            break

    # 9. Mostrar resultados
    print("\n" + "="*70)
    print("RESULTADOS DEL ENSAYO")
    print("="*70)

    if len(loads) > 0:
        print(f"\nCarga final: {loads[-1]:.2f} kN")
        print(f"Asentamiento final: {settlements[-1]:.4f} mm")
        print(f"Rigidez promedio: {loads[-1] / settlements[-1]:.2f} kN/mm")

        # Guardar resultados
        results_file = 'results/load_test_results.txt'
        with open(results_file, 'w') as f:
            f.write("Carga (kN)\tAsentamiento (mm)\n")
            for load, settle in zip(loads, settlements):
                f.write(f"{load:.2f}\t{settle:.6f}\n")
        print(f"\n📁 Resultados guardados en: {results_file}")

        # Graficar
        plt.figure(figsize=(10, 6))
        plt.plot(settlements, loads, 'b-o', linewidth=2, markersize=4)
        plt.xlabel('Asentamiento (mm)', fontsize=12)
        plt.ylabel('Carga (kN)', fontsize=12)
        plt.title('Curva Carga vs Asentamiento\nModelo 1/4 Simetría - Elementos Elásticos Lineales', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        fig_file = 'results/load_settlement_curve.png'
        plt.savefig(fig_file, dpi=300)
        print(f"📊 Gráfico guardado en: {fig_file}")

        plt.show()

    print("\n" + "="*70)

if __name__ == "__main__":
    run_incremental_load_test()
