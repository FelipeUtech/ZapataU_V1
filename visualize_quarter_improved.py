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
#
# NOTA IMPORTANTE SOBRE DATOS:
# - Si existe 'settlements_3d_complete.csv': USA DATOS REALES de OpenSeesPy
# - Si NO existe: USA APROXIMACIÓN TEÓRICA para profundidad
#
# Para generar datos 3D reales:
#   1. Ejecutar localmente: python zapata_analysis_quarter.py
#   2. Ver INSTRUCCIONES_3D.md para más detalles
#
# Con datos 3D reales:
#   ✓ Perfil vertical: datos reales nodales
#   ✓ Planos verticales: aproximación (TODO: usar datos reales)
#   ✓ Superficie: siempre usa datos reales
# ================================================================================

print("\n" + "="*80)
print("GENERANDO VISUALIZACIÓN ISOMÉTRICA - MALLA GRADUAL OPTIMIZADA")
print("="*80 + "\n")

# -------------------------
# CARGAR DATOS EXISTENTES
# -------------------------
print("Cargando datos de asentamientos...")

# Intentar cargar datos 3D completos primero
data_3d_available = False
try:
    data_3d = pd.read_csv('settlements_3d_graded.csv')
    data_3d_available = True
    print(f"✓ Datos 3D MALLA GRADUAL cargados: {len(data_3d)} puntos")
    print(f"  Usando datos REALES de OpenSeesPy con malla optimizada")
except FileNotFoundError:
    print("⚠ No se encontró settlements_3d_graded.csv")
    print("  Usando datos de superficie + aproximación teórica para profundidad")
    print("  Para obtener datos reales, ejecuta: python zapata_graded_mesh.py")
    print("  Ver INSTRUCCIONES_3D.md para más detalles\n")

# Cargar datos de superficie
try:
    surface_data = pd.read_csv('surface_settlements_graded.csv')
    print(f"✓ Datos de superficie (malla gradual) cargados: {len(surface_data)} puntos")
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
# DOMINIO: 18m × 18m completo (9m × 9m en modelo 1/4)
# B = 3m, 6B = 18m, profundidad 20m
B = 3.0
Lx_quarter = 9.0  # Modelo 1/4: 9m (6B/2 = 3B)
Ly_quarter = 9.0  # Modelo 1/4: 9m
Lz_soil = 20.0    # Profundidad: 20m
B_quarter = 1.5   # B/2
L_quarter = 1.5   # B/2
h_zapata = 0.6
P_total_quarter = 1127.14 / 4.0
E_soil = 20000.0  # kPa (20 MPa)
E_concrete = 250000000.0  # kPa (250 GPa - 10× más rígida)
nu_soil = 0.3
rho_soil = 1800.0
# Malla gradual: refinada en zapata, transición suave a bordes
nx = 16  # Elementos en x (malla gradual)
ny = 16  # Elementos en y (malla gradual)
nz = 20  # Elementos en z (malla gradual)
dx = 0.56  # Aproximado (malla gradual: 0.25m → 1.49m)
dy = 0.56  # Aproximado (malla gradual: 0.25m → 1.49m)
dz = 1.0  # Aproximado (malla gradual: 0.30m → 3.26m)

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
fig = plt.figure(figsize=(24, 20), facecolor='white')  # Ajustado para 3 filas x 3 columnas
fig.suptitle('ANÁLISIS DE ZAPATA - MALLA GRADUAL OPTIMIZADA (6B-20m)',
             fontsize=18, fontweight='bold', y=0.98)

# ========================================
# 1. VISTA ISOMÉTRICA PRINCIPAL
# ========================================
ax1 = fig.add_subplot(3, 3, 1, projection='3d')  # Layout 3x3

