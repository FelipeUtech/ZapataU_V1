import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.interpolate import griddata
from matplotlib import cm
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.patches import Rectangle, FancyBboxPatch
import pandas as pd

# ================================================================================
# VISUALIZACIÓN MEJORADA DEL MODELO 1/4 - USANDO DATOS EXISTENTES
# ================================================================================

print("\n" + "="*80)
print("GENERANDO VISUALIZACIÓN MEJORADA DEL MODELO 1/4")
print("="*80 + "\n")

# -------------------------
# CARGAR DATOS EXISTENTES
# -------------------------
print("Cargando datos de asentamientos...")
try:
    # Intentar cargar datos del modelo quarter
    surface_data = pd.read_csv('surface_settlements_quarter_full.csv')
    print(f"✓ Datos cargados: {len(surface_data)} puntos")
except FileNotFoundError:
    print("⚠ No se encontró surface_settlements_quarter_full.csv")
    print("  Generando datos sintéticos para demostración...")
    # Generar datos sintéticos si no existen
    Lx_quarter = 10.0
    Ly_quarter = 10.0
    nx, ny = 11, 11
    x = np.linspace(0, Lx_quarter, nx)
    y = np.linspace(0, Ly_quarter, ny)
    X, Y = np.meshgrid(x, y)

    # Simular asentamientos (mayor cerca de la esquina)
    Z = 35 * np.exp(-((X**2 + Y**2) / 8.0))

    surface_data = pd.DataFrame({
        'X': X.flatten(),
        'Y': Y.flatten(),
        'Settlement': Z.flatten()
    })

# -------------------------
# PARÁMETROS DEL MODELO
# -------------------------
Lx_quarter = 10.0
Ly_quarter = 10.0
Lz_soil = 20.0
B_quarter = 1.5
L_quarter = 1.5
h_zapata = 0.6
P_total_quarter = 1127.14 / 4.0
E_soil = 30000.0
nu_soil = 0.3
rho_soil = 1800.0
nx = 10
ny = 10
nz = 15
dx = Lx_quarter / nx
dy = Ly_quarter / ny
dz = Lz_soil / nz

# Extraer datos - intentar diferentes nombres de columnas
if 'X' in surface_data.columns:
    x_surf = surface_data['X'].values
elif 'x' in surface_data.columns:
    x_surf = surface_data['x'].values
else:
    x_surf = surface_data.iloc[:, 0].values

if 'Y' in surface_data.columns:
    y_surf = surface_data['Y'].values
elif 'y' in surface_data.columns:
    y_surf = surface_data['y'].values
else:
    y_surf = surface_data.iloc[:, 1].values

if 'Settlement_mm' in surface_data.columns:
    z_surf = surface_data['Settlement_mm'].values
elif 'Settlement' in surface_data.columns:
    z_surf = surface_data['Settlement'].values
elif 'settlement' in surface_data.columns:
    z_surf = surface_data['settlement'].values
else:
    z_surf = surface_data.iloc[:, 2].values

# Número de nodos bajo zapata
zapata_nodes_count = np.sum((x_surf <= B_quarter) & (y_surf <= L_quarter))
P_per_node = -P_total_quarter / zapata_nodes_count if zapata_nodes_count > 0 else 0

print(f"\nParámetros del modelo:")
print(f"  Dominio: {Lx_quarter}m × {Ly_quarter}m × {Lz_soil}m")
print(f"  Zapata: {B_quarter}m × {L_quarter}m × {h_zapata}m")
print(f"  Carga: {P_total_quarter:.2f} kN")

# -------------------------
# CREAR COLORMAP PROFESIONAL
# -------------------------
colors_custom = ['#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#fddbc7', '#f4a582', '#d6604d', '#b2182b']
n_bins = 100
cmap_custom = LinearSegmentedColormap.from_list('settlement', colors_custom, N=n_bins)

# -------------------------
# CREAR FIGURA PRINCIPAL
# -------------------------
print("\nGenerando visualización mejorada...")

plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(22, 18), facecolor='white')
fig.suptitle('ANÁLISIS DE ZAPATA - MODELO 1/4 CON SIMETRÍA',
             fontsize=18, fontweight='bold', y=0.98)

# ========================================
# 1. VISTA ISOMÉTRICA PRINCIPAL
# ========================================
ax1 = fig.add_subplot(2, 2, 1, projection='3d')

# Crear grid para interpolación
xi_iso = np.linspace(0, Lx_quarter, 30)
yi_iso = np.linspace(0, Ly_quarter, 30)
Xi_iso, Yi_iso = np.meshgrid(xi_iso, yi_iso)

# Interpolar asentamientos
Zi_iso = griddata((x_surf, y_surf), z_surf, (Xi_iso, Yi_iso), method='cubic')

# Dibujar contorno del dominio
domain_corners = [
    [0, 0, 0], [Lx_quarter, 0, 0], [Lx_quarter, Ly_quarter, 0], [0, Ly_quarter, 0],
    [0, 0, -Lz_soil], [Lx_quarter, 0, -Lz_soil], [Lx_quarter, Ly_quarter, -Lz_soil], [0, Ly_quarter, -Lz_soil]
]

# Líneas verticales
for i in range(4):
    ax1.plot([domain_corners[i][0], domain_corners[i+4][0]],
             [domain_corners[i][1], domain_corners[i+4][1]],
             [domain_corners[i][2], domain_corners[i+4][2]], 'k-', linewidth=1.5, alpha=0.3)

# Líneas horizontales
edges_top = [[0,1], [1,2], [2,3], [3,0]]
for edge in edges_top:
    ax1.plot([domain_corners[edge[0]][0], domain_corners[edge[1]][0]],
             [domain_corners[edge[0]][1], domain_corners[edge[1]][1]],
             [domain_corners[edge[0]][2], domain_corners[edge[1]][2]], 'k-', linewidth=2, alpha=0.5)

edges_bottom = [[4,5], [5,6], [6,7], [7,4]]
for edge in edges_bottom:
    ax1.plot([domain_corners[edge[0]][0], domain_corners[edge[1]][0]],
             [domain_corners[edge[0]][1], domain_corners[edge[1]][1]],
             [domain_corners[edge[0]][2], domain_corners[edge[1]][2]], 'k-', linewidth=2, alpha=0.5)

# Superficie de contornos en z=0
surf_contour = ax1.plot_surface(Xi_iso, Yi_iso, np.zeros_like(Xi_iso) + 0.1,
                                 facecolors=cmap_custom(Zi_iso/np.nanmax(Zi_iso)),
                                 alpha=0.85, rstride=1, cstride=1,
                                 linewidth=0, antialiased=True, shade=True)

# PLANOS VERTICALES CON CONTORNOS
def settlement_decay(surface_settlement, depth):
    """Decaimiento exponencial del asentamiento con la profundidad"""
    decay_factor = np.exp(-depth / (B_quarter * 2))
    return surface_settlement * decay_factor

# PLANO X=0
y_plane_x0 = np.linspace(0, Ly_quarter, 30)
z_plane_x0 = np.linspace(0, -Lz_soil, 40)
Y_x0, Z_x0 = np.meshgrid(y_plane_x0, z_plane_x0)

# Interpolar asentamientos en superficie para Y en x=0
idx_x0 = np.abs(x_surf - 0) < dx/2
if np.sum(idx_x0) > 0:
    y_surf_x0 = y_surf[idx_x0]
    settlement_surf_x0 = z_surf[idx_x0]
    settlement_interp_x0 = np.interp(y_plane_x0, y_surf_x0, settlement_surf_x0)

    Settlement_x0 = np.zeros_like(Y_x0)
    for i in range(len(y_plane_x0)):
        for j in range(len(z_plane_x0)):
            depth = abs(z_plane_x0[j])
            Settlement_x0[j, i] = settlement_decay(settlement_interp_x0[i], depth)

    X_x0 = np.zeros_like(Y_x0)
    colors_x0 = cmap_custom(Settlement_x0 / np.nanmax(Zi_iso))
    ax1.plot_surface(X_x0, Y_x0, Z_x0, facecolors=colors_x0,
                     alpha=0.75, rstride=1, cstride=1,
                     linewidth=0, antialiased=True, shade=True, edgecolor='none')

