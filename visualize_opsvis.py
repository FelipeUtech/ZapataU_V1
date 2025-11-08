#!/usr/bin/env python3
"""
Visualización avanzada con opsvis
Genera visualizaciones interactivas del modelo OpenSees
"""

import openseespy.opensees as ops
import opsvis as opsv
import matplotlib.pyplot as plt
from config import ZAPATA, DOMINIO, ESTRATOS_SUELO, MATERIAL_ZAPATA, CARGAS, MALLA
import utils

print("="*80)
print("VISUALIZACIÓN AVANZADA CON OPSVIS")
print("="*80)
print()

# Obtener configuración
zapata = ZAPATA
dominio_cfg = DOMINIO
estratos_suelo = ESTRATOS_SUELO
mat_zapata = MATERIAL_ZAPATA
cargas = CARGAS
malla_cfg = MALLA
tipo_malla = malla_cfg['tipo']

B_completa = zapata['B']
L_completa = zapata['L']
h_zapata = zapata['h']
Df = zapata['Df']

# Configuración de dominio
num_B = dominio_cfg['factor_horizontal']
profundidad = dominio_cfg['profundidad']
usar_cuarto = dominio_cfg['usar_cuarto_modelo']

# Modelo 1/4
B_modelo = B_completa / 2.0
L_modelo = L_completa / 2.0
dominio_ancho = num_B * B_completa / 2.0
dominio_largo = num_B * B_completa / 2.0

zapata_modelo = {
    'B': B_modelo,
    'L': L_modelo,
    'h': h_zapata,
    'Df': Df,
    'x_min': 0.0,
    'y_min': 0.0
}

dominio = {
    'Lx': dominio_ancho,
    'Ly': dominio_largo,
    'Lz': profundidad
}

print(f"Configuración:")
print(f"  Zapata: {B_completa}m × {L_completa}m × {h_zapata}m")
print(f"  Df: {Df}m")
print(f"  Dominio: {dominio_ancho*2}m × {dominio_largo*2}m × {profundidad}m")
print(f"  Malla: {tipo_malla}")
print()

# ============================================================================
# PASO 1: GENERAR MALLA
# ============================================================================
print("PASO 1: Generando malla...")

if tipo_malla == 'graded':
    params = malla_cfg['graded']
    x_coords, y_coords, z_coords = utils.generar_malla_gradual(
        dominio, zapata_modelo, params)
    nx = len(x_coords) - 1
    ny = len(y_coords) - 1
    nz = len(z_coords) - 1
else:
    print(f"Error: tipo de malla '{tipo_malla}' no soportado")
    exit(1)

print(f"✓ Malla generada: {nx} × {ny} × {nz} elementos")
print()

# ============================================================================
# PASO 2: CREAR MODELO EN OPENSEES
# ============================================================================
print("PASO 2: Creando modelo en OpenSeesPy...")

ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# Crear nodos
print("  Creando nodos...")
node_coords, surface_nodes = utils.crear_nodos(x_coords, y_coords, z_coords)
num_nodos = len(node_coords)
nodes_per_layer = (nx + 1) * (ny + 1)

print(f"✓ {num_nodos} nodos creados")

# Condiciones de borde
print("  Aplicando condiciones de borde...")
utils.aplicar_condiciones_borde(nz + 1, nodes_per_layer, nx, ny, usar_cuarto)
print("✓ Condiciones de borde aplicadas")

# Definir materiales
print("  Definiendo materiales...")

estratos_con_tags = []
for i, estrato in enumerate(estratos_suelo, 1):
    mat_tag = i
    ops.nDMaterial('ElasticIsotropic', mat_tag,
                   estrato['E'], estrato['nu'], estrato['rho'])
    estratos_con_tags.append({
        'espesor': estrato['espesor'],
        'mat_tag': mat_tag
    })

# Material concreto (zapata)
mat_tag_zapata = len(estratos_suelo) + 1
ops.nDMaterial('ElasticIsotropic', mat_tag_zapata,
               mat_zapata['E'], mat_zapata['nu'], mat_zapata['rho'])

# Material aire para excavación
if Df > 0:
    mat_tag_aire = mat_tag_zapata + 1
    ops.nDMaterial('ElasticIsotropic', mat_tag_aire, 1.0, 0.3, 0.001)

print(f"✓ {len(estratos_suelo)} estratos + zapata")

# Crear elementos
print("  Creando elementos...")
n_elements_por_estrato, n_elements_zapata = utils.crear_elementos_con_zapata(
    nx, ny, nz, nodes_per_layer, x_coords, y_coords, z_coords,
    zapata_modelo, mat_tag_zapata=mat_tag_zapata, estratos_suelo=estratos_con_tags
)

total_elementos = sum(n_elements_por_estrato) + n_elements_zapata
print(f"✓ {total_elementos} elementos creados")
print()

# ============================================================================
# PASO 3: APLICAR CARGAS
# ============================================================================
print("PASO 3: Aplicando cargas...")

# Identificar nodos en el tope de la zapata
# BASE en z=-Df, TOPE en z=-Df+h
z_tope_zapata = -Df + h_zapata
nodos_zapata_top = utils.identificar_nodos_en_cota(
    node_coords, z_tope_zapata, zapata_modelo, tolerancia=0.05
)

num_nodos_carga = len(nodos_zapata_top)

