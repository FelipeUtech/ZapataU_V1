"""
Debug de conexión zapata-suelo
"""

import openseespy.opensees as ops
import numpy as np
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def debug_connection():
    print("\n" + "="*70)
    print("DEBUG CONEXIÓN ZAPATA-SUELO")
    print("="*70)

    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()

    # Antes de crear la zapata, buscar nodos en la base de la zapata
    z_bottom = -EMBEDMENT_DEPTH - FOOTING_THICKNESS
    print(f"\n--- Buscando nodos de suelo en z={z_bottom:.3f} m ---")

    nodes_at_base = []
    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(z - z_bottom) < 0.01:  # Tolerancia 1cm
            if x >= FOOTING_START_X and x <= FOOTING_END_X:
                if y >= FOOTING_START_Y and y <= FOOTING_END_Y:
                    nodes_at_base.append((node_tag, x, y, z))

    print(f"Nodos encontrados en base de zapata: {len(nodes_at_base)}")

    if len(nodes_at_base) > 0:
        print("\nPrimeros 10 nodos:")
        for i, (tag, x, y, z) in enumerate(nodes_at_base[:10]):
            print(f"  Nodo {tag}: ({x:.3f}, {y:.3f}, {z:.3f})")
    else:
        print("\n⚠ NO se encontraron nodos en la base de la zapata")
        print(f"\nBuscando nodos más cercanos a z={z_bottom:.3f}:")

        # Buscar nodos cercanos
        all_z = [coord[2] for coord in mesh.nodes.values()]
        z_unique = sorted(set(all_z))

        print(f"\nNiveles Z disponibles cerca de {z_bottom:.3f}:")
        for z_val in z_unique:
            if abs(z_val - z_bottom) < 0.5:  # Dentro de 50cm
                print(f"  Z = {z_val:.3f} m (diff: {abs(z_val - z_bottom):.3f} m)")

    # Ahora crear la zapata
    print(f"\n--- Creando malla de zapata ---")

    # Coordenadas de la zapata
    x_min = FOOTING_START_X
    x_max = FOOTING_END_X
    y_min = FOOTING_START_Y
    y_max = FOOTING_END_Y

    x_footing = np.linspace(x_min, x_max, NX_FOOTING + 1)
    y_footing = np.linspace(y_min, y_max, NY_FOOTING + 1)
    z_footing = np.linspace(z_bottom, -EMBEDMENT_DEPTH, NZ_FOOTING + 1)

    print(f"Coordenadas Z de zapata:")
    for i, z in enumerate(z_footing):
        print(f"  Nivel {i}: z = {z:.4f} m")

    print(f"\nProbando búsqueda de nodos en base (k=0, z={z_footing[0]:.4f}):")
    found_count = 0
    not_found_count = 0

    for j, y in enumerate(y_footing):
        for i, x in enumerate(x_footing):
            z = z_footing[0]  # Base
            existing_node = mesh._find_nearest_node(x, y, z, tolerance=0.1)
            if existing_node:
                found_count += 1
                if found_count <= 5:
                    print(f"  ✓ Encontrado en ({x:.3f}, {y:.3f}, {z:.4f}): nodo {existing_node}")
            else:
                not_found_count += 1
                if not_found_count <= 5:
                    print(f"  ✗ NO encontrado en ({x:.3f}, {y:.3f}, {z:.4f})")

    print(f"\nResultado:")
    print(f"  Nodos encontrados: {found_count}")
    print(f"  Nodos NO encontrados: {not_found_count}")
    print(f"  Total esperado: {len(x_footing) * len(y_footing)}")

    print("\n" + "="*70)

if __name__ == "__main__":
    debug_connection()