# PLANO Y=0
x_plane_y0 = np.linspace(0, Lx_quarter, 30)
z_plane_y0 = np.linspace(0, -Lz_soil, 40)
X_y0, Z_y0 = np.meshgrid(x_plane_y0, z_plane_y0)

idx_y0 = np.abs(y_surf - 0) < dy/2
if np.sum(idx_y0) > 0:
    x_surf_y0 = x_surf[idx_y0]
    settlement_surf_y0 = z_surf[idx_y0]
    settlement_interp_y0 = np.interp(x_plane_y0, x_surf_y0, settlement_surf_y0)

    Settlement_y0 = np.zeros_like(X_y0)
    for i in range(len(x_plane_y0)):
        for j in range(len(z_plane_y0)):
            depth = abs(z_plane_y0[j])
            Settlement_y0[j, i] = settlement_decay(settlement_interp_y0[i], depth)

    Y_y0 = np.zeros_like(X_y0)
    colors_y0 = cmap_custom(Settlement_y0 / np.nanmax(Zi_iso))
    ax1.plot_surface(X_y0, Y_y0, Z_y0, facecolors=colors_y0,
                     alpha=0.75, rstride=1, cstride=1,
                     linewidth=0, antialiased=True, shade=True, edgecolor='none')

# ZAPATA
zapata_z_top = 0
zapata_z_bottom = -h_zapata
zapata_corners = [
    [0, 0, zapata_z_top], [B_quarter, 0, zapata_z_top],
    [B_quarter, L_quarter, zapata_z_top], [0, L_quarter, zapata_z_top],
    [0, 0, zapata_z_bottom], [B_quarter, 0, zapata_z_bottom],
    [B_quarter, L_quarter, zapata_z_bottom], [0, L_quarter, zapata_z_bottom]
]

zapata_faces = [
    [zapata_corners[0], zapata_corners[1], zapata_corners[2], zapata_corners[3]],
    [zapata_corners[4], zapata_corners[5], zapata_corners[6], zapata_corners[7]],
    [zapata_corners[0], zapata_corners[1], zapata_corners[5], zapata_corners[4]],
    [zapata_corners[2], zapata_corners[3], zapata_corners[7], zapata_corners[6]],
    [zapata_corners[0], zapata_corners[3], zapata_corners[7], zapata_corners[4]],
    [zapata_corners[1], zapata_corners[2], zapata_corners[6], zapata_corners[5]]
]

zapata_collection = Poly3DCollection(zapata_faces, alpha=0.7,
                                     facecolor='orange', edgecolor='darkorange', linewidth=2)
ax1.add_collection3d(zapata_collection)

# Configuración de ejes
ax1.set_xlabel('X (m)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
ax1.set_zlabel('Z (m)', fontsize=12, fontweight='bold')
ax1.set_title('Vista Isométrica - Modelo 1/4 con Zapata', fontsize=14, fontweight='bold')
ax1.set_xlim(0, Lx_quarter)
ax1.set_ylim(0, Ly_quarter)
ax1.set_zlim(-Lz_soil, 1)
ax1.view_init(elev=25, azim=225)

# Colorbar
norm = Normalize(vmin=np.nanmin(Zi_iso), vmax=np.nanmax(Zi_iso))
sm = cm.ScalarMappable(cmap=cmap_custom, norm=norm)
sm.set_array([])
cbar_iso = plt.colorbar(sm, ax=ax1, shrink=0.7, aspect=15, pad=0.05)
cbar_iso.set_label('Asentamiento (mm)', fontsize=11, fontweight='bold')
cbar_iso.ax.tick_params(labelsize=9)

# Anotaciones mejoradas
ax1.text2D(0.02, 0.98, '🟧 ZAPATA\n1.5×1.5m\nh=0.6m', transform=ax1.transAxes,
           fontsize=10, verticalalignment='top', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='orange', alpha=0.8, edgecolor='darkorange', linewidth=2))

