import openseespy.opensees as ops
import numpy as np

# ================================================================================
# ANÁLISIS DE ZAPATA - EXTRACCIÓN COMPLETA DE ASENTAMIENTOS 3D
# ================================================================================
# Este script ejecuta el análisis y extrae asentamientos de TODOS los nodos
# incluyendo profundidad, no solo superficie
# ================================================================================

print("\n" + "="*80)
print("ANÁLISIS DE ZAPATA 1/4 - EXTRACCIÓN DE DATOS 3D COMPLETOS")
print("="*80 + "\n")

# -------------------------
# INICIALIZACIÓN
# -------------------------
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# -------------------------
# PARÁMETROS GEOMÉTRICOS
# -------------------------
Lx_quarter = 10.0
Ly_quarter = 10.0
Lz_soil = 20.0

nx = 10
ny = 10
nz = 15

dx = Lx_quarter / nx
dy = Ly_quarter / ny
dz = Lz_soil / nz

B_quarter = 1.5
L_quarter = 1.5
h_zapata = 0.6

# -------------------------
# PARÁMETROS DE MATERIALES
# -------------------------
E_soil = 30000.0
nu_soil = 0.3
rho_soil = 1800.0

rho_concrete = 2400.0

# -------------------------
# CREACIÓN DE NODOS
# -------------------------
print("Generando nodos...")

nodeCounter = 1
nodeCoord = {}
surface_nodes = []
zapata_nodes = []

for k in range(nz + 1):
    z = -k * dz
    for j in range(ny + 1):
        y = j * dy
        for i in range(nx + 1):
            x = i * dx
            ops.node(nodeCounter, x, y, z)
            nodeCoord[nodeCounter] = (x, y, z)

            if k == 0:
                surface_nodes.append(nodeCounter)
                if (0 <= x <= B_quarter and 0 <= y <= L_quarter):
                    zapata_nodes.append(nodeCounter)

            nodeCounter += 1

nodesPerLayer = (nx + 1) * (ny + 1)
total_nodes = nodeCounter - 1

print(f"Total de nodos creados: {total_nodes}")

# -------------------------
# CONDICIONES DE BORDE
# -------------------------
print("Aplicando condiciones de borde...")

# Base fija
baseNodeTags = list(range(nodesPerLayer * nz + 1, nodesPerLayer * (nz + 1) + 1))
for nodeTag in baseNodeTags:
    ops.fix(nodeTag, 1, 1, 1)

# Condiciones de simetría
for k in range(nz + 1):
    currentLayer = k * nodesPerLayer

    # Plano x=0 (simetría)
    for j in range(ny + 1):
        nodeTag = currentLayer + j * (nx + 1) + 1
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 1, 0, 0)

    # Plano y=0 (simetría)
    for i in range(nx + 1):
        nodeTag = currentLayer + i + 1
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 0, 1, 0)

# -------------------------
# MATERIAL
# -------------------------
print("Definiendo materiales...")
ops.nDMaterial('ElasticIsotropic', 1, E_soil, nu_soil, rho_soil)

# -------------------------
# ELEMENTOS
# -------------------------
print("Generando elementos...")
elementCounter = 1

for k in range(nz):
    for j in range(ny):
        for i in range(nx):
            node1 = 1 + i + j*(nx+1) + k*nodesPerLayer
            node2 = node1 + 1
            node3 = node2 + nx + 1
            node4 = node3 - 1
            node5 = node1 + nodesPerLayer
            node6 = node2 + nodesPerLayer
            node7 = node3 + nodesPerLayer
            node8 = node4 + nodesPerLayer

            ops.element('stdBrick', elementCounter, node1, node2, node3, node4,
                       node5, node6, node7, node8, 1)
            elementCounter += 1

print(f"Total de elementos: {elementCounter-1}")

# -------------------------
# CARGAS
# -------------------------
print("Aplicando cargas...")

ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

P_column_full = 1000.0
B_zapata_full = 3.0
L_zapata_full = 3.0
P_zapata_full = B_zapata_full * L_zapata_full * h_zapata * rho_concrete * 9.81 / 1000
P_total_full = P_column_full + P_zapata_full
P_total_quarter = P_total_full / 4.0

P_per_node = -P_total_quarter / len(zapata_nodes)

for node in zapata_nodes:
    ops.load(node, 0.0, 0.0, P_per_node)

print(f"Carga total 1/4: {P_total_quarter:.2f} kN")
print(f"Nodos cargados: {len(zapata_nodes)}")

# -------------------------
# ANÁLISIS
# -------------------------
print("\n" + "="*80)
print("EJECUTANDO ANÁLISIS")
print("="*80 + "\n")

ops.system('BandGeneral')
ops.numberer('RCM')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

print("Analizando...")
ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado exitosamente\n")
else:
    print("✗ Error en el análisis\n")
    exit(1)

# -------------------------
# EXTRACCIÓN DE RESULTADOS 3D COMPLETOS
# -------------------------
print("="*80)
print("EXTRAYENDO ASENTAMIENTOS DE TODOS LOS NODOS (3D COMPLETO)")
print("="*80 + "\n")

all_settlements_3d = []

for nodeTag in range(1, total_nodes + 1):
    try:
        disp = ops.nodeDisp(nodeTag, 3)  # Desplazamiento en Z
        settlement = abs(disp * 1000)  # mm
        coord = nodeCoord[nodeTag]
        x, y, z = coord
        all_settlements_3d.append((x, y, z, settlement))
    except:
        pass

print(f"Datos extraídos: {len(all_settlements_3d)} nodos con asentamientos")

# -------------------------
# GUARDAR DATOS COMPLETOS
# -------------------------
print("\nGuardando datos...")

# Guardar todos los nodos 3D
with open('settlements_3d_complete.csv', 'w') as f:
    f.write('X,Y,Z,Settlement_mm\n')
    for x, y, z, s in all_settlements_3d:
        f.write(f'{x:.6f},{y:.6f},{z:.6f},{s:.6f}\n')

print(f"✓ Guardado: settlements_3d_complete.csv ({len(all_settlements_3d)} puntos)")

# Estadísticas
settlements_values = [s for _, _, _, s in all_settlements_3d]
print(f"\nEstadísticas de asentamientos:")
print(f"  Máximo: {max(settlements_values):.4f} mm")
print(f"  Mínimo: {min(settlements_values):.4f} mm")
print(f"  Promedio: {np.mean(settlements_values):.4f} mm")

print("\n" + "="*80)
print("EXTRACCIÓN COMPLETADA")
print("="*80 + "\n")