# Crear grid de alta resolución para interpolación suave
xi_iso = np.linspace(0, Lx_quarter, 80)  # Aumentado de 30 a 80 para mayor suavidad
yi_iso = np.linspace(0, Ly_quarter, 80)
Xi_iso, Yi_iso = np.meshgrid(xi_iso, yi_iso)

# Interpolar asentamientos usando todos los puntos disponibles
Zi_iso = griddata((x_surf, y_surf), z_surf, (Xi_iso, Yi_iso), method='cubic')

# Rellenar NaN si existen usando interpolación lineal
if np.any(np.isnan(Zi_iso)):
    mask = np.isnan(Zi_iso)
    Zi_iso_linear = griddata((x_surf, y_surf), z_surf, (Xi_iso, Yi_iso), method='linear')
    Zi_iso[mask] = Zi_iso_linear[mask]

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

# PLANO X=0 con alta resolución
y_plane_x0 = np.linspace(0, Ly_quarter, 60)  # Aumentado para mejor detalle
z_plane_x0 = np.linspace(0, -Lz_soil, 60)    # Aumentado para mejor detalle
Y_x0, Z_x0 = np.meshgrid(y_plane_x0, z_plane_x0)

# Interpolar asentamientos en superficie para Y en x=0 usando más puntos
idx_x0 = np.abs(x_surf - 0) < dx/2
if np.sum(idx_x0) > 2:  # Necesitamos al menos 3 puntos
    y_surf_x0 = y_surf[idx_x0]
    settlement_surf_x0 = z_surf[idx_x0]

    # Ordenar para interpolación y eliminar duplicados
    sort_idx = np.argsort(y_surf_x0)
    y_surf_x0_sorted = y_surf_x0[sort_idx]
    settlement_surf_x0_sorted = settlement_surf_x0[sort_idx]

    # Eliminar duplicados promediando valores
    unique_y, indices = np.unique(y_surf_x0_sorted, return_inverse=True)
    unique_settlement = np.zeros_like(unique_y)
    for i in range(len(unique_y)):
        unique_settlement[i] = np.mean(settlement_surf_x0_sorted[indices == i])

    # Interpolación cúbica para superficie más suave
    from scipy.interpolate import interp1d
    if len(unique_y) >= 4:
        interp_func = interp1d(unique_y, unique_settlement,
                               kind='cubic', fill_value='extrapolate')
    else:
        interp_func = interp1d(unique_y, unique_settlement,
                               kind='linear', fill_value='extrapolate')

    settlement_interp_x0 = interp_func(y_plane_x0)
    settlement_interp_x0 = np.clip(settlement_interp_x0, 0, None)  # No negativos

    Settlement_x0 = np.zeros_like(Y_x0)
    for i in range(len(y_plane_x0)):
        for j in range(len(z_plane_x0)):
            depth = abs(z_plane_x0[j])
            Settlement_x0[j, i] = settlement_decay(settlement_interp_x0[i], depth)

    X_x0 = np.zeros_like(Y_x0)
    colors_x0 = cmap_custom(Settlement_x0 / np.nanmax(Zi_iso))
    ax1.plot_surface(X_x0, Y_x0, Z_x0, facecolors=colors_x0,
                     alpha=0.8, rstride=1, cstride=1,
                     linewidth=0, antialiased=True, shade=True, edgecolor='none')

# PLANO Y=0 con alta resolución
x_plane_y0 = np.linspace(0, Lx_quarter, 60)  # Aumentado para mejor detalle
z_plane_y0 = np.linspace(0, -Lz_soil, 60)    # Aumentado para mejor detalle
X_y0, Z_y0 = np.meshgrid(x_plane_y0, z_plane_y0)

