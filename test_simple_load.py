"""
Script simple para probar carga en zapata
"""

import openseespy.opensees as ops
import numpy as np
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry
from materials import MaterialManager

def run_simple_test():
    print("\n" + "="*70)
    print("PRUEBA SIMPLE DE CARGA")
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

    print(f"  Elementos de suelo creados: {len(mesh.soil_elements)}")

    # Elementos de zapata
    elem_counter = max(mesh.soil_elements.keys()) + 1
    for elem_info in mesh.footing_elements:
        nodes = elem_info['nodes']
        ops.element('stdBrick', elem_counter, *nodes, 4)  # Material 4 = concreto
        elem_counter += 1

    print(f"  Elementos de zapata creados: {len(mesh.footing_elements)}")

    # 6. Aplicar pequeña carga vertical
    print("\n[6] Aplicando carga vertical...")

    # Definir patrón de carga
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    # Aplicar carga pequeña en nodos de contacto (top de zapata en z=-1.5m)
    z_top = -EMBEDMENT_DEPTH
    load_nodes = []

    for node_tag, (x, y, z) in mesh.nodes.items():
        # Nodos en la superficie superior de la zapata
        if abs(z - z_top) < 0.01:  # Tolerancia de 1cm
            if x >= FOOTING_START_X and x <= FOOTING_END_X:
                if y >= FOOTING_START_Y and y <= FOOTING_END_Y:
                    load_nodes.append(node_tag)

    # Carga total de 10 kN distribuida
    total_load = -10.0  # kN (negativo = hacia abajo)
    load_per_node = total_load / len(load_nodes)  # kN por nodo

    print(f"  Nodos de carga: {len(load_nodes)}")
    print(f"  Carga total: {total_load} kN")
    print(f"  Carga por nodo: {load_per_node:.4f} kN")

    for node in load_nodes:
        ops.load(node, 0.0, 0.0, load_per_node)

    # 7. Configurar análisis
    print("\n[7] Configurando análisis...")
    ops.constraints('Transformation')
    ops.numberer('RCM')
    ops.system('BandGeneral')
    ops.integrator('LoadControl', 1.0)
    ops.algorithm('Newton')
    ops.test('NormDispIncr', 1.0e-6, 50)
    ops.analysis('Static')

    # 8. Ejecutar análisis
    print("\n[8] Ejecutando análisis...")
    ok = ops.analyze(1)

    if ok == 0:
        print("\n✅ Análisis completado exitosamente")

        # Mostrar algunos desplazamientos
        print("\nDesplazamientos verticales en nodos de carga:")
        max_disp = 0
        for node_tag in load_nodes[:5]:  # Mostrar solo 5 primeros
            try:
                disp = ops.nodeDisp(node_tag, 3)
                print(f"  Nodo {node_tag}: {disp*1000:.4f} mm")
                if abs(disp) > abs(max_disp):
                    max_disp = disp
            except:
                pass

        print(f"\n  Máximo asentamiento: {abs(max_disp)*1000:.4f} mm")
    else:
        print(f"\n❌ Análisis falló con código: {ok}")

    print("\n" + "="*70)

if __name__ == "__main__":
    run_simple_test()
