#!/usr/bin/env python3
"""
Visualización profesional con PyVista
Genera visualizaciones 3D de alta calidad del modelo de elementos finitos
"""

import pyvista as pv
import numpy as np
import pandas as pd
from config import ZAPATA, DOMINIO

print("="*80)
print("VISUALIZACIÓN PROFESIONAL CON PYVISTA")
print("="*80)
print()

# Configuración
pv.set_plot_theme("document")
pv.global_theme.font.size = 14
pv.global_theme.font.family = 'arial'

# Cargar configuración
zapata = ZAPATA
B = zapata['B']
L = zapata['L']
h = zapata['h']
Df = zapata['Df']

print(f"Cargando datos del modelo...")
print(f"  Zapata: {B}m × {L}m × {h}m")
print(f"  Profundidad desplante: {Df}m")
print()

# ============================================================================
# CARGAR DATOS DE ASENTAMIENTOS
# ============================================================================
print("Cargando asentamientos...")
df_3d = pd.read_csv('settlements_3d.csv')
df_surface = pd.read_csv('surface_settlements.csv')

print(f"✓ {len(df_3d)} puntos 3D cargados")
print(f"✓ {len(df_surface)} puntos de superficie")
print(f"  Asentamiento máximo: {df_surface['Settlement_mm'].max():.2f} mm")
print()

# ============================================================================
# CREAR MALLA 3D CON PYVISTA
# ============================================================================
print("Creando malla 3D...")

# Extraer coordenadas únicas
x_unique = sorted(df_3d['X'].unique())
y_unique = sorted(df_3d['Y'].unique())
z_unique = sorted(df_3d['Z'].unique())

nx, ny, nz = len(x_unique), len(y_unique), len(z_unique)
print(f"  Dimensiones: {nx} × {ny} × {nz} puntos")

# Crear grid estructurado
x_grid, y_grid, z_grid = np.meshgrid(x_unique, y_unique, z_unique, indexing='ij')

# Crear diccionario de asentamientos
settlement_dict = {}
for _, row in df_3d.iterrows():
    key = (round(row['X'], 4), round(row['Y'], 4), round(row['Z'], 4))
    settlement_dict[key] = row['Settlement_mm']

# Mapear asentamientos al grid
settlement_grid = np.zeros_like(x_grid, dtype=float)
for i in range(nx):
    for j in range(ny):
        for k in range(nz):
            key = (round(x_grid[i,j,k], 4), round(y_grid[i,j,k], 4), round(z_grid[i,j,k], 4))
            settlement_grid[i,j,k] = settlement_dict.get(key, 0.0)

# Crear malla estructurada de PyVista
grid = pv.StructuredGrid(x_grid, y_grid, z_grid)
grid['Asentamiento (mm)'] = settlement_grid.flatten(order='F')

print(f"✓ Malla creada: {grid.n_points} puntos, {grid.n_cells} celdas")
print()

# ============================================================================
# CREAR GEOMETRÍAS DE ZAPATA Y EXCAVACIÓN
# ============================================================================
print("Creando geometrías...")

# Zapata (modelo 1/4)
B_quarter = B / 2.0
L_quarter = L / 2.0
z_base = -Df
z_top = -Df + h

zapata_bounds = [0, B_quarter, 0, L_quarter, z_base, z_top]
zapata = pv.Box(bounds=zapata_bounds)
zapata['Material'] = np.ones(zapata.n_cells) * 2  # Código para zapata

# Excavación (si Df > 0)
if Df > 0.01:
    excavacion_bounds = [0, B_quarter, 0, L_quarter, z_top, 0]
    excavacion = pv.Box(bounds=excavacion_bounds)
    excavacion['Material'] = np.ones(excavacion.n_cells) * 3  # Código para excavación
else:
    excavacion = None

print(f"✓ Zapata: {B}m×{L}m×{h}m en z=[{z_base:.2f}, {z_top:.2f}]")
if excavacion:
    print(f"✓ Excavación: profundidad {Df}m")
print()

# ============================================================================
# VISUALIZACIÓN 1: Vista Isométrica con Asentamientos
# ============================================================================
print("1. Generando vista isométrica...")

plotter = pv.Plotter(off_screen=True, window_size=[1800, 1400])
plotter.set_background('white')

# Superficie del suelo con asentamientos
surface = grid.extract_cells_by_type(pv.CellType.HEXAHEDRON)
surface_top = surface.clip_box(bounds=[-100, 100, -100, 100, -0.1, 0.1], invert=False)