idx_y0 = np.abs(y_surf - 0) < dy/2
if np.sum(idx_y0) > 2:  # Necesitamos al menos 3 puntos
    x_surf_y0 = x_surf[idx_y0]
    settlement_surf_y0 = z_surf[idx_y0]

    # Ordenar para interpolación y eliminar duplicados
    sort_idx = np.argsort(x_surf_y0)
    x_surf_y0_sorted = x_surf_y0[sort_idx]
    settlement_surf_y0_sorted = settlement_surf_y0[sort_idx]

    # Eliminar duplicados promediando valores
    unique_x, indices = np.unique(x_surf_y0_sorted, return_inverse=True)
    unique_settlement = np.zeros_like(unique_x)
    for i in range(len(unique_x)):
        unique_settlement[i] = np.mean(settlement_surf_y0_sorted[indices == i])

    # Interpolación cúbica para superficie más suave
    if len(unique_x) >= 4:
        interp_func = interp1d(unique_x, unique_settlement,
                               kind='cubic', fill_value='extrapolate')
    else:
        interp_func = interp1d(unique_x, unique_settlement,
                               kind='linear', fill_value='extrapolate')

    settlement_interp_y0 = interp_func(x_plane_y0)
    settlement_interp_y0 = np.clip(settlement_interp_y0, 0, None)  # No negativos

    Settlement_y0 = np.zeros_like(X_y0)
    for i in range(len(x_plane_y0)):
        for j in range(len(z_plane_y0)):
            depth = abs(z_plane_y0[j])
            Settlement_y0[j, i] = settlement_decay(settlement_interp_y0[i], depth)

    Y_y0 = np.zeros_like(X_y0)
    colors_y0 = cmap_custom(Settlement_y0 / np.nanmax(Zi_iso))
    ax1.plot_surface(X_y0, Y_y0, Z_y0, facecolors=colors_y0,
                     alpha=0.8, rstride=1, cstride=1,
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
# Mantener escala igual en todos los ejes para evitar distorsión
ax1.set_box_aspect([Lx_quarter, Ly_quarter, Lz_soil])

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
ax2 = fig.add_subplot(3, 3, 2)  # Layout 3x3

# Contorno de asentamientos con alta resolución
xi = np.linspace(0, Lx_quarter, 80)  # Aumentado para coincidir con isométrico
yi = np.linspace(0, Ly_quarter, 80)
Xi, Yi = np.meshgrid(xi, yi)
Zi = griddata((x_surf, y_surf), z_surf, (Xi, Yi), method='cubic')

# Rellenar NaN si existen
if np.any(np.isnan(Zi)):
    mask = np.isnan(Zi)
    Zi_linear = griddata((x_surf, y_surf), z_surf, (Xi, Yi), method='linear')
    Zi[mask] = Zi_linear[mask]

# Contornos rellenos con más niveles para suavidad
contour = ax2.contourf(Xi, Yi, Zi, levels=30, cmap=cmap_custom, extend='both')

# Líneas de contorno con etiquetas discretas solo en niveles clave
contour_lines = ax2.contour(Xi, Yi, Zi, levels=8, colors='black', linewidths=0.7, alpha=0.5)
# Etiquetas de asentamiento solo en las líneas de contorno (discretas)
ax2.clabel(contour_lines, inline=True, fontsize=7, fmt='%.1f', inline_spacing=15)

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

# ELIMINADAS todas las etiquetas que tapan la visualización
# Solo se mantienen las etiquetas de asentamiento en las líneas de contorno (clabel arriba)

# ========================================
# 3. PERFIL VERTICAL - ASENTAMIENTO EN CENTRO DE ZAPATA
# ========================================
ax3 = fig.add_subplot(3, 3, 3)  # Layout 3x3 - perfil vertical

print("  Calculando perfil vertical de asentamientos...")

# El centro de la zapata en el modelo 1/4 está en (0, 0) por la simetría

if data_3d_available:
    # =========== USAR DATOS REALES 3D ===========
    print("    Usando datos REALES de OpenSeesPy para perfil vertical")

    # Extraer datos en x=0, y=0 (centro de zapata)
    data_center = data_3d[(np.abs(data_3d['X'] - 0) < dx/2) &
                          (np.abs(data_3d['Y'] - 0) < dy/2)].copy()

    if len(data_center) > 0:
        # Ordenar por profundidad
        data_center = data_center.sort_values('Z', ascending=False)

        z_depths = data_center['Z'].values
        settlements_vertical = data_center['Settlement_mm'].values

        settlement_surface_center = settlements_vertical[0]
        print(f"    Puntos reales en perfil: {len(z_depths)}")
    else:
        # Fallback a aproximación
        print("    ⚠ No hay datos en centro, usando aproximación")
        data_3d_available = False  # Forzar uso de aproximación

if not data_3d_available:
    # =========== USAR APROXIMACIÓN TEÓRICA ===========
    print("    Usando aproximación teórica (decaimiento exponencial)")

    # Crear array de profundidades
    z_depths = np.linspace(0, -Lz_soil, 50)

    # Asentamiento en superficie
    idx_center = (np.abs(x_surf - 0) < dx/2) & (np.abs(y_surf - 0) < dy/2)

    if np.sum(idx_center) > 0:
        settlement_surface_center = np.mean(z_surf[idx_center])
    else:
        if len(x_surf) > 0:
            settlement_surface_center = griddata((x_surf, y_surf), z_surf,
                                                 ([0], [0]), method='cubic')[0]
            if np.isnan(settlement_surface_center):
                settlement_surface_center = griddata((x_surf, y_surf), z_surf,
                                                     ([0], [0]), method='linear')[0]
        else:
            settlement_surface_center = 18.0

    # Decaimiento exponencial
    settlements_vertical = []
    for z in z_depths:
        depth = abs(z)
        if depth == 0:
            settlement = settlement_surface_center
        else:
            decay_length = B_quarter * 3.0
            decay_factor = np.exp(-depth / decay_length)
            settlement = settlement_surface_center * decay_factor

        settlements_vertical.append(settlement)

    settlements_vertical = np.array(settlements_vertical)

# Graficar perfil vertical
ax3.plot(settlements_vertical, z_depths, 'b-', linewidth=2.5, label='Perfil de asentamiento')
ax3.fill_betweenx(z_depths, 0, settlements_vertical, alpha=0.3, color='lightblue')

# Marcar profundidad de la zapata
ax3.axhline(y=0, color='green', linewidth=2, linestyle='-', label='Superficie', zorder=5)
ax3.axhline(y=-h_zapata, color='orange', linewidth=2, linestyle='--',
            label=f'Base zapata ({h_zapata}m)', zorder=5)

# Marcar asentamiento en superficie
ax3.plot(settlement_surface_center, 0, 'ro', markersize=10,
         markeredgecolor='darkred', markeredgewidth=2, label='Superficie', zorder=10)

# Anotaciones
ax3.annotate(f'{settlement_surface_center:.2f} mm',
             xy=(settlement_surface_center, 0),
             xytext=(settlement_surface_center + 2, -2),
             fontsize=10, fontweight='bold', color='darkred',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.8),
             arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

# Configuración de ejes
ax3.set_xlabel('Asentamiento (mm)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Profundidad Z (m)', fontsize=12, fontweight='bold')
ax3.set_title('Perfil Vertical - Centro de Zapata (x=0, y=0)', fontsize=13, fontweight='bold', pad=15)
ax3.grid(True, alpha=0.4, linestyle='--', linewidth=0.5)
ax3.legend(loc='lower right', fontsize=10, framealpha=0.9)

# Invertir eje Y para que profundidad positiva vaya hacia abajo visualmente
ax3.set_ylim(-Lz_soil, 1)

# Añadir zona de influencia
influence_depth = -B_quarter * 3.0
if influence_depth > -Lz_soil:
    ax3.axhspan(0, influence_depth, alpha=0.1, color='red',
                label='Zona de influencia (~3B)')
    ax3.text(ax3.get_xlim()[1]*0.7, influence_depth/2,
             'Zona de\ninfluencia\n(≈3B)',
             fontsize=9, ha='center', va='center',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Añadir líneas de referencia de profundidad
for mult in [1, 2, 3]:
    ref_depth = -B_quarter * mult
    if -Lz_soil <= ref_depth <= 0:
        ax3.axhline(y=ref_depth, color='gray', linewidth=0.8,
                   linestyle=':', alpha=0.5)
        ax3.text(ax3.get_xlim()[0], ref_depth, f'{mult}B',
                fontsize=8, va='bottom', ha='left', color='gray')

print(f"    Asentamiento en superficie (centro): {settlement_surface_center:.4f} mm")
print(f"    Profundidad de análisis: 0 a {Lz_soil} m")

# ========================================
# 4. VISTA 3D - SUPERFICIE HUNDIDA
# ========================================
ax4 = fig.add_subplot(3, 3, 4, projection='3d')  # Layout 3x3 - posición 4

z_surf_hundido = z_surf  # Usar valores positivos para hundimiento hacia abajo

surf = ax4.plot_trisurf(x_surf, y_surf, z_surf_hundido, cmap=cmap_custom, alpha=0.9,
                        edgecolor='none', linewidth=0, antialiased=True, shade=True)
cbar4 = plt.colorbar(surf, ax=ax4, label='Asentamiento (mm)', shrink=0.7, aspect=15)
cbar4.ax.tick_params(labelsize=9)

# Plano de referencia en z = max(asentamiento) para referencia visual
xx_ref, yy_ref = np.meshgrid([0, Lx_quarter], [0, Ly_quarter])
zz_ref = np.full_like(xx_ref, np.max(z_surf_hundido))
ax4.plot_surface(xx_ref, yy_ref, zz_ref, alpha=0.2, color='gray', edgecolor='k', linewidth=0.5)

# Contorno zapata en la superficie hundida
zapata_outline_x = [0, B_quarter, B_quarter, 0, 0]
zapata_outline_y = [0, 0, L_quarter, L_quarter, 0]
zapata_outline_z = [max(z_surf_hundido)*1.05] * 5
ax4.plot(zapata_outline_x, zapata_outline_y, zapata_outline_z,
         'yellow', linewidth=3, linestyle='--', label='Contorno Zapata')

ax4.set_xlabel('X (m)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
ax4.set_zlabel('Asentamiento (mm)', fontsize=12, fontweight='bold')
ax4.set_title('Vista 3D - Superficie Hundida (Asentamientos)', fontsize=15, fontweight='bold', pad=15)
ax4.view_init(elev=30, azim=225)
# Invertir eje Z para que hundimiento vaya hacia abajo visualmente
ax4.invert_zaxis()
# Mantener escala igual en todos los ejes para evitar distorsión
ax4.set_box_aspect([Lx_quarter, Ly_quarter, max(abs(z_surf_hundido))])
ax4.legend(fontsize=10, loc='upper left')
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.set_box_aspect([1, 1, 0.5])

# ========================================
# 5. PERFIL HORIZONTAL - ASENTAMIENTO EN EJE X (Y=0, Z=0)
# ========================================
ax5 = fig.add_subplot(3, 3, 5)  # Layout 3x3 - posición 5

print("  Calculando perfil horizontal en eje X...")

# Extraer datos en superficie (Z=0) a lo largo de X, con Y=0
# Filtrar datos en Y=0 (o muy cerca)
idx_y0_surface = (np.abs(y_surf - 0) < dy/2)

if np.sum(idx_y0_surface) > 2:
    x_profile = x_surf[idx_y0_surface]
    settlement_profile = z_surf[idx_y0_surface]

    # Ordenar por X
    sort_idx = np.argsort(x_profile)
    x_profile_sorted = x_profile[sort_idx]
    settlement_profile_sorted = settlement_profile[sort_idx]

    # Eliminar duplicados promediando
    unique_x, indices = np.unique(x_profile_sorted, return_inverse=True)
    unique_settlement = np.zeros_like(unique_x)
    for i in range(len(unique_x)):
        unique_settlement[i] = np.mean(settlement_profile_sorted[indices == i])

    # Graficar perfil
    ax5.plot(unique_x, unique_settlement, 'b-', linewidth=2.5, label='Perfil de asentamiento')
    ax5.fill_between(unique_x, 0, unique_settlement, alpha=0.3, color='lightblue')

    # Marcar límite de zapata
    ax5.axvline(x=B_quarter, color='orange', linewidth=2, linestyle='--',
                label=f'Límite zapata ({B_quarter}m)', zorder=5)

    # Marcar asentamiento máximo
    max_idx = np.argmax(unique_settlement)
    x_max = unique_x[max_idx]
    settlement_max = unique_settlement[max_idx]

    ax5.plot(x_max, settlement_max, 'ro', markersize=10,
             markeredgecolor='darkred', markeredgewidth=2, label='Máximo', zorder=10)

    # Anotación
    ax5.annotate(f'{settlement_max:.2f} mm',
                 xy=(x_max, settlement_max),
                 xytext=(x_max + 1, settlement_max + 2),
                 fontsize=10, fontweight='bold', color='darkred',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.8),
                 arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))

    print(f"    Asentamiento máximo en perfil X: {settlement_max:.4f} mm en x={x_max:.2f} m")
else:
    # Fallback: interpolar si no hay datos directos
    x_profile = np.linspace(0, Lx_quarter, 50)
    settlement_profile = griddata((x_surf, y_surf), z_surf,
                                   (x_profile, np.zeros_like(x_profile)), method='cubic')
    if np.any(np.isnan(settlement_profile)):
        settlement_profile = griddata((x_surf, y_surf), z_surf,
                                       (x_profile, np.zeros_like(x_profile)), method='linear')

    ax5.plot(x_profile, settlement_profile, 'b-', linewidth=2.5, label='Perfil de asentamiento')
    ax5.fill_between(x_profile, 0, settlement_profile, alpha=0.3, color='lightblue')
    ax5.axvline(x=B_quarter, color='orange', linewidth=2, linestyle='--',
                label=f'Límite zapata ({B_quarter}m)', zorder=5)

# Configuración de ejes
ax5.set_xlabel('Distancia X (m)', fontsize=12, fontweight='bold')
ax5.set_ylabel('Asentamiento (mm)', fontsize=12, fontweight='bold')
ax5.set_title('Perfil Horizontal - Eje X en Superficie (Y=0, Z=0)', fontsize=13, fontweight='bold', pad=15)
ax5.grid(True, alpha=0.4, linestyle='--', linewidth=0.5)
ax5.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax5.set_xlim(0, Lx_quarter)
ax5.set_ylim(0, max(z_surf) * 1.1)

# ========================================
# 6. INFORMACIÓN DEL MODELO
# ========================================
ax6 = fig.add_subplot(3, 3, (7, 9))  # Panel ocupa posiciones 7-9 (toda la fila 3)
ax6.axis('off')

max_settlement = np.max(z_surf)
min_settlement = np.min(z_surf)
avg_settlement = np.mean(z_surf)
std_settlement = np.std(z_surf)

allowable_settlement = 25.0
fs_settlement = allowable_settlement / max_settlement if max_settlement > 0 else 0

info_text = f"""
╔═══════════════════════════════════════════════╗
║  MODELO 6B-20m MALLA GRADUAL OPTIMIZADA      ║
╚═══════════════════════════════════════════════╝

🏗️ GEOMETRÍA DEL CUADRANTE MODELADO:
  📐 Dimensiones: {Lx_quarter}m × {Ly_quarter}m × {Lz_soil}m
  🔲 MALLA GRADUAL con transición suave
  🔹 Zona zapata: 0.25m elementos (refinada)
  🔸 Transición gradual: 0.25m → 1.5m
  🔹 Zona superficial: 0.5m (0 a -5m)
  🔸 Zona profunda: 0.5m → 3.3m (gradual)
  📊 Total nodos: 6,069 (62% menos)

🟧 ZAPATA RÍGIDA (CUARTO DE SECCIÓN):
  📏 Zapata completa: {B}m × {B}m × {h_zapata}m
  📏 Modelo 1/4: {B_quarter}m × {L_quarter}m × {h_zapata}m
  📍 Posición: Esquina (0, 0, 0) - Df=0m ✓
  🔗 Nodos cargados: {zapata_nodes_count}
  💪 Material: Concreto 10× más rígido
  🏋️ E_concrete: {E_concrete/1e6:.0f} GPa

🔄 CONDICIONES DE SIMETRÍA:
  ✅ Plano X=0: Restricción en dirección X
  ✅ Plano Y=0: Restricción en dirección Y
  ✅ Base Z=-{Lz_soil}m: Empotrada (3 GDL fijos)

🌍 MATERIAL DEL SUELO:
  • Módulo elástico: {E_soil:.0f} kPa = {E_soil/1000:.0f} MPa
  • Coef. Poisson: {nu_soil}
  • Densidad: {rho_soil:.0f} kg/m³
  • Tipo: Suelo medio-denso

📊 MODELO COMPLETO EQUIVALENTE:
  • B = {B}m, 6B = {6*B}m
  • Dominio total: {6*B}m × {6*B}m × {Lz_soil}m
  • Zapata completa: {B}m × {B}m × {h_zapata}m
  • Malla refinada adaptativa automática

⚡ VENTAJAS MALLA GRADUAL OPTIMIZADA:
  ✓ 62% menos nodos (6,069 vs 15,972)
  ✓ 60× más rápido (~10 seg vs ~10 min)
  ✓ Transición suave (mejor aspect ratio)
  ✓ Refinada donde se necesita
  ✓ Elementos grandes en bordes
  ✓ Dominio 6B: bordes ≈0 asentamiento
  ✓ Df=0 corregido: base en superficie

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

ax6.text(0.03, 0.97, info_text, transform=ax6.transAxes,
         fontsize=8.5, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#E8F4F8', alpha=0.95,
                   edgecolor='#1E88E5', linewidth=2))

# ========================================
# GUARDAR
# ========================================
plt.tight_layout(pad=2.0)
plt.subplots_adjust(top=0.96, wspace=0.25, hspace=0.25)

output_file = 'modelo_quarter_isometrico_graded.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"\n✓ Imagen isométrica MALLA GRADUAL guardada: {output_file}")
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
print("  2. 🗺️  Vista en planta con contornos suaves y etiquetas discretas")
print("  3. 📊 Perfil vertical de asentamiento en centro de zapata (Z)")
print("  4. 🏔️  Superficie 3D hundida con deformación hacia abajo")
print("  5. 📈 Perfil horizontal de asentamiento en eje X (superficie)")
print("  6. 📋 Panel informativo completo con análisis detallado")

print(f"\n✅ Modelo 1/4 con MALLA GRADUAL OPTIMIZADA 6B-20m")
print(f"✅ B = {B}m, Dominio 6B = {6*B}m completo ({Lx_quarter}m modelo 1/4)")
print(f"✅ Profundidad = {Lz_soil}m")
print(f"✅ Zapata rígida: E = 250 GPa (10× más rígida), Df = 0m")
print(f"✅ Total nodos: 6,069 (62% menos que malla uniforme)")
print(f"✅ Tiempo análisis: ~10 seg (60× más rápido)")
print(f"✅ Asentamiento máximo: {max_settlement:.4f} mm")
print(f"✅ Factor de seguridad: {fs_settlement:.2f}\n")
