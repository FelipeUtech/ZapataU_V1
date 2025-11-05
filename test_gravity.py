"""
Script para probar la fase de gravedad
"""

import openseespy.opensees as ops
import numpy as np
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry
from materials import MaterialManager

def run_gravity_analysis():
    print("\n" + "="*70)
    print("FASE DE GRAVEDAD - PRUEBA")
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

    # 6. Aplicar gravedad
    print("\n[6] Aplicando gravedad...")

    # Definir patrón de carga de gravedad
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    # Aplicar gravedad a todos los nodos
    g = -9.81  # m/s^2

    footing_density = FOOTING_MATERIAL['rho']  # 2400 kg/m^3

    # Aplicar peso propio a nodos de suelo
    for node_tag, (x, y, z) in mesh.nodes.items():
        # Determinar estrato
        depth = -z
        layer_idx = 0
        for i, layer in enumerate(SOIL_LAYERS):
            if depth >= layer['depth_top'] and depth < layer['depth_bottom']:
                layer_idx = i
                break

        # Usar densidad del estrato
        rho = SOIL_LAYERS[layer_idx]['rho']

        # Estimar volumen nodal (aproximado)
        vol_nodal = 0.1  # m^3 (estimado)
        mass = rho * vol_nodal
        weight = mass * g

        ops.load(node_tag, 0.0, 0.0, weight)

    print(f"  Gravedad aplicada a {len(mesh.nodes)} nodos de suelo")

    # Aplicar peso de zapata
    for elem_info in mesh.footing_elements:
        nodes = elem_info['nodes']
        # Volumen del elemento (aproximado)
        vol_elem = 0.02  # m^3
        mass_elem = footing_density * vol_elem
        weight_elem = mass_elem * g / 8  # Dividido entre 8 nodos

        for node in nodes:
            if node in mesh.nodes:  # Solo nodos de suelo
                continue
            # Nodos de zapata
            try:
                ops.load(node, 0.0, 0.0, weight_elem)
            except:
                pass  # Nodo ya tiene carga

    print(f"  Gravedad aplicada a zapata")

    # 7. Configurar análisis
    print("\n[7] Configurando análisis...")
    ops.constraints('Penalty', 1.0e15, 1.0e15)
    ops.numberer('RCM')
    ops.system('BandGeneral')
    ops.integrator('LoadControl', 0.1)  # 10 pasos
    ops.algorithm('Newton')
    ops.test('NormDispIncr', 1.0e-4, 100)
    ops.analysis('Static')

    # 8. Ejecutar análisis de gravedad
    print("\n[8] Ejecutando análisis de gravedad...")
    print(f"{'Paso':<6} {'Estado':<15}")
    print("-" * 25)

    for i in range(10):
        ok = ops.analyze(1)
        if ok == 0:
            print(f"{i+1:<6} {'CONVERGIÓ':<15}")
        else:
            print(f"{i+1:<6} {'NO CONVERGIÓ':<15}")
            print(f"\n⚠ Análisis detenido en paso {i+1}")
            break

    if ok == 0:
        print("\n✅ Fase de gravedad completada exitosamente")

        # Mostrar algunos desplazamientos
        print("\nDesplazamientos verticales máximos:")
        max_disp = 0
        for node_tag in mesh.nodes.keys():
            try:
                disp = ops.nodeDisp(node_tag, 3)
                if abs(disp) > abs(max_disp):
                    max_disp = disp
            except:
                pass

        print(f"  Máximo asentamiento: {abs(max_disp)*1000:.2f} mm")
    else:
        print("\n❌ Fase de gravedad falló")

    print("\n" + "="*70)

if __name__ == "__main__":
    run_gravity_analysis()
