#!/usr/bin/env python3
"""
Visualización SIMPLIFICADA y CLARA del modelo
Menos líneas, más colores sólidos, más fácil de entender
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pandas as pd
import numpy as np
from config import ZAPATA, DOMINIO

# Configuración
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

# Cargar datos
zapata = ZAPATA
B = zapata['B']
L = zapata['L']
h = zapata['h']
Df = zapata['Df']

B_quarter = B / 2.0
L_quarter = L / 2.0

print("="*80)
print("VISUALIZACIÓN SIMPLIFICADA - MODELO 3D")
print("="*80)
print(f"\nZapata: {B}m × {L}m × {h}m")
print(f"Profundidad desplante: {Df}m\n")

# Cargar asentamientos
df_surface = pd.read_csv('surface_settlements.csv')
df_3d = pd.read_csv('settlements_3d.csv')

# Crear figura grande
fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('white')

# ============================================================================
# VISTA ISOMÉTRICA SIMPLIFICADA
# ============================================================================
ax1 = fig.add_subplot(2, 3, 1, projection='3d')
ax1.set_facecolor('white')

# 1. ZAPATA - Bloque sólido naranja
z_base_zapata = -Df
z_top_zapata = -Df + h

zapata_vertices = np.array([
    [0, 0, z_base_zapata], [B_quarter, 0, z_base_zapata],
    [B_quarter, L_quarter, z_base_zapata], [0, L_quarter, z_base_zapata],
    [0, 0, z_top_zapata], [B_quarter, 0, z_top_zapata],
    [B_quarter, L_quarter, z_top_zapata], [0, L_quarter, z_top_zapata]
])

zapata_faces = [
    [zapata_vertices[0], zapata_vertices[1], zapata_vertices[5], zapata_vertices[4]],  # Frente
    [zapata_vertices[1], zapata_vertices[2], zapata_vertices[6], zapata_vertices[5]],  # Derecha
    [zapata_vertices[2], zapata_vertices[3], zapata_vertices[7], zapata_vertices[6]],  # Atrás
    [zapata_vertices[3], zapata_vertices[0], zapata_vertices[4], zapata_vertices[7]],  # Izquierda
    [zapata_vertices[4], zapata_vertices[5], zapata_vertices[6], zapata_vertices[7]],  # Top
    [zapata_vertices[0], zapata_vertices[1], zapata_vertices[2], zapata_vertices[3]]   # Bottom
]

zapata_collection = Poly3DCollection(zapata_faces, alpha=1.0, facecolor='darkorange',
                                     edgecolor='black', linewidth=2.5)
ax1.add_collection3d(zapata_collection)

# 2. EXCAVACIÓN - Si Df > 0, mostrar como volumen semi-transparente
if Df > 0.01:
    exc_vertices = np.array([
        [0, 0, 0], [B_quarter, 0, 0],
        [B_quarter, L_quarter, 0], [0, L_quarter, 0],
        [0, 0, z_top_zapata], [B_quarter, 0, z_top_zapata],
        [B_quarter, L_quarter, z_top_zapata], [0, L_quarter, z_top_zapata]
    ])

    exc_faces = [
        [exc_vertices[0], exc_vertices[1], exc_vertices[5], exc_vertices[4]],
        [exc_vertices[1], exc_vertices[2], exc_vertices[6], exc_vertices[5]],
        [exc_vertices[2], exc_vertices[3], exc_vertices[7], exc_vertices[6]],
        [exc_vertices[3], exc_vertices[0], exc_vertices[4], exc_vertices[7]]
    ]

    exc_collection = Poly3DCollection(exc_faces, alpha=0.15, facecolor='gray',
                                      edgecolor='darkgray', linewidth=2, linestyle='--')
    ax1.add_collection3d(exc_collection)

    # Borde superior de excavación (en superficie)
    exc_top = [[exc_vertices[0], exc_vertices[1], exc_vertices[2], exc_vertices[3]]]
    exc_top_collection = Poly3DCollection(exc_top, alpha=0.3, facecolor='lightgray',
                                          edgecolor='red', linewidth=3)
    ax1.add_collection3d(exc_top_collection)

# 3. SUPERFICIE CON ASENTAMIENTOS - Solo contornos, sin malla densa
x_surf = df_surface['X'].values.reshape(13, 13)
y_surf = df_surface['Y'].values.reshape(13, 13)
z_surf = np.zeros_like(x_surf)
settlement_surf = df_surface['Settlement_mm'].values.reshape(13, 13)

# Contornos de asentamientos en superficie
contour = ax1.contourf(x_surf, y_surf, settlement_surf,
                       levels=15, cmap='RdYlBu_r', alpha=0.7, offset=0,
                       zdir='z')

# 4. PLANOS DE SIMETRÍA con asentamientos
# Plano X=0 (muy simplificado)
df_x0 = df_3d[df_3d['X'] < 0.1].copy()
if len(df_x0) > 0:
    y_x0 = df_x0['Y'].values
    z_x0 = df_x0['Z'].values
    s_x0 = df_x0['Settlement_mm'].values

    scatter_x0 = ax1.scatter(np.zeros_like(y_x0), y_x0, z_x0, c=s_x0,
                             cmap='RdYlBu_r', s=30, alpha=0.6, edgecolor='none')

# Plano Y=0 (muy simplificado)
df_y0 = df_3d[df_3d['Y'] < 0.1].copy()
if len(df_y0) > 0:
    x_y0 = df_y0['X'].values
    z_y0 = df_y0['Z'].values
    s_y0 = df_y0['Settlement_mm'].values

    scatter_y0 = ax1.scatter(x_y0, np.zeros_like(x_y0), z_y0, c=s_y0,
                             cmap='RdYlBu_r', s=30, alpha=0.6, edgecolor='none')

# Colorbar
cbar = plt.colorbar(contour, ax=ax1, shrink=0.5, aspect=10, pad=0.1)
cbar.set_label('Asentamiento (mm)', fontsize=11, fontweight='bold')

# Configurar ejes
ax1.set_xlim(0, 9)
ax1.set_ylim(0, 9)
ax1.set_zlim(-20, 0.5)

ax1.set_xlabel('X (m)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
ax1.set_zlabel('Z (m)', fontsize=12, fontweight='bold')

ax1.set_title(f'Vista 3D Simplificada\nZapata {B}m×{L}m, Df={Df}m',
              fontsize=14, fontweight='bold', pad=15)

ax1.view_init(elev=25, azim=-65)

# Añadir leyenda simple
legend_text = (
    f'🟧 ZAPATA\n'
    f'   {B}m×{L}m×{h}m\n'
    f'   Df={Df}m\n\n'
    f'⬜ EXCAVACIÓN\n'
    f'   Prof: {Df}m'
)
ax1.text2D(0.02, 0.75, legend_text, transform=ax1.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=1.5))

# ============================================================================
# VISTA EN PLANTA
# ============================================================================
ax2 = fig.add_subplot(2, 3, 2)

contour2 = ax2.contourf(x_surf, y_surf, settlement_surf, levels=20, cmap='RdYlBu_r')
ax2.contour(x_surf, y_surf, settlement_surf, levels=10, colors='black', linewidths=0.5, alpha=0.3)

# Contorno de zapata/excavación
rect_color = 'red' if Df > 0.01 else 'black'
rect_label = 'Excavación' if Df > 0.01 else 'Zapata'
rect = plt.Rectangle((0, 0), B_quarter, L_quarter, fill=False,
                      edgecolor=rect_color, linewidth=3, label=rect_label)
ax2.add_patch(rect)

plt.colorbar(contour2, ax=ax2, label='Asentamiento (mm)')

ax2.set_xlabel('X (m)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Y (m)', fontsize=11, fontweight='bold')
ax2.set_title(f'Vista en Planta\nAsentamientos en Superficie', fontsize=13, fontweight='bold')
ax2.set_aspect('equal')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# ============================================================================
# CORTE VERTICAL X=0
# ============================================================================
ax3 = fig.add_subplot(2, 3, 3)

# Datos del plano X=0
if len(df_x0) > 0:
    # Reorganizar datos para contorno
    y_unique = sorted(df_x0['Y'].unique())
    z_unique = sorted(df_x0['Z'].unique(), reverse=True)

    Y_grid, Z_grid = np.meshgrid(y_unique, z_unique)
    S_grid = np.zeros_like(Y_grid)

    for i, z in enumerate(z_unique):
        for j, y in enumerate(y_unique):
            mask = (np.abs(df_x0['Y'] - y) < 0.01) & (np.abs(df_x0['Z'] - z) < 0.01)
            if mask.any():
                S_grid[i, j] = df_x0[mask]['Settlement_mm'].values[0]

    contour3 = ax3.contourf(Y_grid, Z_grid, S_grid, levels=15, cmap='RdYlBu_r')
    ax3.contour(Y_grid, Z_grid, S_grid, levels=8, colors='black', linewidths=0.5, alpha=0.3)

    plt.colorbar(contour3, ax=ax3, label='Asentamiento (mm)')

# Zapata
rect_zapata = plt.Rectangle((0, z_base_zapata), L_quarter, h,
                             facecolor='darkorange', edgecolor='black', linewidth=2,
                             label='Zapata', alpha=0.9)
ax3.add_patch(rect_zapata)

# Excavación
if Df > 0.01:
    rect_exc = plt.Rectangle((0, z_top_zapata), L_quarter, Df-h,
                              facecolor='lightgray', edgecolor='gray', linewidth=1.5,
                              label='Excavación', alpha=0.3, linestyle='--')
    ax3.add_patch(rect_exc)

# Estratos
ax3.axhline(y=-3, color='brown', linestyle='--', linewidth=1.5, alpha=0.5, label='Estrato 1-2')
ax3.axhline(y=-13, color='brown', linestyle='--', linewidth=1.5, alpha=0.5, label='Estrato 2-3')

ax3.set_xlabel('Y (m)', fontsize=11, fontweight='bold')
ax3.set_ylabel('Z - Profundidad (m)', fontsize=11, fontweight='bold')
ax3.set_title('Corte Vertical (X=0)\nPlano de Simetría', fontsize=13, fontweight='bold')
ax3.set_xlim(0, 9)
ax3.set_ylim(-20, 0.5)
ax3.legend(fontsize=9, loc='lower right')
ax3.grid(True, alpha=0.3)

# ============================================================================
# PERFIL VERTICAL EN CENTRO
# ============================================================================
ax4 = fig.add_subplot(2, 3, 4)

# Perfil vertical en el centro (x≈0, y≈0)
df_centro = df_3d[(df_3d['X'] < 0.1) & (df_3d['Y'] < 0.1)].copy()
df_centro = df_centro.sort_values('Z', ascending=False)

if len(df_centro) > 0:
    ax4.plot(df_centro['Settlement_mm'], df_centro['Z'],
             'b-o', linewidth=2.5, markersize=7, label='Perfil de asentamiento')
    ax4.axvline(x=df_centro['Settlement_mm'].max(), color='red', linestyle='--',
                linewidth=1.5, alpha=0.7, label=f'Máximo: {df_centro["Settlement_mm"].max():.2f} mm')

# Marcar zapata
ax4.axhspan(z_base_zapata, z_top_zapata, alpha=0.3, color='orange', label='Zapata')

if Df > 0.01:
    ax4.axhspan(z_top_zapata, 0, alpha=0.15, color='gray', label='Excavación')

# Estratos
ax4.axhspan(0, -3, alpha=0.1, color='brown')
ax4.axhspan(-3, -13, alpha=0.08, color='brown')
ax4.axhspan(-13, -20, alpha=0.06, color='brown')

ax4.text(1, -1.5, 'E=5 MPa', fontsize=9, color='brown')
ax4.text(1, -8, 'E=20 MPa', fontsize=9, color='brown')
ax4.text(1, -16.5, 'E=50 MPa', fontsize=9, color='brown')

ax4.set_xlabel('Asentamiento (mm)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Profundidad Z (m)', fontsize=11, fontweight='bold')
ax4.set_title('Perfil Vertical\nCentro de Zapata (X=0, Y=0)', fontsize=13, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)
ax4.invert_yaxis()

# ============================================================================
# SUPERFICIE 3D HUNDIDA
# ============================================================================
ax5 = fig.add_subplot(2, 3, 5, projection='3d')
ax5.set_facecolor('white')

# Superficie deformada (exagerada 10x para visualización)
scale = 10
z_deformed = -settlement_surf / 1000 * scale  # Convertir a metros y escalar

surf = ax5.plot_surface(x_surf, y_surf, z_deformed, facecolors=plt.cm.RdYlBu_r(settlement_surf/settlement_surf.max()),
                        alpha=0.9, edgecolor='none', shade=True)

# Contorno de zapata proyectado
zapata_contour = np.array([[0, 0, 0], [B_quarter, 0, 0],
                           [B_quarter, L_quarter, 0], [0, L_quarter, 0], [0, 0, 0]])
ax5.plot(zapata_contour[:, 0], zapata_contour[:, 1], zapata_contour[:, 2],
         'r-', linewidth=3, label='Límite zapata')

ax5.set_xlabel('X (m)', fontsize=11, fontweight='bold')
ax5.set_ylabel('Y (m)', fontsize=11, fontweight='bold')
ax5.set_zlabel(f'Deformación (×{scale})', fontsize=11, fontweight='bold')
ax5.set_title(f'Superficie Deformada\nEscala vertical {scale}x', fontsize=13, fontweight='bold')
ax5.view_init(elev=30, azim=-120)

# ============================================================================
# INFORMACIÓN DEL MODELO
# ============================================================================
ax6 = fig.add_subplot(2, 3, 6)
ax6.axis('off')

info_text = f"""
╔══════════════════════════════════════╗
║     MODELO DE ELEMENTOS FINITOS      ║
╚══════════════════════════════════════╝

