#!/usr/bin/env python3
"""
Visualiza la malla para identificar el problema de conexión zapata-suelo.
"""

import pyvista as pv
import numpy as np

# Cargar malla
mesh = pv.read("mallas/zapata_3D_cuarto.vtu")
print(f"Malla cargada: {mesh.n_points} nodos, {mesh.n_cells} elementos")

# Obtener materiales
materials = mesh.cell_data['dominio']

# Separar por dominio
zapata_mask = materials == 4
suelo_mask = materials != 4

# Extraer submallas
zapata = mesh.extract_cells(np.where(zapata_mask)[0])
suelo = mesh.extract_cells(np.where(suelo_mask)[0])

print(f"\nZapata: {zapata.n_cells} elementos, {zapata.n_points} nodos")
print(f"Suelo: {suelo.n_cells} elementos, {suelo.n_points} nodos")

# Buscar nodos en la interfaz esperada (z ≈ -1.9 m, base de zapata)
all_points = mesh.points
z_base_zapata = -1.9

# Nodos de zapata cerca de la base
zapata_points_ids = set()
for i in np.where(zapata_mask)[0]:
    cell = mesh.get_cell(i)
    for node_id in cell.point_ids:
        zapata_points_ids.add(node_id)

# Nodos de suelo cerca del tope
suelo_points_ids = set()
for i in np.where(suelo_mask)[0]:
    cell = mesh.get_cell(i)
    for node_id in cell.point_ids:
        suelo_points_ids.add(node_id)

print(f"\nNodos únicos en zapata: {len(zapata_points_ids)}")
print(f"Nodos únicos en suelo: {len(suelo_points_ids)}")
print(f"Nodos compartidos: {len(zapata_points_ids & suelo_points_ids)}")

# Analizar nodos en la interfaz esperada
zapata_base_nodes = []
for node_id in zapata_points_ids:
    z = all_points[node_id, 2]
    if abs(z - z_base_zapata) < 0.1:  # Dentro de 10 cm de la base
        zapata_base_nodes.append(node_id)

suelo_top_nodes = []
for node_id in suelo_points_ids:
    z = all_points[node_id, 2]
    if z > -2.0 and z < -1.4:  # En zona de interfaz
        suelo_top_nodes.append(node_id)

print(f"\nNodos de zapata cerca de la base (z≈{z_base_zapata}): {len(zapata_base_nodes)}")
print(f"Nodos de suelo en zona de interfaz: {len(suelo_top_nodes)}")

# Verificar si hay duplicados (nodos muy cercanos pero diferentes)
print("\n🔍 Buscando nodos duplicados...")
threshold = 1e-6

zapata_base_coords = all_points[zapata_base_nodes]
suelo_top_coords = all_points[suelo_top_nodes]

duplicates_found = 0
for i, zb_coord in enumerate(zapata_base_coords):
    for j, st_coord in enumerate(suelo_top_coords):
        dist = np.linalg.norm(zb_coord - st_coord)
        if dist < threshold:
            duplicates_found += 1
            if duplicates_found <= 5:  # Mostrar solo los primeros 5
                print(f"   Nodo zapata {zapata_base_nodes[i]} ≈ nodo suelo {suelo_top_nodes[j]}, dist={dist:.2e}m")

if duplicates_found > 5:
    print(f"   ... y {duplicates_found - 5} pares más")

print(f"\nTotal de pares de nodos duplicados encontrados: {duplicates_found}")

if duplicates_found > 0:
    print("\n❌ PROBLEMA IDENTIFICADO:")
    print("   La zapata y el suelo tienen nodos separados en la interfaz.")
    print("   Gmsh NO fusionó los nodos automáticamente.")
    print("\n💡 SOLUCIÓN:")
    print("   Necesitamos usar gmsh.model.occ.fragment() en lugar de cut()")
    print("   para que los volúmenes compartan nodos en la interfaz.")
