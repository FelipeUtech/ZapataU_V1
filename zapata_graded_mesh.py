#!/usr/bin/env python3
"""
Modelo 1/4 de Zapata con MALLA GRADUAL ÓPTIMA
- Malla refinada en zapata con transición gradual
- Elementos crecen geométricamente hacia los bordes
- Dominio: 6B (18m × 18m completo)
- Profundidad: 20m
- Df = 0 (BASE de zapata en superficie z=0)
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd

# ================================================================================
# FUNCIONES AUXILIARES PARA MALLA GRADUAL
# ================================================================================

def geometric_grading(start, end, n_elements, first_size, last_size=None, return_coords=True):
    """
    Genera coordenadas con crecimiento geométrico.

    Parameters:
    -----------
    start : float
        Coordenada inicial
    end : float
        Coordenada final
    n_elements : int
        Número de elementos deseados
    first_size : float
        Tamaño del primer elemento
    last_size : float, optional
        Tamaño del último elemento (si None, se calcula automáticamente)
    return_coords : bool
        Si True retorna coordenadas, si False retorna tamaños

    Returns:
    --------
    coords : array
        Coordenadas de los nodos
    """
    L = abs(end - start)

    if last_size is None:
        # Calcular ratio óptimo para n_elements
        # Usar búsqueda numérica para encontrar ratio
        ratio = 1.1  # Valor inicial

        for _ in range(100):  # Iteraciones para converger
            sum_sizes = first_size * (1 - ratio**n_elements) / (1 - ratio)
            if abs(sum_sizes - L) < 1e-6:
                break
            # Ajustar ratio
            if sum_sizes < L:
                ratio += 0.001
            else:
                ratio -= 0.001
    else:
        # Calcular ratio dado first_size y last_size
        ratio = (last_size / first_size) ** (1.0 / (n_elements - 1))

    # Generar tamaños de elementos
    sizes = [first_size * (ratio ** i) for i in range(n_elements)]

    # Normalizar para que sumen exactamente L
    actual_sum = sum(sizes)
    sizes = [s * L / actual_sum for s in sizes]

    if return_coords:
        # Generar coordenadas
        coords = [start]
        for size in sizes:
            coords.append(coords[-1] + size * np.sign(end - start))
        return np.array(coords)
    else:
        return np.array(sizes)


def bilinear_grading(start, end, n_fine, n_coarse, fine_size, transition_point=None):
    """
    Malla con zona refinada y transición gradual.

    Parameters:
    -----------
    start : float
        Coordenada inicial
    end : float
        Coordenada final
    n_fine : int
        Número de elementos en zona refinada
    n_coarse : int
        Número de elementos en zona gruesa
    fine_size : float
        Tamaño de elemento en zona refinada
    transition_point : float, optional
        Punto donde termina zona refinada

    Returns:
    --------
    coords : array
        Coordenadas de los nodos
    """
    if transition_point is None:
        # 1/3 del dominio refinado por defecto
        transition_point = start + (end - start) / 3.0

    L_fine = abs(transition_point - start)
    L_coarse = abs(end - transition_point)

    # Zona refinada con elementos uniformes
    coords_fine = np.linspace(start, transition_point, n_fine + 1)

    # Zona gruesa con crecimiento geométrico
    first_coarse = fine_size
    coords_coarse = geometric_grading(transition_point, end, n_coarse,
                                       first_coarse, return_coords=True)

    # Combinar (eliminar duplicado en transition_point)
    coords = np.concatenate([coords_fine[:-1], coords_coarse])

    return coords


# ================================================================================
# INICIALIZACIÓN
# ================================================================================
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# ================================================================================
# PARÁMETROS GEOMÉTRICOS
# ================================================================================
B = 3.0              # Ancho zapata completa
h_zapata = 0.6       # Altura zapata
Df = 0.0             # Profundidad de fundación

zapata_quarter = B / 2.0           # Zapata en modelo 1/4
dominio_quarter = 6 * B / 2.0      # Dominio 6B en modelo 1/4: (6B)/2 = 3B = 9m
Lz_soil_deep = 20.0                # Profundidad total 20m

print("\n" + "="*80)
print("MODELO 1/4 CON MALLA GRADUAL ÓPTIMA - DOMINIO 6B")
print("="*80)
print(f"\n📐 GEOMETRÍA (automatizada en función de B={B}m):")
print(f"  Zapata completa: {B}m × {B}m × {h_zapata}m")
print(f"  Dominio completo: {6*B}m × {6*B}m × {Lz_soil_deep}m (6B horizontal, 20m profundidad)")
print(f"  Modelo 1/4: {dominio_quarter}m × {dominio_quarter}m × {Lz_soil_deep}m")
print(f"  Zapata 1/4: {zapata_quarter}m × {zapata_quarter}m")
print(f"  Df: {Df}m (base zapata en superficie)")

# ================================================================================
# MALLA GRADUAL OPTIMIZADA
# ================================================================================
print(f"\n🔬 GENERANDO MALLA GRADUAL OPTIMIZADA:")

# ---------------------------
# MALLA HORIZONTAL (X, Y)
# ---------------------------
print(f"\n  Malla horizontal con transición gradual:")

# Estrategia:
# - Zona zapata (0 a 1.5m): elementos 0.25m
# - Transición gradual hasta borde (1.5m a 9m)

n_zapata = int(zapata_quarter / 0.25)  # 6 elementos en zapata
n_transition = 10  # Elementos en transición

# Generar coordenadas X con crecimiento gradual
x_zapata = np.linspace(0, zapata_quarter, n_zapata + 1)
x_transition = geometric_grading(zapata_quarter, dominio_quarter, n_transition,
                                  first_size=0.25, return_coords=True)

# Combinar (eliminar duplicado en zapata_quarter)
x_coords = np.concatenate([x_zapata[:-1], x_transition])
y_coords = x_coords.copy()  # Simetría

dx_min = np.min(np.diff(x_coords))
dx_max = np.max(np.diff(x_coords))
print(f"    Zona zapata: {n_zapata} elementos × 0.25m")
print(f"    Zona transición: {n_transition} elementos (crecimiento gradual)")
print(f"    Tamaño elemento: {dx_min:.3f}m (mín) → {dx_max:.3f}m (máx)")
print(f"    Total nodos X/Y: {len(x_coords)}")
print(f"    Ratio máx/mín: {dx_max/dx_min:.2f}×")

# ---------------------------
# MALLA VERTICAL (Z)
# ---------------------------
print(f"\n  Malla vertical con transición gradual:")

# Estrategia:
# - Zapata (0.6m a 0m): 2-3 elementos uniformes
# - Zona superficial (0 a -5m): elementos pequeños 0.5m
# - Transición gradual (-5m a -20m): crecimiento geométrico

# Zapata
n_zapata_z = 2
z_zapata = np.linspace(h_zapata, 0, n_zapata_z + 1)

# Zona superficial (importante para interacción zapata-suelo)
depth_fine = 5.0  # Primeros 5m refinados
n_fine_z = int(depth_fine / 0.5)  # 10 elementos
z_fine = np.linspace(0, -depth_fine, n_fine_z + 1)

# Zona profunda con transición gradual
n_deep_z = 8  # Elementos en profundidad
z_deep = geometric_grading(-depth_fine, -Lz_soil_deep, n_deep_z,
                           first_size=0.5, return_coords=True)

# Combinar eliminando duplicados
z_coords = np.concatenate([z_zapata[:-1], z_fine[:-1], z_deep])
z_coords = np.unique(z_coords)[::-1]  # Ordenar de mayor a menor y eliminar duplicados

dz_min = np.min(np.abs(np.diff(z_coords)))
dz_max = np.max(np.abs(np.diff(z_coords)))
print(f"    Zapata: {n_zapata_z} elementos uniformes")
print(f"    Zona superficial (0 a -{depth_fine}m): {n_fine_z} elementos × 0.5m")
print(f"    Zona profunda (-{depth_fine}m a -{Lz_soil_deep}m): {n_deep_z} elementos (gradual)")
print(f"    Tamaño elemento: {dz_min:.3f}m (mín) → {dz_max:.3f}m (máx)")
print(f"    Total niveles Z: {len(z_coords)}")
print(f"    Ratio máx/mín: {dz_max/dz_min:.2f}×")

# ---------------------------
# ANÁLISIS DE CALIDAD DE MALLA
# ---------------------------
print(f"\n  📊 Análisis de calidad de malla:")
total_nodes = len(x_coords) * len(y_coords) * len(z_coords)
total_elements = (len(x_coords)-1) * (len(y_coords)-1) * (len(z_coords)-1)

# Calcular aspect ratio típico
typical_dx = np.median(np.diff(x_coords))
typical_dz = np.median(np.abs(np.diff(z_coords)))
aspect_ratio = typical_dx / typical_dz

print(f"    Total nodos: {total_nodes}")
print(f"    Total elementos: {total_elements}")
print(f"    Aspect ratio típico: {aspect_ratio:.2f}")
print(f"    Reducción vs malla uniforme: ~{15972 / total_nodes:.1f}× menos nodos")

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

total_nodes_actual = nodeCounter - 1
nodesPerLayer = len(x_coords) * len(y_coords)

print(f"  Total nodos: {total_nodes_actual}")
print(f"  Nodos por capa: {nodesPerLayer}")
print(f"  Nodos bajo zapata: {len(zapata_nodes)}")

# ================================================================================
# CONDICIONES DE BORDE
# ================================================================================
print(f"\n🔒 APLICANDO CONDICIONES DE BORDE...")

# Base fija (fondo del modelo)
baseNodeTags = list(range(nodesPerLayer * nz + 1, total_nodes_actual + 1))
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

E_concrete = 250e6    # kPa = 250 GPa (10× más rígida)
nu_concrete = 0.2
rho_concrete = 2400.0

ops.nDMaterial('ElasticIsotropic', 1, E_soil, nu_soil, rho_soil)
ops.nDMaterial('ElasticIsotropic', 2, E_concrete, nu_concrete, rho_concrete)

print(f"  Suelo: E = {E_soil/1000:.1f} MPa")
print(f"  Zapata: E = {E_concrete/1e6:.1f} GPa (10× más rígida)")
print(f"  Relación E_zapata/E_suelo = {E_concrete/E_soil:.0f}×")

# ================================================================================
# ELEMENTOS
# ================================================================================
print(f"\n🧱 GENERANDO ELEMENTOS...")

elementCounter = 1

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

total_elements_actual = elementCounter - 1
print(f"  Total elementos: {total_elements_actual}")

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
output_3d = 'settlements_3d_graded.csv'
output_surface = 'surface_settlements_graded.csv'

df.to_csv(output_3d, index=False)
surface_df[['X', 'Y', 'Settlement_mm']].to_csv(output_surface, index=False)

print(f"\n✓ Datos guardados:")
print(f"  - {output_3d} ({len(df)} puntos)")
print(f"  - {output_surface} ({len(surface_df)} puntos)")

print(f"\n" + "="*80)
print("ANÁLISIS COMPLETADO - MALLA GRADUAL OPTIMIZADA")
print("="*80)
print(f"\n🎯 VENTAJAS MALLA GRADUAL:")
print(f"  ✓ Nodos totales: {total_nodes_actual} (vs 15,972 malla uniforme)")
print(f"  ✓ Reducción: {100 * (1 - total_nodes_actual/15972):.1f}% menos nodos")
print(f"  ✓ Refinamiento donde se necesita (zapata + superficie)")
print(f"  ✓ Elementos grandes en bordes (más eficiente)")
print(f"  ✓ Transición suave (mejor aspect ratio)")
print(f"  ✓ Tiempo de cómputo reducido\n")
