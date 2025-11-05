"""
Diagnóstico del modelo
"""

import openseespy.opensees as ops
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry
from materials import MaterialManager

def diagnose():
    print("\n" + "="*70)
    print("DIAGNÓSTICO DEL MODELO")
    print("="*70)

    # Generar malla
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    print(f"\nNodos totales: {len(mesh.nodes)}")
    print(f"Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"Elementos de zapata: {len(mesh.footing_elements)}")

    # Verificar nodos sin restricciones
    print("\n--- Verificando restricciones ---")

    # Obtener todos los nodos
    all_nodes = set(mesh.nodes.keys())

    # Obtener nodos restringidos
    restrained_nodes = set()

    # Nodos en base (z = -15m)
    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(z + SOIL_DEPTH) < 0.01:
            restrained_nodes.add(node_tag)

    # Nodos en planos de simetría
    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(x - 0.0) < 0.01 or abs(y - 0.0) < 0.01:
            restrained_nodes.add(node_tag)

    # Nodos laterales
    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(x - SOIL_WIDTH_X) < 0.01 or abs(y - SOIL_WIDTH_Y) < 0.01:
            restrained_nodes.add(node_tag)

    unrestrained = all_nodes - restrained_nodes
    print(f"Nodos restringidos: {len(restrained_nodes)}")
    print(f"Nodos sin restricción: {len(unrestrained)}")

    # Ver algunos nodos sin restricción
    if len(unrestrained) > 0:
        print("\nAlgunos nodos sin restricción:")
        for i, node in enumerate(list(unrestrained)[:5]):
            x, y, z = mesh.nodes[node]
            print(f"  Nodo {node}: ({x:.2f}, {y:.2f}, {z:.2f})")

    # Verificar conectividad de elementos
    print("\n--- Verificando elementos ---")

    nodes_in_elements = set()
    for elem_info in mesh.soil_elements.values():
        nodes_in_elements.update(elem_info['nodes'])

    for elem_info in mesh.footing_elements:
        nodes_in_elements.update(elem_info['nodes'])

    print(f"Nodos usados en elementos: {len(nodes_in_elements)}")

    nodes_without_elements = all_nodes - nodes_in_elements
    print(f"Nodos SIN elementos: {len(nodes_without_elements)}")

    if len(nodes_without_elements) > 0:
        print(f"\n⚠ ADVERTENCIA: Hay {len(nodes_without_elements)} nodos sin conectar a elementos!")
        print("Primeros 10 nodos sin elementos:")
        for i, node in enumerate(list(nodes_without_elements)[:10]):
            x, y, z = mesh.nodes[node]
            print(f"  Nodo {node}: ({x:.3f}, {y:.3f}, {z:.3f})")

    # Verificar si algún elemento tiene nodos que no existen
    print("\n--- Verificando integridad de elementos ---")
    missing_nodes_count = 0

    for elem_tag, elem_info in mesh.soil_elements.items():
        for node in elem_info['nodes']:
            if node not in all_nodes:
                missing_nodes_count += 1
                print(f"  ⚠ Elemento {elem_tag} referencia nodo {node} que no existe!")

    for i, elem_info in enumerate(mesh.footing_elements):
        for node in elem_info['nodes']:
            if node not in all_nodes:
                missing_nodes_count += 1
                print(f"  ⚠ Elemento zapata {i} referencia nodo {node} que no existe!")

    if missing_nodes_count == 0:
        print("  ✓ Todos los elementos tienen nodos válidos")
    else:
        print(f"  ✗ Encontrados {missing_nodes_count} referencias a nodos faltantes")

    print("\n" + "="*70)

if __name__ == "__main__":
    diagnose()