if surface_top.n_points > 0:
    plotter.add_mesh(
        surface_top,
        scalars='Asentamiento (mm)',
        cmap='RdYlBu_r',
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={
            'title': 'Asentamiento (mm)',
            'title_font_size': 16,
            'label_font_size': 12,
            'position_x': 0.85,
            'position_y': 0.15,
            'width': 0.12,
            'height': 0.7
        }
    )

# Zapata
plotter.add_mesh(
    zapata,
    color='orange',
    opacity=0.9,
    show_edges=True,
    edge_color='black',
    line_width=2,
    label='Zapata'
)

# Excavación (si existe)
if excavacion:
    plotter.add_mesh(
        excavacion,
        color='lightgray',
        opacity=0.3,
        show_edges=True,
        edge_color='gray',
        line_width=1,
        style='wireframe',
        label='Excavación'
    )

# Planos de simetría
x_plane = grid.slice(normal='x', origin=(0, 0, 0))
y_plane = grid.slice(normal='y', origin=(0, 0, 0))

plotter.add_mesh(
    x_plane,
    scalars='Asentamiento (mm)',
    cmap='RdYlBu_r',
    opacity=0.7,
    show_edges=False
)

plotter.add_mesh(
    y_plane,
    scalars='Asentamiento (mm)',
    cmap='RdYlBu_r',
    opacity=0.7,
    show_edges=False
)

# Configurar cámara y ejes
plotter.camera_position = [
    (15, 15, 10),  # Posición de la cámara
    (4.5, 4.5, -10),  # Punto de enfoque
    (0, 0, 1)  # Vector "arriba"
]

plotter.add_axes(
    xlabel='X (m)',
    ylabel='Y (m)',
    zlabel='Z (m)',
    line_width=3,
    color='black'
)

plotter.add_text(
    f'Modelo 3D - Zapata {B}m×{L}m, Df={Df}m\n'
    f'Asentamiento máx: {df_surface["settlement_mm"].max():.2f} mm',
    position='upper_edge',
    font_size=14,
    color='black',
    font='arial'
)

plotter.screenshot('modelo_pyvista_isometric.png', scale=2)
plotter.close()

print(f"✓ Guardado: modelo_pyvista_isometric.png")

# ============================================================================
# VISUALIZACIÓN 2: Vista en Planta (Superficie)
# ============================================================================
print("2. Generando vista en planta...")

plotter = pv.Plotter(off_screen=True, window_size=[1400, 1400])
plotter.set_background('white')

# Superficie con asentamientos
if surface_top.n_points > 0:
    plotter.add_mesh(
        surface_top,
        scalars='Asentamiento (mm)',
        cmap='RdYlBu_r',
        show_edges=True,
        edge_color='gray',
        line_width=0.5,
        scalar_bar_args={
            'title': 'Asentamiento (mm)',
            'title_font_size': 16,
            'label_font_size': 12,
            'position_x': 0.85,
            'position_y': 0.15,
            'width': 0.12,
            'height': 0.7
        }
    )

# Contorno de zapata en superficie
if Df > 0.01:
    # Mostrar el contorno de la excavación
    excavacion_top = excavacion.extract_surface()
    plotter.add_mesh(
        excavacion_top,
        color='black',
        style='wireframe',
        line_width=3,
        label='Excavación'
    )

# Vista desde arriba
plotter.view_xy()
plotter.camera.zoom(1.2)

plotter.add_text(
    f'Vista en Planta - Zapata {B}m×{L}m (1/4 modelo)\n'
    f'Df={Df}m, Asent. máx: {df_surface["settlement_mm"].max():.2f} mm',
    position='upper_edge',
    font_size=14,
    color='black'
)

plotter.screenshot('modelo_pyvista_planta.png', scale=2)
plotter.close()

print(f"✓ Guardado: modelo_pyvista_planta.png")

# ============================================================================
# VISUALIZACIÓN 3: Corte Vertical (Vista Lateral)
# ============================================================================
print("3. Generando corte vertical...")

plotter = pv.Plotter(off_screen=True, window_size=[2000, 1200])
plotter.set_background('white')

# Corte en Y=0 (plano de simetría)
slice_y = grid.slice(normal='y', origin=(0, 0, 0))

