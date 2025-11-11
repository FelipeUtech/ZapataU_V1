#!/usr/bin/env python3
"""
Test para verificar si nodeDisp retorna valores correctos después del análisis completo
"""
import openseespy.opensees as ops
import pyvista as pv
import numpy as np

print("="*80)
print("TEST: Verificar nodeDisp en análisis completo")
print("="*80)

# Cargar malla
mesh_file = "mallas/zapata_3D_cuarto.vtu"
grid = pv.read(mesh_file)
points = np.array(grid.points)
cells = np.array(grid.cells)
material_ids = grid.cell_data['dominio']

# Crear modelo
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

node_coords = {}
for i, point in enumerate(points):
    nid = i + 1
    x, y, z = point
    ops.node(nid, x, y, z)
    node_coords[nid] = (x, y, z)

print(f"✓ {len(node_coords)} nodos creados")

# Condiciones de borde
z_min = points[:, 2].min()
fixed_nodes = [nid for nid, coords in node_coords.items() if abs(coords[2] - z_min) < 0.01]
for nid in fixed_nodes:
    ops.fix(nid, 1, 1, 1)

x_min = points[:, 0].min()
x_symmetry = [nid for nid, coords in node_coords.items() if abs(coords[0] - x_min) < 0.01 and nid not in fixed_nodes]
for nid in x_symmetry:
    ops.fix(nid, 1, 0, 0)

y_min = points[:, 1].min()
y_symmetry = [nid for nid, coords in node_coords.items() if abs(coords[1] - y_min) < 0.01 and nid not in fixed_nodes]
for nid in y_symmetry:
    ops.fix(nid, 0, 1, 0)

print(f"✓ Condiciones de borde aplicadas")

# Materiales
ops.nDMaterial('ElasticIsotropic', 1, 5000.0, 0.3)
ops.nDMaterial('ElasticIsotropic', 2, 20000.0, 0.3)
ops.nDMaterial('ElasticIsotropic', 3, 50000.0, 0.3)
ops.nDMaterial('ElasticIsotropic', 4, 25000000.0, 0.2)

# Crear elementos
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

    ops.element('FourNodeTetrahedron', element_id, n1, n2, n3, n4, mat_id)
    element_id += 1
    cell_idx += n_points + 1

print(f"✓ {element_id-1} elementos creados")

# Aplicar carga
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Buscar un nodo en superficie cerca de la zapata
surface_nodes = [(nid, coords) for nid, coords in node_coords.items()
                 if abs(coords[2] - 0.0) < 0.1 and coords[0] < 1.0 and coords[1] < 1.5]

if surface_nodes:
    load_node = surface_nodes[0][0]
    ops.load(load_node, 0.0, 0.0, -250.0)
    print(f"✓ Carga 250 kN aplicada en nodo {load_node}")

# Análisis
ops.system('BandGeneral')
ops.numberer('Plain')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

print("\nEjecutando análisis...")
ok = ops.analyze(1)

if ok != 0:
    print(f"❌ Análisis falló: código {ok}")
    exit(1)

print("✓ Análisis completado\n")

# AHORA VERIFICAR LOS DESPLAZAMIENTOS
print("Verificando desplazamientos en nodos seleccionados:")
print(f"{'Nodo':<6} {'X':>8} {'Y':>8} {'Z':>8} {'DiспZ_raw':>20} {'Settlement_mm':>20}")
print("-"*90)

# Revisar nodos en diferentes zonas
test_nodes = []

# Nodos en superficie
for nid, coords in list(node_coords.items())[:30]:
    if abs(coords[2]) < 0.1:  # Superficie
        test_nodes.append(nid)

# Nodos cerca de la zapata
for nid, coords in node_coords.items():
    if abs(coords[2] - (-0.8)) < 0.2 and coords[0] < 0.6 and coords[1] < 0.9:
        test_nodes.append(nid)

# Revisar estos nodos
for nid in test_nodes[:20]:
    x, y, z = node_coords[nid]
    try:
        # MÉTODO 1: nodeDisp con índice
        disp_z_indexed = ops.nodeDisp(nid, 3)

        # MÉTODO 2: nodeDisp sin índice
        disp_full = ops.nodeDisp(nid)
        disp_z_full = disp_full[2]

        settlement_mm = abs(disp_z_full * 1000)

        print(f"{nid:<6} {x:>8.2f} {y:>8.2f} {z:>8.2f} {disp_z_full:>20.6e} {settlement_mm:>20.6e}")

        # Verificar si ambos métodos dan el mismo resultado
        if abs(disp_z_indexed - disp_z_full) > 1e-10:
            print(f"  ⚠️  DIFERENCIA: indexed={disp_z_indexed}, full={disp_z_full}")

    except Exception as e:
        print(f"{nid:<6} ERROR: {e}")

print("\n✓ Verificación completada")
print("="*80)
