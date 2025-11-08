#!/usr/bin/env python3
"""
Script para verificar la conexión entre zapata y suelo en la malla OpenSees.
Analiza si hay nodos compartidos entre elementos de zapata y elementos de suelo.
"""

import numpy as np
import pyvista as pv
from collections import defaultdict

def load_mesh_and_analyze(mesh_file):
    """Carga malla y analiza conectividad zapata-suelo."""

    print("=" * 70)
    print("VERIFICACIÓN DE CONEXIÓN ZAPATA-SUELO")
    print("=" * 70 + "\n")

    # Cargar malla
    print(f"📂 Cargando malla: {mesh_file}")
    mesh = pv.read(mesh_file)

    print(f"✅ Malla cargada:")
    print(f"   Nodos: {mesh.n_points:,}")
    print(f"   Elementos: {mesh.n_cells:,}\n")

    # Obtener materiales
    if 'dominio' in mesh.cell_data:
        materials = mesh.cell_data['dominio']
    else:
        print("❌ Error: No se encontró campo 'dominio'")
        return

    # Crear diccionario: nodo -> lista de materiales que lo usan
    node_materials = defaultdict(set)

    # Mapeo material -> elementos
    footing_elements = []
    soil_elements = []

    print("🔍 Analizando conectividad...")

    for i in range(mesh.n_cells):
        cell = mesh.get_cell(i)
        mat_id = materials[i]

        # Material 4 = zapata, 1-3 = suelo
        if mat_id == 4:
            footing_elements.append(i)
        else:
            soil_elements.append(i)

        # Registrar qué materiales usa cada nodo
        for node_id in cell.point_ids:
            node_materials[node_id].add(mat_id)

    print(f"   Elementos de zapata (mat=4): {len(footing_elements):,}")
    print(f"   Elementos de suelo (mat=1-3): {len(soil_elements):,}\n")

    # Buscar nodos compartidos entre zapata y suelo
    shared_nodes = []
    interface_by_material = defaultdict(list)

    for node_id, mats in node_materials.items():
        # Si un nodo pertenece a zapata (4) Y a suelo (1, 2, o 3)
        has_footing = 4 in mats
        soil_mats = mats & {1, 2, 3}

        if has_footing and len(soil_mats) > 0:
            shared_nodes.append(node_id)
            for soil_mat in soil_mats:
                interface_by_material[soil_mat].append(node_id)

    # Resultados
    print("=" * 70)
    print("RESULTADOS DE CONECTIVIDAD")
    print("=" * 70 + "\n")

    if len(shared_nodes) == 0:
        print("❌ ERROR: No hay nodos compartidos entre zapata y suelo!")
        print("   La zapata y el suelo NO están conectados.\n")
        return False
    else:
        print(f"✅ CONEXIÓN VERIFICADA:")
        print(f"   {len(shared_nodes):,} nodos compartidos entre zapata y suelo\n")

        print("📊 Distribución de nodos de interfaz:")
        for soil_mat in sorted(interface_by_material.keys()):
            nodes_count = len(interface_by_material[soil_mat])
            print(f"   Zapata ↔ Suelo_{soil_mat}: {nodes_count:,} nodos")

        print("\n🔗 Análisis de interfaz:")

        # Calcular coordenadas Z de nodos compartidos
        shared_coords = mesh.points[shared_nodes]
        z_coords = shared_coords[:, 2]

        print(f"   Z mínimo: {z_coords.min():.3f} m")
        print(f"   Z máximo: {z_coords.max():.3f} m")
        print(f"   Z promedio: {z_coords.mean():.3f} m")

        # Análisis por rangos de profundidad
        print(f"\n   Distribución por profundidad:")
        z_ranges = [
            (-2.0, -1.8, "Base de zapata"),
            (-1.8, -1.5, "Zapata intermedia"),
            (-1.5, -1.0, "Cerca superficie"),
            (-3.0, 0.0, "Total")
        ]

        for z_min, z_max, desc in z_ranges:
            count = np.sum((z_coords >= z_min) & (z_coords < z_max))
            if count > 0:
                print(f"     {desc} [{z_min:.1f}, {z_max:.1f}): {count} nodos")

        print("\n" + "=" * 70)
        print("✅ VERIFICACIÓN EXITOSA")
        print("=" * 70)
        print("La zapata está correctamente conectada al suelo.")
        print("Los nodos de interfaz permiten transferencia de fuerzas.\n")

        return True

if __name__ == "__main__":
    import sys
    import os

    # Usar malla fusionada si existe, sino la original
    mesh_file_fused = "mallas/zapata_3D_cuarto_fused.vtu"
    mesh_file_original = "mallas/zapata_3D_cuarto.vtu"

    if os.path.exists(mesh_file_fused):
        mesh_file = mesh_file_fused
        print(f"ℹ️  Usando malla fusionada: {mesh_file}\n")
    else:
        mesh_file = mesh_file_original
        print(f"ℹ️  Usando malla original: {mesh_file}\n")

    success = load_mesh_and_analyze(mesh_file)

    if not success:
        sys.exit(1)
