"""
Verificar conexión entre zapata y suelo
"""

import openseespy.opensees as ops
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def verify_connection():
    print("\n" + "="*70)
    print("VERIFICACIÓN DE CONEXIÓN ZAPATA-SUELO")
    print("="*70)

    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()

    # Encontrar nodos compartidos entre zapata y suelo
    print("\n--- Buscando nodos compartidos ---")

    # Nodos de elementos de suelo
    soil_nodes = set()
    for elem_info in mesh.soil_elements.values():
        soil_nodes.update(elem_info['nodes'])

    # Nodos de elementos de zapata
    footing_nodes = set()
    for elem_info in mesh.footing_elements:
        footing_nodes.update(elem_info['nodes'])

    # Nodos compartidos (contacto)
    shared_nodes = soil_nodes.intersection(footing_nodes)

    print(f"Nodos de suelo: {len(soil_nodes)}")
    print(f"Nodos de zapata: {len(footing_nodes)}")
    print(f"Nodos compartidos (CONTACTO): {len(shared_nodes)}")

    if len(shared_nodes) > 0:
        print(f"\n✅ Hay {len(shared_nodes)} nodos de contacto entre zapata y suelo")

        # Mostrar posición de algunos nodos de contacto
        print("\nPrimeros 10 nodos de contacto:")
        for i, node in enumerate(list(shared_nodes)[:10]):
            x, y, z = mesh.nodes[node]
            print(f"  Nodo {node}: ({x:.3f}, {y:.3f}, {z:.3f}) m")

        # Verificar que están en la base de la zapata
        z_bottom = -EMBEDMENT_DEPTH - FOOTING_THICKNESS
        contact_z = [mesh.nodes[n][2] for n in shared_nodes]
        z_min_contact = min(contact_z)
        z_max_contact = max(contact_z)

        print(f"\nRango Z de nodos de contacto:")
        print(f"  Z mínimo: {z_min_contact:.3f} m")
        print(f"  Z máximo: {z_max_contact:.3f} m")
        print(f"  Z esperado (base zapata): {z_bottom:.3f} m")

        if abs(z_min_contact - z_bottom) < 0.1 and abs(z_max_contact - z_bottom) < 0.1:
            print(f"\n✅ Los nodos de contacto están correctamente en la base de la zapata")
        else:
            print(f"\n⚠ ADVERTENCIA: Los nodos de contacto NO están en la base de la zapata")

    else:
        print(f"\n❌ ERROR: NO hay nodos compartidos entre zapata y suelo")
        print("La zapata y el suelo están desconectados!")

    print("\n" + "="*70)

if __name__ == "__main__":
    verify_connection()
