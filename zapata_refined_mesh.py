#!/usr/bin/env python3
"""
Modelo 1/4 de Zapata con Malla Refinada
- Dominio: 3B = 9m × 9m (completo) = 4.5m × 4.5m (modelo 1/4)
- Malla refinada en zapata: 0.25m × 0.25m
- Malla exterior: 0.5m × 0.5m
- Zapata 10× más rígida que la actual
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd

# ================================================================================
# INICIALIZACIÓN
# ================================================================================
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# ================================================================================
# PARÁMETROS GEOMÉTRICOS
# ================================================================================
B = 3.0  # Ancho zapata completa
dominio_quarter = 4.5  # Modelo 1/4: 4.5m × 4.5m (dominio completo 9m × 9m = 3B)
zapata_quarter = 1.5   # Zapata en modelo 1/4
Lz_soil = 20.0
h_zapata = 0.6

print("\n" + "="*80)
print("MODELO 1/4 CON MALLA REFINADA - DOMINIO 3B")
print("="*80)
print(f"\n📐 GEOMETRÍA:")
print(f"  Dominio completo: {dominio_quarter*2}m × {dominio_quarter*2}m (3B)")
print(f"  Dominio modelo 1/4: {dominio_quarter}m × {dominio_quarter}m")
print(f"  Zapata (1/4): {zapata_quarter}m × {zapata_quarter}m")
print(f"  Profundidad: {Lz_soil}m")

# ================================================================================
# MALLA NO UNIFORME
# ================================================================================
print(f"\n🔬 GENERANDO MALLA NO UNIFORME:")

# Coordenadas X e Y (idénticas por simetría)
# Zona zapata: 0 a 1.5m con dx=0.25m
x_zapata = np.arange(0, 1.5 + 0.01, 0.25)
# Zona exterior: 1.5 a 4.5m con dx=0.5m
x_exterior = np.arange(2.0, 4.5 + 0.01, 0.5)
# Combinar
x_coords = np.concatenate([x_zapata, x_exterior])
y_coords = x_coords.copy()

print(f"  Coordenadas X/Y: {len(x_coords)} posiciones")
print(f"  X = {x_coords}")

# Coordenadas Z: uniforme
z_coords = np.arange(0, -Lz_soil - 0.01, -1.0)
print(f"  Coordenadas Z: {len(z_coords)} niveles (dz=1.0m)")

# ================================================================================
# CREACIÓN DE NODOS
# ================================================================================
print(f"\n🔨 CREANDO NODOS...")

nodeCounter = 1
nodeCoord = {}
surface_nodes = []
zapata_nodes = []

nx = len(x_coords) - 1
ny = len(y_coords) - 1
nz = len(z_coords) - 1

for k, z in enumerate(z_coords):
    for j, y in enumerate(y_coords):
        for i, x in enumerate(x_coords):
            ops.node(nodeCounter, x, y, z)
            nodeCoord[nodeCounter] = (x, y, z)

            # Superficie
            if k == 0:
                surface_nodes.append(nodeCounter)
                # Nodos bajo zapata
                if x <= zapata_quarter and y <= zapata_quarter:
                    zapata_nodes.append(nodeCounter)

            nodeCounter += 1

total_nodes = nodeCounter - 1
nodesPerLayer = len(x_coords) * len(y_coords)

print(f"  Total nodos: {total_nodes}")
print(f"  Nodos por capa: {nodesPerLayer}")
print(f"  Nodos bajo zapata: {len(zapata_nodes)}")

# ================================================================================
# CONDICIONES DE BORDE
# ================================================================================
print(f"\n🔒 APLICANDO CONDICIONES DE BORDE...")

# Base fija
baseNodeTags = list(range(nodesPerLayer * nz + 1, total_nodes + 1))
for nodeTag in baseNodeTags:
    ops.fix(nodeTag, 1, 1, 1)

# Planos de simetría
for k in range(nz + 1):
    currentLayer = k * nodesPerLayer

    # Plano x=0 (i=0)
    for j in range(len(y_coords)):
        nodeTag = currentLayer + j * len(x_coords) + 1
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 1, 0, 0)

    # Plano y=0 (j=0)
    for i in range(len(x_coords)):
        nodeTag = currentLayer + i + 1
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 0, 1, 0)

# Bordes laterales externos
for k in range(nz + 1):
    currentLayer = k * nodesPerLayer

    # Borde x = max
    for j in range(len(y_coords)):
        nodeTag = currentLayer + j * len(x_coords) + len(x_coords)
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 1, 0, 0)

    # Borde y = max
    for i in range(len(x_coords)):
        nodeTag = currentLayer + (len(y_coords)-1) * len(x_coords) + i + 1
        if nodeTag not in baseNodeTags:
            ops.fix(nodeTag, 0, 1, 0)

print(f"  ✓ Condiciones de borde aplicadas")

# ================================================================================
# MATERIALES
# ================================================================================
print(f"\n🏗️  DEFINIENDO MATERIALES...")

E_soil = 20000.0      # kPa = 20 MPa
nu_soil = 0.3
rho_soil = 1800.0

# Zapata 10× más rígida que la actual (25 GPa → 250 GPa)
E_concrete = 250e6    # kPa = 250 GPa (10× más rígida)
nu_concrete = 0.2
rho_concrete = 2400.0

ops.nDMaterial('ElasticIsotropic', 1, E_soil, nu_soil, rho_soil)
ops.nDMaterial('ElasticIsotropic', 2, E_concrete, nu_concrete, rho_concrete)

print(f"  Suelo: E = {E_soil/1000:.1f} MPa")
print(f"  Zapata: E = {E_concrete/1e6:.1f} GPa (10× más rígida que antes)")
print(f"  Relación E_zapata/E_suelo = {E_concrete/E_soil:.0f}×")

# ================================================================================
# ELEMENTOS
# ================================================================================
print(f"\n🧱 GENERANDO ELEMENTOS...")

elementCounter = 1

# Identificar qué elementos son zapata (z >= -h_zapata y x,y <= zapata_quarter)
for k in range(nz):
    z_elem = z_coords[k]
    for j in range(ny):
        y_elem = y_coords[j]
        for i in range(nx):
            x_elem = x_coords[i]

            # Índices de nodos (esquema estándar de brick)
            node1 = 1 + i + j*len(x_coords) + k*nodesPerLayer
            node2 = node1 + 1
            node3 = node2 + len(x_coords)
            node4 = node3 - 1
            node5 = node1 + nodesPerLayer
            node6 = node2 + nodesPerLayer
            node7 = node3 + nodesPerLayer
            node8 = node4 + nodesPerLayer

            # Determinar material
            # Zapata si: z >= -h_zapata Y x <= zapata_quarter Y y <= zapata_quarter
            if z_elem >= -h_zapata and x_elem <= zapata_quarter and y_elem <= zapata_quarter:
                matTag = 2  # Concreto
            else:
                matTag = 1  # Suelo

            ops.element('stdBrick', elementCounter, node1, node2, node3, node4,
                       node5, node6, node7, node8, matTag)
            elementCounter += 1

total_elements = elementCounter - 1
print(f"  Total elementos: {total_elements}")

# ================================================================================
# CARGAS
# ================================================================================
print(f"\n⚡ APLICANDO CARGAS...")

ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Cargas
P_column_full = 1000.0
P_zapata_full = B * B * h_zapata * rho_concrete * 9.81 / 1000
P_total_full = P_column_full + P_zapata_full
P_total_quarter = P_total_full / 4.0

if len(zapata_nodes) > 0:
    P_per_node = -P_total_quarter / len(zapata_nodes)

    for node in zapata_nodes:
        ops.load(node, 0.0, 0.0, P_per_node)

    print(f"  Carga total (completo): {P_total_full:.2f} kN")
    print(f"  Carga 1/4: {P_total_quarter:.2f} kN")
    print(f"  Nodos cargados: {len(zapata_nodes)}")
    print(f"  Carga por nodo: {P_per_node:.4f} kN")

# ================================================================================
# ANÁLISIS
# ================================================================================
print(f"\n" + "="*80)
print("EJECUTANDO ANÁLISIS")
print("="*80)

ops.system('BandGeneral')
ops.numberer('RCM')
ops.constraints('Transformation')
ops.test('NormDispIncr', 1.0e-6, 100, 0)
ops.algorithm('Newton')
ops.integrator('LoadControl', 1.0)
ops.analysis('Static')

print("\nAnalizando...")
ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado exitosamente")
else:
    print("✗ Error en el análisis")
    exit(1)

# ================================================================================
# EXTRACCIÓN DE RESULTADOS
# ================================================================================
print(f"\n" + "="*80)
print("EXTRAYENDO RESULTADOS")
print("="*80)

settlements = []
for nodeTag, (x, y, z) in nodeCoord.items():
    disp = ops.nodeDisp(nodeTag, 3)
    settlements.append({
        'X': x,
        'Y': y,
        'Z': z,
        'Settlement_mm': abs(disp) * 1000
    })

df = pd.DataFrame(settlements)

# Estadísticas
surface_df = df[df['Z'] == 0]
max_settlement = surface_df['Settlement_mm'].max()
min_settlement = surface_df['Settlement_mm'].min()
avg_settlement = surface_df['Settlement_mm'].mean()

print(f"\n📊 RESULTADOS:")
print(f"  Asentamiento máximo: {max_settlement:.4f} mm")
print(f"  Asentamiento mínimo: {min_settlement:.4f} mm")
print(f"  Asentamiento promedio (superficie): {avg_settlement:.4f} mm")

# Guardar datos
df.to_csv('settlements_3d_complete_refined.csv', index=False)
surface_df[['X', 'Y', 'Settlement_mm']].to_csv('surface_settlements_refined.csv', index=False)

print(f"\n✓ Datos guardados:")
print(f"  - settlements_3d_complete_refined.csv ({len(df)} puntos)")
print(f"  - surface_settlements_refined.csv ({len(surface_df)} puntos)")

print(f"\n" + "="*80)
print("ANÁLISIS COMPLETADO")
print("="*80)
