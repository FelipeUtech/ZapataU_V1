#!/usr/bin/env python3
"""
Script de debug para investigar problema de desplazamientos
"""
import openseespy.opensees as ops
import pyvista as pv
import numpy as np

print("="*80)
print("DEBUG: Análisis simple para verificar desplazamientos")
print("="*80)

# Cargar malla
print("\n1. Cargando malla...")
mesh_file = "mallas/zapata_3D_cuarto.vtu"
grid = pv.read(mesh_file)

points = np.array(grid.points)
cells = np.array(grid.cells)
material_ids = grid.cell_data['dominio']

print(f"✓ Nodos: {len(points)}")
print(f"✓ Elementos: {len(material_ids)}")

# Crear modelo simple
print("\n2. Creando modelo OpenSeesPy...")
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# Crear nodos
node_coords = {}
for i, point in enumerate(points):
    nid = i + 1
    x, y, z = point
    ops.node(nid, x, y, z)
    node_coords[nid] = (x, y, z)

print(f"✓ {len(node_coords)} nodos creados")

# Aplicar condiciones de borde simples
z_min = points[:, 2].min()
fixed_nodes = [nid for nid, coords in node_coords.items() if abs(coords[2] - z_min) < 0.01]
for nid in fixed_nodes:
    ops.fix(nid, 1, 1, 1)
print(f"✓ {len(fixed_nodes)} nodos fijados en base")

# Materiales simples
print("\n3. Definiendo materiales...")
ops.nDMaterial('ElasticIsotropic', 1, 5000.0, 0.3)   # Estrato 1
ops.nDMaterial('ElasticIsotropic', 2, 20000.0, 0.3)  # Estrato 2
ops.nDMaterial('ElasticIsotropic', 3, 50000.0, 0.3)  # Estrato 3
ops.nDMaterial('ElasticIsotropic', 4, 25000000.0, 0.2)  # Zapata

# Crear elementos
print("\n4. Creando elementos...")
element_id = 1
cell_idx = 0

while cell_idx < len(cells):
    n_points = cells[cell_idx]
    if n_points != 4:
        cell_idx += n_points + 1
        continue

    n1 = int(cells[cell_idx + 1]) + 1
    n2 = int(cells[cell_idx + 2]) + 1
    n3 = int(cells[cell_idx + 3]) + 1
    n4 = int(cells[cell_idx + 4]) + 1
    mat_id = int(material_ids[element_id - 1])

    try:
        ops.element('FourNodeTetrahedron', element_id, n1, n2, n3, n4, mat_id)
    except Exception as e:
        print(f"❌ Error creando elemento {element_id}: {e}")
        break

    element_id += 1
    cell_idx += n_points + 1

print(f"✓ {element_id-1} elementos creados")

# Aplicar carga simple
print("\n5. Aplicando carga...")
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Encontrar nodos en superficie
surface_nodes = [nid for nid, coords in node_coords.items() if abs(coords[2] - 0.0) < 0.1]
print(f"✓ {len(surface_nodes)} nodos en superficie")

# Aplicar carga pequeña en nodo central
if surface_nodes:
    central_node = surface_nodes[0]
    ops.load(central_node, 0.0, 0.0, -100.0)  # 100 kN hacia abajo
    print(f"✓ Carga aplicada en nodo {central_node}")

# Análisis
print("\n6. Ejecutando análisis...")
ops.system('BandGeneral')
ops.numberer('Plain')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado")
else:
    print(f"❌ Análisis falló con código {ok}")

# Leer desplazamientos
print("\n7. Leyendo desplazamientos...")
print(f"\nPrimeros 10 nodos:")
print(f"{'Nodo':<8} {'X':>10} {'Y':>10} {'Z':>10} {'DispZ':>15} {'SettleMM':>15}")
print("-"*80)

for i, nid in enumerate(sorted(node_coords.keys())[:10]):
    x, y, z = node_coords[nid]
    try:
        disp = ops.nodeDisp(nid)
        disp_z = disp[2]
        settlement_mm = abs(disp_z * 1000)
        print(f"{nid:<8} {x:>10.3f} {y:>10.3f} {z:>10.3f} {disp_z:>15.6e} {settlement_mm:>15.6e}")
    except Exception as e:
        print(f"{nid:<8} ERROR: {e}")

print("\n✓ Debug completado")
print("="*80)
