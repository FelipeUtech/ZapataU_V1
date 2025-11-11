#!/usr/bin/env python3
"""
Corregir el archivo VTU para asegurar que los asentamientos estén correctamente mapeados
"""
import pyvista as pv
import pandas as pd
import numpy as np

# Leer la malla original
grid = pv.read('mallas/zapata_3D_cuarto.vtu')
points = grid.points
cells = grid.cells
material_ids = grid.cell_data.get('dominio', None)

print(f"Malla original: {grid.n_points} nodos, {grid.n_cells} elementos")

# Leer los datos de asentamiento del CSV
df = pd.read_csv('settlements_total.csv')
print(f"Datos CSV: {len(df)} registros")

# Crear mapeo de coordenadas a asentamientos
coord_to_settlement = {}
for _, row in df.iterrows():
    key = (round(row['X'], 6), round(row['Y'], 6), round(row['Z'], 6))
    coord_to_settlement[key] = {
        'gravedad': row['Settlement_gravedad_mm'],
        'carga': row['Settlement_carga_mm'],
        'total': row['Settlement_total_mm']
    }

# Fusionar nodos duplicados
tolerance = 1e-6
coord_to_nodes = {}

for i, point in enumerate(points):
    key = (round(point[0] / tolerance) * tolerance,
           round(point[1] / tolerance) * tolerance,
           round(point[2] / tolerance) * tolerance)

    if key not in coord_to_nodes:
        coord_to_nodes[key] = []
    coord_to_nodes[key].append(i)

# Crear nodos únicos y mapeo
node_mapping = {}
unique_points = []
unique_settlements_grav = []
unique_settlements_carga = []
unique_settlements_total = []
unique_disp_x = []
unique_disp_y = []
unique_disp_z = []

for key, node_indices in coord_to_nodes.items():
    master_idx = node_indices[0]
    master_point = points[master_idx]

    # Índice en la lista de nodos únicos
    new_idx = len(unique_points)

    # Mapear todos los índices originales a este nuevo índice
    for idx in node_indices:
        node_mapping[idx] = new_idx

    # Agregar coordenadas
    unique_points.append(master_point)

    # Buscar asentamiento para este nodo
    coord_key = (round(master_point[0], 6), round(master_point[1], 6), round(master_point[2], 6))

    if coord_key in coord_to_settlement:
        data = coord_to_settlement[coord_key]
        unique_settlements_grav.append(data['gravedad'])
        unique_settlements_carga.append(data['carga'])
        unique_settlements_total.append(data['total'])
        # Desplazamientos (asentamiento negativo en Z)
        unique_disp_x.append(0.0)
        unique_disp_y.append(0.0)
        unique_disp_z.append(-data['total'] / 1000.0)  # mm a m
    else:
        unique_settlements_grav.append(0.0)
        unique_settlements_carga.append(0.0)
        unique_settlements_total.append(0.0)
        unique_disp_x.append(0.0)
        unique_disp_y.append(0.0)
        unique_disp_z.append(0.0)

unique_points = np.array(unique_points)
print(f"Nodos únicos: {len(unique_points)}")
print(f"Nodos duplicados fusionados: {len(points) - len(unique_points)}")

# Reconstruir conectividad de elementos
new_cells = []
new_material_ids = []

element_id = 0
cell_idx = 0

while cell_idx < len(cells):
    n_points = cells[cell_idx]
    if n_points != 4:
        cell_idx += n_points + 1
        continue

    # Índices originales
    idx1 = int(cells[cell_idx + 1])
    idx2 = int(cells[cell_idx + 2])
    idx3 = int(cells[cell_idx + 3])
    idx4 = int(cells[cell_idx + 4])

    # Mapear a índices únicos
    new_idx1 = node_mapping[idx1]
    new_idx2 = node_mapping[idx2]
    new_idx3 = node_mapping[idx3]
    new_idx4 = node_mapping[idx4]

    # Agregar celda
    new_cells.extend([4, new_idx1, new_idx2, new_idx3, new_idx4])

    # Material
    mat_id = int(material_ids[element_id])
    new_material_ids.append(mat_id)

    element_id += 1
    cell_idx += n_points + 1

print(f"Elementos procesados: {len(new_material_ids)}")

# Crear nuevo grid
celltypes = [pv.CellType.TETRA] * len(new_material_ids)
result_grid = pv.UnstructuredGrid(new_cells, celltypes, unique_points)

# Agregar datos
result_grid.cell_data['dominio'] = np.array(new_material_ids)
result_grid.point_data['Settlement_gravedad_mm'] = np.array(unique_settlements_grav)
result_grid.point_data['Settlement_carga_mm'] = np.array(unique_settlements_carga)
result_grid.point_data['Settlement_total_mm'] = np.array(unique_settlements_total)
result_grid.point_data['Displacement_X_m'] = np.array(unique_disp_x)
result_grid.point_data['Displacement_Y_m'] = np.array(unique_disp_y)
result_grid.point_data['Displacement_Z_m'] = np.array(unique_disp_z)

# Magnitud de desplazamiento
disp_mag = np.sqrt(np.array(unique_disp_x)**2 +
                   np.array(unique_disp_y)**2 +
                   np.array(unique_disp_z)**2)
result_grid.point_data['Displacement_Magnitude_m'] = disp_mag

# Guardar
result_grid.save('resultados_2phases.vtu')
print(f"\n✓ Archivo VTU corregido guardado: resultados_2phases.vtu")

# Verificar
max_settlement = np.array(unique_settlements_total).max()
max_idx = np.argmax(unique_settlements_total)
max_coord = unique_points[max_idx]

print(f"\nVerificación:")
print(f"  Asentamiento máximo: {max_settlement:.2f} mm")
print(f"  Ubicación: ({max_coord[0]:.2f}, {max_coord[1]:.2f}, {max_coord[2]:.2f})")
print(f"  DEBE estar en (0.00, 0.00, 0.00) - origen donde está la zapata")

# Verificar esquina opuesta
corner_settlements = []
for i, point in enumerate(unique_points):
    if abs(point[0] - 4.5) < 0.1 and abs(point[1] - 4.5) < 0.1 and abs(point[2] - 0.0) < 0.1:
        corner_settlements.append(unique_settlements_total[i])

if corner_settlements:
    print(f"  Asentamiento en esquina (4.5, 4.5, 0): {np.mean(corner_settlements):.2f} mm")
    print(f"  DEBE ser menor (~130-135 mm)")
