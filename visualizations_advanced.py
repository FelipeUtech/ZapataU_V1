#!/usr/bin/env python3
"""
===================================================================================
VISUALIZACIONES AVANZADAS - ANÁLISIS DE ZAPATAS
===================================================================================
Este módulo proporciona visualizaciones profesionales adicionales:

GRÁFICAS INCLUIDAS:
  1. Mapa de contornos 2D con isolíneas
  2. Vista 3D de superficie de asentamientos
  3. Perfil de asentamientos en secciones
  4. Distribución de presiones
  5. Comparación múltiples resultados
  6. Dashboard completo con múltiples vistas

USO:
    python visualizations_advanced.py --input settlements_3d.csv
===================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.patches import Rectangle
import sys
import argparse

# ===================================================================================
# FUNCIONES DE VISUALIZACIÓN AVANZADAS
# ===================================================================================

def plot_contour_map_advanced(df_surface, zapata_info, archivo='settlements_contour_advanced.png'):
    """
    Mapa de contornos mejorado con isolíneas y anotaciones.

    Parameters:
    -----------
    df_surface : pd.DataFrame
        DataFrame con asentamientos en superficie (X, Y, Settlement_mm)
    zapata_info : dict
        {'B': float, 'L': float, 'x_min': float, 'y_min': float}
    archivo : str
        Nombre del archivo de salida
    """
    fig, ax = plt.subplots(figsize=(12, 10))

    # Extraer datos
    x = df_surface['X'].values
    y = df_surface['Y'].values
    z = df_surface['Settlement_mm'].values

    # Crear grid regular para interpolación
    xi = np.linspace(x.min(), x.max(), 200)
    yi = np.linspace(y.min(), y.max(), 200)
    Xi, Yi = np.meshgrid(xi, yi)

    # Interpolar
    from scipy.interpolate import griddata
    Zi = griddata((x, y), z, (Xi, Yi), method='cubic')

    # Contornos rellenos
    levels = np.linspace(z.min(), z.max(), 20)
    contourf = ax.contourf(Xi, Yi, Zi, levels=levels, cmap='jet', alpha=0.8)

    # Isolíneas
    contour = ax.contour(Xi, Yi, Zi, levels=10, colors='black', linewidths=0.5, alpha=0.5)
    ax.clabel(contour, inline=True, fontsize=8, fmt='%.1f mm')

    # Barra de color
    cbar = plt.colorbar(contourf, ax=ax, label='Asentamiento (mm)')
    cbar.ax.tick_params(labelsize=10)

    # Dibujar zapata
    B = zapata_info['B']
    L = zapata_info['L']
    x_min = zapata_info.get('x_min', 0.0)
    y_min = zapata_info.get('y_min', 0.0)

    rect = Rectangle((x_min, y_min), B, L, fill=False, edgecolor='red',
                     linewidth=3, linestyle='--', label='Zapata')
    ax.add_patch(rect)

    # Marcar puntos de interés
    idx_max = z.argmax()
    ax.plot(x[idx_max], y[idx_max], 'r*', markersize=20, label=f'Máx: {z.max():.2f} mm')

    idx_min = z.argmin()
    ax.plot(x[idx_min], y[idx_min], 'b*', markersize=20, label=f'Mín: {z.min():.2f} mm')

    # Configuración
    ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
    ax.set_title('Mapa de Asentamientos en Superficie - Vista Detallada',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo}")
    plt.close()


def plot_3d_surface(df_surface, zapata_info, archivo='settlements_3d_surface.png'):
    """
    Superficie 3D de asentamientos.

    Parameters:
    -----------
    df_surface : pd.DataFrame
        DataFrame con asentamientos en superficie
    zapata_info : dict
        Información de la zapata
    archivo : str
        Nombre del archivo de salida
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Extraer datos
    x = df_surface['X'].values
    y = df_surface['Y'].values
    z = df_surface['Settlement_mm'].values

    # Crear grid
    xi = np.linspace(x.min(), x.max(), 100)
    yi = np.linspace(y.min(), y.max(), 100)
    Xi, Yi = np.meshgrid(xi, yi)

    from scipy.interpolate import griddata
    Zi = griddata((x, y), z, (Xi, Yi), method='cubic')

    # Superficie
    surf = ax.plot_surface(Xi, Yi, Zi, cmap='jet', alpha=0.8,
                          linewidth=0, antialiased=True, shade=True)

    # Contornos proyectados en la base
    ax.contour(Xi, Yi, Zi, zdir='z', offset=z.min()-2, cmap='coolwarm', alpha=0.5)

    # Barra de color
    cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
    cbar.set_label('Asentamiento (mm)', fontsize=11)

    # Configuración
    ax.set_xlabel('X (m)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=11, fontweight='bold')
    ax.set_zlabel('Asentamiento (mm)', fontsize=11, fontweight='bold')
    ax.set_title('Superficie 3D de Asentamientos', fontsize=14, fontweight='bold', pad=20)

    # Vista
    ax.view_init(elev=25, azim=45)

    plt.tight_layout()
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo}")
    plt.close()


