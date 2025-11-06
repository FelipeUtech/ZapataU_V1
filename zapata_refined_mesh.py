#!/usr/bin/env python3
"""
Modelo 1/4 de Zapata con Malla Refinada AUTOMATIZADA
- Dominio: 6B (automático en función de B)
- Profundidad: 20m
- Malla refinada en zapata: 0.25m × 0.25m
- Malla exterior: 0.5m × 0.5m
- Malla profundidad < 10m: 0.5m
- Malla profundidad > 10m: 1.0m
- Zapata 10× más rígida
- Df = 0 (BASE de zapata en superficie z=0)
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
# PARÁMETROS GEOMÉTRICOS - AUTOMATIZADOS EN FUNCIÓN DE B
# ================================================================================
B = 3.0              # Ancho zapata completa (PARÁMETRO PRINCIPAL)
h_zapata = 0.6       # Altura zapata
Df = 0.0             # Profundidad de fundación (superficial)

# Cálculos automáticos basados en B
zapata_quarter = B / 2.0           # Zapata en modelo 1/4
dominio_quarter = 6 * B / 2.0      # Dominio 6B en modelo 1/4: (6B)/2 = 3B
Lz_soil_shallow = 10.0             # Profundidad hasta 10m (malla fina)
Lz_soil_deep = 20.0                # Profundidad total 20m

print("\n" + "="*80)
print("MODELO 1/4 CON MALLA REFINADA AUTOMATIZADA - DOMINIO 6B")
print("="*80)
print(f"\n📐 GEOMETRÍA (automatizada en función de B={B}m):")
print(f"  Zapata completa: {B}m × {B}m × {h_zapata}m")
print(f"  Dominio completo: {6*B}m × {6*B}m × {Lz_soil_deep}m (6B horizontal, 20m profundidad)")
print(f"  Modelo 1/4: {dominio_quarter}m × {dominio_quarter}m × {Lz_soil_deep}m")
print(f"  Zapata 1/4: {zapata_quarter}m × {zapata_quarter}m")
print(f"  Df: {Df}m (base zapata en superficie)")

# ================================================================================
# MALLA NO UNIFORME AUTOMATIZADA
# ================================================================================
print(f"\n🔬 GENERANDO MALLA NO UNIFORME AUTOMATIZADA:")

# Tamaños de elemento
dx_zapata = 0.25      # Elemento en zona zapata
dx_exterior = 0.5     # Elemento en zona exterior
dz_shallow = 0.5      # Elemento vertical hasta 3B
dz_deep = 1.0         # Elemento vertical después de 3B

# Coordenadas X e Y (idénticas por simetría)
# Zona zapata: 0 a B/2 con dx=0.25m
x_zapata = np.arange(0, zapata_quarter + 0.01, dx_zapata)
# Zona exterior: B/2 a 3B/2 con dx=0.5m
x_start_exterior = zapata_quarter + dx_exterior
x_exterior = np.arange(x_start_exterior, dominio_quarter + 0.01, dx_exterior)
# Combinar
x_coords = np.concatenate([x_zapata, x_exterior])
y_coords = x_coords.copy()

print(f"  Malla horizontal:")
print(f"    - Zona zapata (0 a {zapata_quarter}m): dx = {dx_zapata}m → {len(x_zapata)} nodos")
print(f"    - Zona exterior ({zapata_quarter}m a {dominio_quarter}m): dx = {dx_exterior}m → {len(x_exterior)} nodos")
print(f"    - Total nodos X/Y: {len(x_coords)}")

# Coordenadas Z: variable
# IMPORTANTE: Con Df=0, z=0 es la BASE de la zapata (superficie del suelo)
# La zapata va de z=0 (base) a z=h_zapata (tope)
# El suelo va de z=0 (superficie) hacia abajo (z<0)

# Primero crear nodos de zapata (encima de z=0)
z_zapata = np.arange(h_zapata, -0.01, -dz_shallow)  # Desde tope zapata hasta base
# Zona superficial del suelo: 0 a -10m con dz_shallow
z_shallow = np.arange(0, -Lz_soil_shallow - 0.01, -dz_shallow)
# Zona profunda: -10m a -20m con dz_deep
z_start_deep = -Lz_soil_shallow - dz_deep
z_deep = np.arange(z_start_deep, -Lz_soil_deep - 0.01, -dz_deep)
# Combinar TODO: zapata + suelo superficial + suelo profundo
z_coords = np.concatenate([z_zapata, z_shallow, z_deep])
# Eliminar duplicados y ordenar de mayor a menor
z_coords = np.unique(z_coords)[::-1]

print(f"  Malla vertical:")
print(f"    - Zapata ({h_zapata}m a 0m): dz = {dz_shallow}m → {len(z_zapata)} niveles")
print(f"    - Suelo superficial (0 a -{Lz_soil_shallow}m): dz = {dz_shallow}m → {len(z_shallow)} niveles")
print(f"    - Suelo profundo (-{Lz_soil_shallow}m a -{Lz_soil_deep}m): dz = {dz_deep}m → {len(z_deep)} niveles")
print(f"    - Total niveles Z: {len(z_coords)}")

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

            # Superficie (z=0, base de zapata / superficie de suelo)
            if abs(z - 0.0) < 0.001:
                surface_nodes.append(nodeCounter)
                # Nodos bajo zapata (donde se aplica la carga)
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

# Base fija (fondo del modelo)
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
            # Con Df=0: zapata va de z=0 (base en superficie) a z=h_zapata (tope)
            # Zapata si: z > 0 Y z <= h_zapata Y x <= zapata_quarter Y y <= zapata_quarter
            if z_elem > 0 and z_elem <= h_zapata and x_elem <= zapata_quarter and y_elem <= zapata_quarter:
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
output_3d = 'settlements_3d_complete.csv'
output_surface = 'surface_settlements_quarter_full.csv'

df.to_csv(output_3d, index=False)
surface_df[['X', 'Y', 'Settlement_mm']].to_csv(output_surface, index=False)

print(f"\n✓ Datos guardados:")
print(f"  - {output_3d} ({len(df)} puntos)")
print(f"  - {output_surface} ({len(surface_df)} puntos)")

print(f"\n" + "="*80)
print("ANÁLISIS COMPLETADO")
print("="*80)