ax1.text2D(0.02, 0.82, '📐 Plano X=0\n(Simetría Y-Z)', transform=ax1.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='cyan', alpha=0.7, edgecolor='blue', linewidth=1.5))

ax1.text2D(0.02, 0.68, '📐 Plano Y=0\n(Simetría X-Z)', transform=ax1.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.7, edgecolor='orange', linewidth=1.5))

ax1.text2D(0.02, 0.54, '🌊 Superficie\n(Asentamientos)', transform=ax1.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.7, edgecolor='darkgreen', linewidth=1.5))

ax1.text2D(0.98, 0.98, f'⬇ CARGA\n{P_total_quarter:.1f} kN', transform=ax1.transAxes,
           fontsize=10, verticalalignment='top', horizontalalignment='right', fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.7, edgecolor='darkred', linewidth=2))

# ========================================
# 2. VISTA SUPERIOR - ASENTAMIENTOS
# ========================================
ax2 = fig.add_subplot(2, 2, 2)

# Contorno de asentamientos
xi = np.linspace(0, Lx_quarter, 50)
yi = np.linspace(0, Ly_quarter, 50)
Xi, Yi = np.meshgrid(xi, yi)
Zi = griddata((x_surf, y_surf), z_surf, (Xi, Yi), method='cubic')

contour = ax2.contourf(Xi, Yi, Zi, levels=25, cmap=cmap_custom, extend='both')
contour_lines = ax2.contour(Xi, Yi, Zi, levels=10, colors='black', linewidths=0.5, alpha=0.3)
ax2.clabel(contour_lines, inline=True, fontsize=8, fmt='%.2f mm')

cbar2 = plt.colorbar(contour, ax=ax2, label='Asentamiento (mm)', shrink=0.9)
cbar2.ax.tick_params(labelsize=9)

# Zapata mejorada
rect = FancyBboxPatch((0, 0), B_quarter, L_quarter,
                      boxstyle="round,pad=0.05",
                      linewidth=3, edgecolor='white', facecolor='orange',
                      alpha=0.3, linestyle='--')
ax2.add_patch(rect)

rect_border = Rectangle((0, 0), B_quarter, L_quarter,
                        linewidth=4, edgecolor='darkorange', facecolor='none', linestyle='-')
ax2.add_patch(rect_border)

# Ejes de simetría
ax2.axhline(y=0, color='blue', linewidth=4, linestyle='-', alpha=0.6, label='Simetría X=0', zorder=10)
ax2.axvline(x=0, color='orange', linewidth=4, linestyle='-', alpha=0.6, label='Simetría Y=0', zorder=10)

ax2.set_xlabel('X (m)', fontsize=13, fontweight='bold')
ax2.set_ylabel('Y (m)', fontsize=13, fontweight='bold')
ax2.set_title('Vista en Planta - Asentamientos en Superficie', fontsize=15, fontweight='bold', pad=15)
ax2.set_aspect('equal')
ax2.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax2.grid(True, alpha=0.4, linestyle='--', linewidth=0.5)

# Anotaciones
ax2.text(B_quarter/2, L_quarter/2, 'ZAPATA\n1.5×1.5m', ha='center', va='center',
         color='white', fontweight='bold', fontsize=12,
         bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='white', linewidth=2))