def plot_settlement_profiles(df_surface, zapata_info, archivo='settlement_profiles.png'):
    """
    Perfiles de asentamientos en secciones X e Y.

    Parameters:
    -----------
    df_surface : pd.DataFrame
        DataFrame con asentamientos en superficie
    zapata_info : dict
        Información de la zapata
    archivo : str
        Nombre del archivo de salida
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    B = zapata_info['B']
    L = zapata_info['L']

    # PERFIL EN X (a través del centro de la zapata)
    y_center = L / 2.0
    tolerance = 0.1  # Tolerancia para seleccionar puntos cercanos

    df_x_profile = df_surface[np.abs(df_surface['Y'] - y_center) < tolerance].sort_values('X')

    if len(df_x_profile) > 0:
        ax1.plot(df_x_profile['X'], df_x_profile['Settlement_mm'],
                'o-', linewidth=2, markersize=6, color='blue', label='Perfil X')

        # Marcar zona de zapata
        ax1.axvspan(0, B, alpha=0.2, color='red', label='Zona de zapata')

        ax1.set_xlabel('X (m)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Asentamiento (mm)', fontsize=11, fontweight='bold')
        ax1.set_title(f'Perfil de Asentamientos en X (Y={y_center:.2f}m)',
                     fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.invert_yaxis()  # Asentamiento positivo hacia abajo

    # PERFIL EN Y (a través del centro de la zapata)
    x_center = B / 2.0

    df_y_profile = df_surface[np.abs(df_surface['X'] - x_center) < tolerance].sort_values('Y')

    if len(df_y_profile) > 0:
        ax2.plot(df_y_profile['Y'], df_y_profile['Settlement_mm'],
                'o-', linewidth=2, markersize=6, color='green', label='Perfil Y')

        # Marcar zona de zapata
        ax2.axvspan(0, L, alpha=0.2, color='red', label='Zona de zapata')

        ax2.set_xlabel('Y (m)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Asentamiento (mm)', fontsize=11, fontweight='bold')
        ax2.set_title(f'Perfil de Asentamientos en Y (X={x_center:.2f}m)',
                     fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.invert_yaxis()

    plt.tight_layout()
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo}")
    plt.close()


def plot_depth_profile(df_3d, x_point, y_point, archivo='depth_profile.png'):
    """
    Perfil de asentamientos con la profundidad en un punto específico.

    Parameters:
    -----------
    df_3d : pd.DataFrame
        DataFrame completo 3D
    x_point : float
        Coordenada X del punto
    y_point : float
        Coordenada Y del punto
    archivo : str
        Nombre del archivo de salida
    """
    tolerance = 0.2

    # Seleccionar puntos cercanos
    df_point = df_3d[
        (np.abs(df_3d['X'] - x_point) < tolerance) &
        (np.abs(df_3d['Y'] - y_point) < tolerance)
    ].sort_values('Z', ascending=False)

    if len(df_point) == 0:
        print(f"⚠️  No se encontraron datos en punto ({x_point}, {y_point})")
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(df_point['Settlement_mm'], df_point['Z'],
           'o-', linewidth=2, markersize=8, color='purple')

    ax.set_xlabel('Asentamiento (mm)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Profundidad Z (m)', fontsize=11, fontweight='bold')
    ax.set_title(f'Perfil de Asentamientos con Profundidad\nPunto ({x_point:.2f}, {y_point:.2f})',
                fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Superficie')
    ax.legend()

    plt.tight_layout()
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo}")
    plt.close()


def plot_dashboard(df_surface, df_3d, zapata_info, archivo='dashboard_completo.png'):
    """
    Dashboard completo con múltiples visualizaciones.

    Parameters:
    -----------
    df_surface : pd.DataFrame
        DataFrame con asentamientos en superficie
    df_3d : pd.DataFrame
        DataFrame 3D completo
    zapata_info : dict
        Información de la zapata
    archivo : str
        Nombre del archivo de salida
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # 1. Mapa de contornos (principal, grande)
    ax1 = fig.add_subplot(gs[0:2, 0:2])

    x = df_surface['X'].values
    y = df_surface['Y'].values
    z = df_surface['Settlement_mm'].values

    scatter = ax1.tricontourf(x, y, z, levels=15, cmap='jet')
    plt.colorbar(scatter, ax=ax1, label='Asentamiento (mm)')

    B = zapata_info['B']
    L = zapata_info['L']
    x_min = zapata_info.get('x_min', 0.0)
    y_min = zapata_info.get('y_min', 0.0)

    rect = Rectangle((x_min, y_min), B, L, fill=False, edgecolor='red',
                     linewidth=2, linestyle='--')
    ax1.add_patch(rect)

    ax1.set_xlabel('X (m)', fontweight='bold')
    ax1.set_ylabel('Y (m)', fontweight='bold')
    ax1.set_title('Mapa de Asentamientos', fontweight='bold', fontsize=12)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)

    # 2. Histograma de asentamientos
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.hist(z, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Asentamiento (mm)', fontsize=9)
    ax2.set_ylabel('Frecuencia', fontsize=9)
    ax2.set_title('Distribución de Asentamientos', fontweight='bold', fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')

    # 3. Estadísticas
    ax3 = fig.add_subplot(gs[1, 2])
    ax3.axis('off')

    stats_text = f"""
    ESTADÍSTICAS

    Máximo: {z.max():.2f} mm
    Mínimo: {z.min():.2f} mm
    Promedio: {z.mean():.2f} mm
    Mediana: {np.median(z):.2f} mm
    Desv. Est.: {z.std():.2f} mm
    Diferencial: {z.max() - z.min():.2f} mm

    Puntos: {len(z)}
    """

    ax3.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 4. Perfil X
    ax4 = fig.add_subplot(gs[2, 0])
    y_center = L / 2.0
    df_x = df_surface[np.abs(df_surface['Y'] - y_center) < 0.1].sort_values('X')
    if len(df_x) > 0:
        ax4.plot(df_x['X'], df_x['Settlement_mm'], 'o-', linewidth=2, color='blue')
        ax4.axvspan(0, B, alpha=0.2, color='red')
        ax4.set_xlabel('X (m)', fontsize=9)
        ax4.set_ylabel('Asentamiento (mm)', fontsize=9)
        ax4.set_title('Perfil en X', fontweight='bold', fontsize=10)
        ax4.grid(True, alpha=0.3)
        ax4.invert_yaxis()

    # 5. Perfil Y
    ax5 = fig.add_subplot(gs[2, 1])
    x_center = B / 2.0
    df_y = df_surface[np.abs(df_surface['X'] - x_center) < 0.1].sort_values('Y')
    if len(df_y) > 0:
        ax5.plot(df_y['Y'], df_y['Settlement_mm'], 'o-', linewidth=2, color='green')
        ax5.axvspan(0, L, alpha=0.2, color='red')
        ax5.set_xlabel('Y (m)', fontsize=9)
        ax5.set_ylabel('Asentamiento (mm)', fontsize=9)
        ax5.set_title('Perfil en Y', fontweight='bold', fontsize=10)
        ax5.grid(True, alpha=0.3)
        ax5.invert_yaxis()

    # 6. Información del modelo
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')

    info_text = f"""
    MODELO

    Zapata: {B:.1f}m × {L:.1f}m

    Puntos 3D: {len(df_3d)}
    Puntos superficie: {len(df_surface)}

    Rango X: {x.min():.1f} - {x.max():.1f} m
    Rango Y: {y.min():.1f} - {y.max():.1f} m
    """

    ax6.text(0.1, 0.5, info_text, fontsize=9, verticalalignment='center',
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    fig.suptitle('DASHBOARD COMPLETO - ANÁLISIS DE ASENTAMIENTOS',
                fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Dashboard guardado: {archivo}")
    plt.close()


# ===================================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================================

def main():
    """Función principal."""

    parser = argparse.ArgumentParser(description='Visualizaciones avanzadas de asentamientos')
    parser.add_argument('--input', type=str, default='settlements_3d.csv',
                       help='Archivo CSV con resultados 3D')
    parser.add_argument('--surface', type=str, default='surface_settlements.csv',
                       help='Archivo CSV con resultados de superficie')
    parser.add_argument('--all', action='store_true',
                       help='Generar todas las visualizaciones')

    args = parser.parse_args()

    print("\n" + "="*80)
    print("VISUALIZACIONES AVANZADAS")
    print("="*80 + "\n")

    # Leer datos
    try:
        df_3d = pd.read_csv(args.input)
        print(f"✓ Datos 3D cargados: {args.input} ({len(df_3d)} puntos)")
    except FileNotFoundError:
        print(f"❌ Error: Archivo '{args.input}' no encontrado")
        print("   Ejecuta primero: python run_analysis.py")
        sys.exit(1)

    # Superficie
    try:
        df_surface = pd.read_csv(args.surface)
        print(f"✓ Datos superficie cargados: {args.surface} ({len(df_surface)} puntos)")
    except:
        # Si no existe, extraer de 3D
        z_max = df_3d['Z'].max()
        df_surface = df_3d[df_3d['Z'] == z_max].copy()
        print(f"✓ Superficie extraída de datos 3D ({len(df_surface)} puntos)")

    # Información de zapata (estimada)
    x_vals = df_surface['X'].values
    y_vals = df_surface['Y'].values

    # Encontrar área con asentamiento > umbral
    umbral = df_surface['Settlement_mm'].mean()
    df_zapata_area = df_surface[df_surface['Settlement_mm'] > umbral]

    if len(df_zapata_area) > 0:
        B_est = df_zapata_area['X'].max() * 2  # Estimación asumiendo simetría
        L_est = df_zapata_area['Y'].max() * 2
    else:
        B_est = x_vals.max() * 0.2
        L_est = y_vals.max() * 0.2

    zapata_info = {'B': B_est, 'L': L_est, 'x_min': 0.0, 'y_min': 0.0}

    print(f"\nEstimación de zapata: {B_est:.2f}m × {L_est:.2f}m\n")

    # Generar visualizaciones
    print("Generando visualizaciones...\n")

    # Importar scipy para interpolación
    try:
        import scipy
    except ImportError:
        print("⚠️  Advertencia: scipy no instalado. Algunas gráficas pueden no generarse.")
        print("   Instala con: pip install scipy\n")

    plot_contour_map_advanced(df_surface, zapata_info)
    plot_settlement_profiles(df_surface, zapata_info)
    plot_dashboard(df_surface, df_3d, zapata_info)

    # Gráficas adicionales si se solicitan todas
    if args.all:
        try:
            plot_3d_surface(df_surface, zapata_info)
            plot_depth_profile(df_3d, B_est/4, L_est/4)
        except Exception as e:
            print(f"⚠️  Algunas visualizaciones no pudieron generarse: {e}")

    print("\n" + "="*80)
    print("VISUALIZACIONES COMPLETADAS")
    print("="*80 + "\n")


# ===================================================================================
# EJECUTAR
# ===================================================================================

if __name__ == "__main__":
    main()
