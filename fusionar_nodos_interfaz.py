#!/usr/bin/env python3
"""
Post-procesador para fusionar nodos duplicados en la interfaz zapata-suelo.
Lee la malla generada por generate_mesh_quarter.py y fusiona nodos que están
en la misma posición espacial.
"""

import numpy as np
import pyvista as pv
from scipy.spatial import cKDTree
import sys

def fusionar_nodos_duplicados(mesh_file, output_file, tolerance=1e-6):
    """
    Fusiona nodos duplicados en una malla y guarda la malla corregida.

    Args:
        mesh_file: Archivo de entrada (.vtu)
        output_file: Archivo de salida (.vtu)
        tolerance: Distancia máxima para considerar nodos duplicados
    """

    print("=" * 70)
    print("FUSIÓN DE NODOS DUPLICADOS EN INTERFAZ ZAPATA-SUELO")
    print("=" * 70 + "\n")

    # Cargar malla original
    print(f"📂 Cargando malla: {mesh_file}")
    mesh = pv.read(mesh_file)

    print(f"   Nodos originales: {mesh.n_points:,}")
    print(f"   Elementos originales: {mesh.n_cells:,}\n")

    # Extraer datos
    points = mesh.points.copy()
    materials = mesh.cell_data['dominio'].copy()

    # Construir árbol KD para búsqueda rápida de vecinos cercanos
    print("🔍 Buscando nodos duplicados...")
    tree = cKDTree(points)

    # Encontrar todos los pares de nodos dentro del tolerance
    pairs = tree.query_pairs(r=tolerance)

    print(f"   Encontrados {len(pairs)} pares de nodos duplicados\n")

    if len(pairs) == 0:
        print("✅ No hay nodos duplicados, la malla ya está bien conectada.")
        return False

    # Crear mapeo: nodo_antiguo -> nodo_nuevo
    node_map = np.arange(len(points))  # Inicialmente cada nodo mapea a sí mismo

    # Fusionar nodos duplicados (mantener el de índice menor)
    for i, j in pairs:
        # Usar el nodo con índice menor como representante
        min_idx = min(i, j)
        max_idx = max(i, j)

        # Actualizar el mapeo
        node_map[max_idx] = min_idx

        # Si max_idx ya estaba mapeado a otro nodo, actualizar en cadena
        for k in range(len(node_map)):
            if node_map[k] == max_idx:
                node_map[k] = min_idx

    # Identificar nodos únicos (que no fueron eliminados)
    unique_nodes = np.unique(node_map)
    n_unique = len(unique_nodes)

    print(f"📊 Resultado de fusión:")
    print(f"   Nodos únicos después de fusión: {n_unique:,}")
    print(f"   Nodos eliminados (duplicados): {len(points) - n_unique:,}\n")

    # Crear mapeo inverso: nodo_antiguo -> índice_nuevo
    new_index = np.zeros(len(points), dtype=int)
    for new_idx, old_idx in enumerate(unique_nodes):
        indices_to_remap = np.where(node_map == old_idx)[0]
        new_index[indices_to_remap] = new_idx

    # Crear nueva lista de puntos (solo nodos únicos)
    new_points = points[unique_nodes]

    # Reconstruir elementos con nuevos índices de nodos
    print("🔨 Reconstruyendo elementos...")
    new_cells = []
    new_materials = []

    for i in range(mesh.n_cells):
        cell = mesh.get_cell(i)

        # Mapear nodos antiguos a nuevos
        old_node_ids = cell.point_ids
        new_node_ids = [new_index[old_id] for old_id in old_node_ids]

        # Verificar que no se colapsó a menos de 4 nodos únicos (tetraedro)
        if len(set(new_node_ids)) == 4:
            new_cells.append(new_node_ids)
            new_materials.append(materials[i])
        else:
            print(f"   ⚠️  Elemento {i} colapsado (menos de 4 nodos únicos), omitido")

    n_new_cells = len(new_cells)

    print(f"   Elementos reconstruidos: {n_new_cells:,}")
    print(f"   Elementos eliminados (degenerados): {mesh.n_cells - n_new_cells:,}\n")

    # Crear nueva malla PyVista
    print("💾 Creando nueva malla...")

    # Convertir a formato PyVista
    cells_array = []
    for cell_nodes in new_cells:
        cells_array.extend([4] + cell_nodes)  # 4 nodos por tetraedro

    cells_array = np.array(cells_array)
    celltypes = np.full(n_new_cells, pv.CellType.TETRA, dtype=np.uint8)

    new_mesh = pv.UnstructuredGrid(cells_array, celltypes, new_points)
    new_mesh.cell_data['dominio'] = np.array(new_materials, dtype=np.int32)

    # Guardar nueva malla
    print(f"💾 Guardando malla fusionada: {output_file}")
    new_mesh.save(output_file)

    # Verificar conectividad
    print("\n🔍 Verificando conectividad zapata-suelo...")
    from collections import defaultdict

    node_materials_map = defaultdict(set)
    for i in range(new_mesh.n_cells):
        cell = new_mesh.get_cell(i)
        mat_id = new_materials[i]
        for node_id in cell.point_ids:
            node_materials_map[node_id].add(mat_id)

    # Contar nodos compartidos entre zapata (4) y suelo (1, 2, 3)
    shared_nodes = 0
    for node_id, mats in node_materials_map.items():
        has_footing = 4 in mats
        has_soil = len(mats & {1, 2, 3}) > 0
        if has_footing and has_soil:
            shared_nodes += 1

    print(f"   ✅ Nodos compartidos zapata-suelo: {shared_nodes:,}\n")

    print("=" * 70)
    print("✅ FUSIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print(f"\nMalla corregida guardada en: {output_file}")
    print(f"Ahora puedes convertir esta malla a OpenSees.\n")

    return True


if __name__ == "__main__":
    input_file = "mallas/zapata_3D_cuarto.vtu"
    output_file = "mallas/zapata_3D_cuarto_fused.vtu"

    success = fusionar_nodos_duplicados(input_file, output_file, tolerance=1e-6)

    if success:
        print("🚀 Siguiente paso:")
        print("   python3 gmsh_to_opensees.py mallas/zapata_3D_cuarto_fused.vtu -o opensees_input\n")

    sys.exit(0 if success else 1)