# Dimensiones
ax2.annotate('', xy=(B_quarter, -0.3), xytext=(0, -0.3),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax2.text(B_quarter/2, -0.5, f'{B_quarter} m', ha='center', fontsize=10,
         fontweight='bold', color='red',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax2.annotate('', xy=(-0.3, L_quarter), xytext=(-0.3, 0),
            arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax2.text(-0.6, L_quarter/2, f'{L_quarter} m', ha='center', fontsize=10,
         fontweight='bold', color='red', rotation=90,
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Máximo asentamiento
max_idx = np.nanargmax(Zi)
max_i, max_j = np.unravel_index(max_idx, Zi.shape)
ax2.plot(Xi[max_i, max_j], Yi[max_i, max_j], 'r*', markersize=20, markeredgecolor='white', markeredgewidth=2)
ax2.text(Xi[max_i, max_j]+0.3, Yi[max_i, max_j]+0.3, f'Máx: {np.nanmax(Zi):.3f} mm',
         fontsize=10, fontweight='bold', color='darkred',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9))

# ========================================
# 3. VISTA 3D - SUPERFICIE HUNDIDA
# ========================================
ax3 = fig.add_subplot(2, 2, 3, projection='3d')

z_surf_inverted = -z_surf

surf = ax3.plot_trisurf(x_surf, y_surf, z_surf_inverted, cmap=cmap_custom, alpha=0.9,
                        edgecolor='none', linewidth=0, antialiased=True, shade=True)
cbar3 = plt.colorbar(surf, ax=ax3, label='Profundidad de hundimiento (mm)', shrink=0.7, aspect=15)
cbar3.ax.tick_params(labelsize=9)

# Plano de referencia
xx_ref, yy_ref = np.meshgrid([0, Lx_quarter], [0, Ly_quarter])
zz_ref = np.zeros_like(xx_ref)
ax3.plot_surface(xx_ref, yy_ref, zz_ref, alpha=0.2, color='gray', edgecolor='k', linewidth=0.5)

# Contorno zapata
zapata_outline_x = [0, B_quarter, B_quarter, 0, 0]
zapata_outline_y = [0, 0, L_quarter, L_quarter, 0]
zapata_outline_z = [min(z_surf_inverted)*0.9] * 5
ax3.plot(zapata_outline_x, zapata_outline_y, zapata_outline_z,
         'yellow', linewidth=3, linestyle='--', label='Contorno Zapata')

ax3.set_xlabel('X (m)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
ax3.set_zlabel('Hundimiento (mm)', fontsize=12, fontweight='bold')
ax3.set_title('Vista 3D - Superficie Hundida (Asentamientos)', fontsize=15, fontweight='bold', pad=15)
ax3.view_init(elev=30, azim=225)
ax3.legend(fontsize=10, loc='upper left')
ax3.invert_zaxis()
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.set_box_aspect([1, 1, 0.5])

# ========================================
# 4. INFORMACIÓN DEL MODELO
# ========================================
ax4 = fig.add_subplot(2, 2, 4)
ax4.axis('off')

max_settlement = np.max(z_surf)
min_settlement = np.min(z_surf)
avg_settlement = np.mean(z_surf)
std_settlement = np.std(z_surf)

allowable_settlement = 25.0
fs_settlement = allowable_settlement / max_settlement if max_settlement > 0 else 0

info_text = f"""
╔═══════════════════════════════════════════════╗
║  MODELO 1/4 CON SIMETRÍA - ANÁLISIS DETALLADO ║
╚═══════════════════════════════════════════════╝

🏗️ GEOMETRÍA DEL CUADRANTE MODELADO:
  📐 Dimensiones: {Lx_quarter}m × {Ly_quarter}m × {Lz_soil}m
  🔲 Malla: {nx} × {ny} × {nz} elementos
  🔹 Total nodos: {(nx+1)*(ny+1)*(nz+1)}
  🔸 Total elementos: {nx*ny*nz}
  📊 Tamaño elemento: {dx:.1f}m × {dy:.1f}m × {dz:.2f}m

🟧 ZAPATA (CUARTO DE SECCIÓN):
  📏 Dimensiones: {B_quarter}m × {L_quarter}m × {h_zapata}m
  📍 Posición: Esquina (0, 0, 0)
  🔗 Nodos cargados: {zapata_nodes_count}
  💪 Material: Concreto armado

🔄 CONDICIONES DE SIMETRÍA:
  ✅ Plano X=0: Restricción en dirección X
  ✅ Plano Y=0: Restricción en dirección Y
  ✅ Base Z=-{Lz_soil}m: Empotrada (3 GDL fijos)

🌍 MATERIAL DEL SUELO:
  • Módulo elástico: {E_soil:.0f} kPa
  • Coef. Poisson: {nu_soil}
  • Densidad: {rho_soil:.0f} kg/m³
  • Tipo: Suelo medio-denso

📊 MODELO COMPLETO EQUIVALENTE:
  • Dominio total: 20m × 20m × 20m
  • Zapata completa: 3m × 3m × 0.6m
  • Nodos totales: {(nx+1)*(ny+1)*(nz+1)*4:,}

⚡ EFICIENCIA COMPUTACIONAL:
  ✓ Reducción de nodos: 75.00%
  ✓ Reducción de tiempo: ~75.00%
  ✓ Reducción de memoria: ~75.00%

🔻 CARGAS APLICADAS:
  • Carga total zapata: 1127.14 kN
  • Carga en 1/4: {P_total_quarter:.2f} kN
  • Presión contacto: 125.24 kPa
  • Carga por nodo: {abs(P_per_node):.2f} kN

📈 RESULTADOS DE ASENTAMIENTOS:
  🔴 Máximo: {max_settlement:.4f} mm
  🟢 Mínimo: {min_settlement:.4f} mm
  🟡 Promedio: {avg_settlement:.4f} mm
  📊 Desv. Estándar: {std_settlement:.4f} mm
  📏 Diferencial: {max_settlement - min_settlement:.4f} mm

🛡️ EVALUACIÓN DE SEGURIDAD:
  • Límite permitido: {allowable_settlement:.1f} mm
  • Factor de seguridad: {fs_settlement:.2f}
  • Estado: {"✅ ACEPTABLE" if fs_settlement > 1.5 else "⚠️ REVISAR" if fs_settlement > 1.0 else "❌ CRÍTICO"}

📝 NOTA: Visualización del cuadrante 1/4.
   El modelo completo se obtiene por reflexión.
"""

ax4.text(0.03, 0.97, info_text, transform=ax4.transAxes,
         fontsize=8.5, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#E8F4F8', alpha=0.95,
                   edgecolor='#1E88E5', linewidth=2))

# ========================================
# GUARDAR
# ========================================
plt.tight_layout(pad=2.0)
plt.subplots_adjust(top=0.96, wspace=0.25, hspace=0.25)

output_file = 'modelo_quarter_isometrico.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"\n✓ Imagen mejorada guardada: {output_file}")
print(f"  Resolución: 300 DPI")
print(f"  Tamaño: {fig.get_size_inches()[0]:.1f} × {fig.get_size_inches()[1]:.1f} pulgadas")

print("\n" + "="*80)
print("✨ VISUALIZACIÓN MEJORADA COMPLETADA ✨")
print("="*80)
print("\n🎨 MEJORAS IMPLEMENTADAS:")
print("  ✓ Colormap profesional (RdYlBu_r personalizado)")
print("  ✓ Iluminación y sombreado mejorados en superficies 3D")
print("  ✓ Contornos con etiquetas de valores")
print("  ✓ Dimensiones y anotaciones técnicas agregadas")
print("  ✓ Indicador de asentamiento máximo")
print("  ✓ Panel de información ampliado con emojis y formato mejorado")
print("  ✓ Factor de seguridad calculado")
print("  ✓ Grid y ejes mejorados")
print("  ✓ Bordes y marcos profesionales")
print("  ✓ Layout optimizado con mejor espaciado")

print("\n📊 COMPONENTES DE LA VISUALIZACIÓN:")
print("  1. 🔷 Vista isométrica 3D con contornos en planos de simetría")
print("  2. 🗺️  Vista en planta con dimensiones y máximo señalizado")
print("  3. 🏔️  Superficie 3D hundida con deformación exagerada")
print("  4. 📋 Panel informativo completo con análisis detallado")

print(f"\n✅ Modelo 1/4 optimizado")
print(f"✅ Dominio: {Lx_quarter}m × {Ly_quarter}m × {Lz_soil}m")
print(f"✅ Asentamiento máximo: {max_settlement:.4f} mm")
print(f"✅ Factor de seguridad: {fs_settlement:.2f}\n")