📐 GEOMETRÍA:
   • Zapata: {B}m × {L}m × {h}m
   • Profundidad desplante: {Df} m
   • Dominio: 18m × 18m × 20m (completo)
   • Modelo: 1/4 con simetría

🔲 MALLA:
   • Tipo: Gradual adaptativa
   • Nodos: {len(df_3d)} puntos
   • Malla más fina cerca de zapata

🏗️ MATERIALES:
   • Zapata: E=250 GPa (concreto)
   • Suelo estratificado:
     - Estrato 1 (0-3m): E=5 MPa
     - Estrato 2 (3-13m): E=20 MPa
     - Estrato 3 (13-20m): E=50 MPa

⚡ CARGAS:
   • Total (modelo 1/4): 271 kN
   • Presión contacto: 125 kPa

📊 RESULTADOS:
   • Asent. máximo: {df_surface['Settlement_mm'].max():.2f} mm
   • Asent. mínimo: {df_surface['Settlement_mm'].min():.2f} mm
   • Asent. promedio: {df_surface['Settlement_mm'].mean():.2f} mm
   • Diferencial: {df_surface['Settlement_mm'].max() - df_surface['Settlement_mm'].min():.2f} mm

✅ CRITERIO:
   • Límite admisible: 25.0 mm
   • Estado: {'✓ OK' if df_surface['Settlement_mm'].max() < 25.0 else '⚠ REVISAR'}
"""

ax6.text(0.05, 0.95, info_text, transform=ax6.transAxes,
         fontsize=10, verticalalignment='top', family='monospace',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='black', linewidth=2))

# Título general
fig.suptitle(f'ANÁLISIS GEOTÉCNICO - FUNDACIÓN SUPERFICIAL\n'
             f'Zapata {B}m×{L}m con Df={Df}m - Modelo 3D Simplificado',
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Guardar
output_file = 'modelo_simplificado.png'
plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')
print(f"\n✓ Visualización guardada: {output_file}")
print(f"  Resolución: 200 DPI")
print(f"  Tamaño: 20×14 pulgadas\n")

plt.close()

print("="*80)
print("VISUALIZACIÓN SIMPLIFICADA COMPLETADA")
print("="*80)