plotter.add_mesh(
    slice_y,
    scalars='Asentamiento (mm)',
    cmap='RdYlBu_r',
    show_edges=True,
    edge_color='black',
    line_width=0.3,
    scalar_bar_args={
        'title': 'Asentamiento (mm)',
        'title_font_size': 16,
        'label_font_size': 12,
        'position_x': 0.85,
        'position_y': 0.15,
        'width': 0.12,
        'height': 0.7
    }
)

# Zapata en el corte
zapata_slice = zapata.clip(normal='y', origin=(0, 0, 0))
plotter.add_mesh(
    zapata_slice,
    color='orange',
    opacity=0.9,
    show_edges=True,
    edge_color='black',
    line_width=2
)

# Excavación en el corte
if excavacion:
    excavacion_slice = excavacion.clip(normal='y', origin=(0, 0, 0))
    plotter.add_mesh(
        excavacion_slice,
        color='lightgray',
        opacity=0.3,
        show_edges=True,
        edge_color='gray',
        line_width=1.5
    )

# Vista lateral
plotter.view_xz()
plotter.camera.zoom(1.3)

plotter.add_text(
    f'Corte Vertical (Y=0) - Zapata {B}m×{L}m×{h}m\n'
    f'Df={Df}m, Profundidad análisis: {abs(z_unique[-1]):.1f}m',
    position='upper_edge',
    font_size=14,
    color='black'
)

plotter.screenshot('modelo_pyvista_corte.png', scale=2)
plotter.close()

print(f"✓ Guardado: modelo_pyvista_corte.png")

# ============================================================================
# VISUALIZACIÓN 4: Vista 3D Completa con Transparencias
# ============================================================================
print("4. Generando vista 3D completa...")

plotter = pv.Plotter(off_screen=True, window_size=[1800, 1400])
plotter.set_background('white')

# Suelo con asentamientos (semi-transparente)
suelo_exterior = grid.threshold([0.1, 100], scalars='Asentamiento (mm)')
if suelo_exterior.n_points > 0:
    plotter.add_mesh(
        suelo_exterior,
        scalars='Asentamiento (mm)',
        cmap='RdYlBu_r',
        opacity=0.4,
        show_edges=False,
        scalar_bar_args={
            'title': 'Asentamiento (mm)',
            'title_font_size': 16,
            'label_font_size': 12,
            'position_x': 0.85,
            'position_y': 0.15,
            'width': 0.12,
            'height': 0.7
        }
    )

# Zapata sólida
plotter.add_mesh(
    zapata,
    color='darkorange',
    opacity=1.0,
    show_edges=True,
    edge_color='black',
    line_width=2
)

# Excavación
if excavacion:
    plotter.add_mesh(
        excavacion,
        color='lightgray',
        opacity=0.2,
        show_edges=True,
        edge_color='darkgray',
        line_width=2,
        style='wireframe'
    )

# Planos de simetría
plotter.add_mesh(x_plane, scalars='Asentamiento (mm)', cmap='RdYlBu_r', opacity=0.6)
plotter.add_mesh(y_plane, scalars='Asentamiento (mm)', cmap='RdYlBu_r', opacity=0.6)

plotter.camera_position = [(20, 20, 15), (4.5, 4.5, -10), (0, 0, 1)]

plotter.add_axes(xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)', line_width=3)

plotter.add_text(
    f'Modelo 3D Completo - Zapata {B}m×{L}m, Df={Df}m\n'
    f'Vista con transparencias',
    position='upper_edge',
    font_size=14,
    color='black'
)

plotter.screenshot('modelo_pyvista_3d_completo.png', scale=2)
plotter.close()

print(f"✓ Guardado: modelo_pyvista_3d_completo.png")

# ============================================================================
# RESUMEN
# ============================================================================
print()
print("="*80)
print("VISUALIZACIÓN COMPLETADA")
print("="*80)
print()
print("Archivos generados:")
print("  • modelo_pyvista_isometric.png - Vista isométrica profesional")
print("  • modelo_pyvista_planta.png - Vista en planta con asentamientos")
print("  • modelo_pyvista_corte.png - Corte vertical mostrando estratificación")
print("  • modelo_pyvista_3d_completo.png - Vista 3D con transparencias")
print()
print(f"Modelo: {grid.n_points} puntos, {grid.n_cells} celdas")
print(f"Zapata: {B}m × {L}m × {h}m")
print(f"Profundidad desplante: {Df} m")
print(f"Asentamiento máximo: {df_surface['Settlement_mm'].max():.2f} mm")
print()
print("="*80)