if num_nodos_carga > 0:
    # Carga para modelo 1/4
    P_column_quarter = cargas['P_column'] / 4.0

    # Crear timeSeries y pattern antes de aplicar cargas
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)

    carga_total = utils.aplicar_cargas(
        nodos_zapata_top, P_column_quarter, zapata_modelo,
        mat_zapata, cargas['incluir_peso_propio']
    )

    print(f"✓ Carga aplicada: {carga_total:.2f} kN en {num_nodos_carga} nodos")
else:
    print("⚠️  No se encontraron nodos para aplicar carga")

print()

# ============================================================================
# PASO 4: EJECUTAR ANÁLISIS
# ============================================================================
print("PASO 4: Ejecutando análisis...")

ops.system('BandGeneral')
ops.numberer('RCM')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado exitosamente")
else:
    print("⚠️  Advertencia: El análisis reportó problemas")

print()

# Calcular asentamiento máximo
max_settlement = 0.0
for node_tag in node_coords.keys():
    disp = ops.nodeDisp(node_tag)
    if abs(disp[2]) > abs(max_settlement):
        max_settlement = disp[2]

print(f"Asentamiento máximo: {abs(max_settlement)*1000:.2f} mm")
print()

# ============================================================================
# PASO 5: VISUALIZACIONES CON OPSVIS
# ============================================================================
print("="*80)
print("GENERANDO VISUALIZACIONES CON OPSVIS")
print("="*80)
print()

# Factor de escala para deformaciones
scale_factor = dominio_ancho * 0.1 / abs(max_settlement) if max_settlement != 0 else 100

# ============================================================================
# VISUALIZACIÓN 1: Modelo sin deformar
# ============================================================================
print("1. Modelo sin deformar...")

fig1 = plt.figure(figsize=(16, 12))
ax1 = fig1.add_subplot(111, projection='3d')

opsv.plot_model(az_el=(-60, 30), fig_wi_he=(16, 12))

plt.title(f'Modelo OpenSees - Zapata {B_completa}m×{L_completa}m, Df={Df}m\n'
          f'Modelo 1/4 simetría - {num_nodos} nodos, {total_elementos} elementos',
          fontsize=16, fontweight='bold', pad=20)

output1 = 'modelo_opsvis_undeformed.png'
plt.savefig(output1, dpi=200, bbox_inches='tight', facecolor='white')
print(f"✓ Guardado: {output1}")
plt.close()

# ============================================================================
# VISUALIZACIÓN 2: Modelo deformado (vista isométrica)
# ============================================================================
print("2. Modelo deformado - vista isométrica...")

fig2 = plt.figure(figsize=(16, 12))

opsv.plot_defo(
    sfac=scale_factor,
    az_el=(-60, 30),
    fig_wi_he=(16, 12)
)

plt.title(f'Modelo Deformado - Vista Isométrica (escala {scale_factor:.0f}x)\n'
          f'Asentamiento máximo: {abs(max_settlement)*1000:.2f} mm, Df={Df}m',
          fontsize=16, fontweight='bold', pad=20)

output2 = 'modelo_opsvis_deformed.png'
plt.savefig(output2, dpi=200, bbox_inches='tight', facecolor='white')
print(f"✓ Guardado: {output2}")
plt.close()

# ============================================================================
# VISUALIZACIÓN 3: Vista lateral con deformación
# ============================================================================
print("3. Vista lateral con deformación...")

fig3 = plt.figure(figsize=(18, 10))

opsv.plot_defo(
    sfac=scale_factor,
    az_el=(0, 0),  # Vista lateral (en el plano YZ)
    fig_wi_he=(18, 10)
)

plt.title(f'Vista Lateral - Deformación Vertical (escala {scale_factor:.0f}x)\n'
          f'Df={Df}m, Asentamiento máx: {abs(max_settlement)*1000:.2f} mm',
          fontsize=16, fontweight='bold', pad=20)

output3 = 'modelo_opsvis_lateral.png'
plt.savefig(output3, dpi=200, bbox_inches='tight', facecolor='white')
print(f"✓ Guardado: {output3}")
plt.close()

# ============================================================================
# VISUALIZACIÓN 4: Vista en planta
# ============================================================================
print("4. Vista en planta...")

fig4 = plt.figure(figsize=(12, 12))

opsv.plot_defo(
    sfac=scale_factor,
    az_el=(0, 90),  # Vista desde arriba
    fig_wi_he=(12, 12)
)

plt.title(f'Vista en Planta - Deformación (escala {scale_factor:.0f}x)\n'
          f'Zapata {B_completa}m×{L_completa}m, Df={Df}m',
          fontsize=16, fontweight='bold', pad=20)

output4 = 'modelo_opsvis_planta.png'
plt.savefig(output4, dpi=200, bbox_inches='tight', facecolor='white')
print(f"✓ Guardado: {output4}")
plt.close()

# ============================================================================
# RESUMEN
# ============================================================================
print()
print("="*80)
print("VISUALIZACIÓN COMPLETADA")
print("="*80)
print()
print("Archivos generados:")
print(f"  • {output1} - Modelo sin deformar")
print(f"  • {output2} - Modelo deformado (isométrico)")
print(f"  • {output3} - Vista lateral")
print(f"  • {output4} - Vista en planta")
print()
print(f"Modelo: {num_nodos} nodos, {total_elementos} elementos")
print(f"Profundidad de desplante: {Df} m")
print(f"Asentamiento máximo: {abs(max_settlement)*1000:.2f} mm")
print(f"Factor de escala deformación: {scale_factor:.0f}x")
print()
print("="*80)
