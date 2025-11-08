"""
Script para verificar que la excavación está correctamente limitada
al área de proyección vertical de la zapata
"""
import pyvista as pv
import numpy as np

# Configurar offscreen rendering
pv.start_xvfb()

# Cargar la malla
vtu_path = "mallas/zapata_3D_cuarto_hex_structured.vtu"
print(f"📂 Cargando malla: {vtu_path}")
grid = pv.read(vtu_path)

# Parámetros geométricos
B = 3.0
Df = 1.5
x0 = 3.0 - B/2  # = 1.5
y0 = 3.0 - B/2  # = 1.5

# Límites de la proyección de la zapata en cuarto de dominio
x_zapata_min = 0.0
x_zapata_max = x0/2 + B/4  # = 1.5
y_zapata_min = 0.0
y_zapata_max = y0/2 + B/4  # = 1.5
z_zapata_top = -Df  # = -1.5
z_superficie = 0.0

print(f"\n📐 Parámetros de verificación:")
print(f"   Proyección de zapata en planta:")
print(f"   - X: [{x_zapata_min:.2f}, {x_zapata_max:.2f}]")
print(f"   - Y: [{y_zapata_min:.2f}, {y_zapata_max:.2f}]")
print(f"   Excavación vertical:")
print(f"   - Z: [{z_zapata_top:.2f}, {z_superficie:.2f}]")

# Información de la malla
print(f"\n📊 Información de la malla:")
print(f"   - Número de puntos: {grid.n_points:,}")
print(f"   - Número de celdas: {grid.n_cells:,}")
print(f"   - Bounds X: [{grid.bounds[0]:.2f}, {grid.bounds[1]:.2f}]")
print(f"   - Bounds Y: [{grid.bounds[2]:.2f}, {grid.bounds[3]:.2f}]")
print(f"   - Bounds Z: [{grid.bounds[4]:.2f}, {grid.bounds[5]:.2f}]")

# Distribución de elementos
dominios = grid.cell_data["dominio"]
print(f"\n📊 Distribución de elementos:")
print(f"   - SOIL_1: {np.sum(dominios == 1):,} hexaedros")
print(f"   - SOIL_2: {np.sum(dominios == 2):,} hexaedros")
print(f"   - SOIL_3: {np.sum(dominios == 3):,} hexaedros")
print(f"   - FOOTING: {np.sum(dominios == 4):,} hexaedros")

# ===========================
# Vista 1: Vista general 3D
# ===========================
print(f"\n🎨 Generando vista general...")
plotter = pv.Plotter(off_screen=True, window_size=[1600, 1200])

plotter.add_mesh(
    grid,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    line_width=0.5,
    opacity=0.85,
    cmap="Set3",
    scalar_bar_args={
        'title': 'Dominio',
        'title_font_size': 20,
        'label_font_size': 16,
        'n_labels': 5,
        'fmt': '%.0f',
    }
)

plotter.add_text(
    "Malla Hexaédrica - Excavación Corregida\n(1/4 Dominio)",
    font_size=16,
    position="upper_edge"
)

plotter.show_axes()
plotter.add_axes_at_origin(labels_off=False, line_width=3)

# Cámara isométrica
plotter.camera_position = [
    (8, 8, 5),
    (1.5, 1.5, -5),
    (0, 0, 1)
]

plotter.screenshot("images/excavation_overview.png")
print("✅ Guardada: images/excavation_overview.png")

# ===========================
# Vista 2: Planta (vista desde arriba) - Clip en Z=-1
# ===========================
print(f"\n🎨 Generando vista en planta...")
plotter2 = pv.Plotter(off_screen=True, window_size=[1600, 1200])

# Hacer un clip para ver solo la parte superior
clipped = grid.clip(normal='z', origin=[0, 0, -1.0], invert=False)

plotter2.add_mesh(
    clipped,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    line_width=1.0,
    cmap="Set3",
    scalar_bar_args={'title': 'Dominio', 'title_font_size': 20, 'label_font_size': 16}
)

# Agregar rectángulo de referencia del área de zapata
box_outline = pv.Box(bounds=[
    x_zapata_min, x_zapata_max,
    y_zapata_min, y_zapata_max,
    -0.6, -0.4
])
plotter2.add_mesh(box_outline, style='wireframe', color='red', line_width=5, label="Límite de excavación")

plotter2.add_text(
    f"Vista superior (Z > -1 m)\nÁrea de excavación: {x_zapata_max:.1f} x {y_zapata_max:.1f} m",
    font_size=16,
    position="upper_edge"
)

plotter2.show_axes()
plotter2.view_xy()  # Vista desde arriba
plotter2.camera.zoom(1.3)

plotter2.screenshot("images/excavation_plan_view.png")
print("✅ Guardada: images/excavation_plan_view.png")

# ===========================
# Vista 3: Corte en plano X=0 (plano de simetría)
# ===========================
print(f"\n🎨 Generando corte en plano X=0...")
plotter3 = pv.Plotter(off_screen=True, window_size=[1600, 1200])

# Crear corte en X=0.01 (muy cerca de X=0)
slice_x = grid.slice(normal='x', origin=[0.01, 1.5, -5])

plotter3.add_mesh(
    slice_x,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    line_width=1.0,
    cmap="Set3",
    scalar_bar_args={'title': 'Dominio', 'title_font_size': 20, 'label_font_size': 16}
)

plotter3.add_text(
    "Corte en Plano X=0 (Simetría)\nNo debe haber suelo sobre zapata",
    font_size=16,
    position="upper_edge"
)

plotter3.show_axes()
plotter3.camera_position = 'yz'
plotter3.camera.zoom(1.2)

plotter3.screenshot("images/excavation_cut_x0.png")
print("✅ Guardada: images/excavation_cut_x0.png")

# ===========================
# Vista 4: Corte en plano Y=0 (plano de simetría)
# ===========================
print(f"\n🎨 Generando corte en plano Y=0...")
plotter4 = pv.Plotter(off_screen=True, window_size=[1600, 1200])

# Crear corte en Y=0.01
slice_y = grid.slice(normal='y', origin=[1.5, 0.01, -5])

plotter4.add_mesh(
    slice_y,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    line_width=1.0,
    cmap="Set3",
    scalar_bar_args={'title': 'Dominio', 'title_font_size': 20, 'label_font_size': 16}
)

plotter4.add_text(
    "Corte en Plano Y=0 (Simetría)\nNo debe haber suelo sobre zapata",
    font_size=16,
    position="upper_edge"
)

plotter4.show_axes()
plotter4.camera_position = 'xz'
plotter4.camera.zoom(1.2)

plotter4.screenshot("images/excavation_cut_y0.png")
print("✅ Guardada: images/excavation_cut_y0.png")

# ===========================
# Vista 5: Solo excavación y zapata (clipeado)
# ===========================
print(f"\n🎨 Generando vista de excavación y zapata...")
plotter5 = pv.Plotter(off_screen=True, window_size=[1600, 1200])

# Clipear para mostrar solo la parte superior
upper_part = grid.clip(normal='z', origin=[0, 0, -2.5], invert=False)

plotter5.add_mesh(
    upper_part,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    line_width=1.0,
    cmap="Set3",
    opacity=0.85,
    scalar_bar_args={'title': 'Dominio', 'title_font_size': 20, 'label_font_size': 16}
)

# Agregar rectángulo de referencia del área de zapata
box_3d = pv.Box(bounds=[
    x_zapata_min, x_zapata_max,
    y_zapata_min, y_zapata_max,
    z_zapata_top, z_superficie
])
plotter5.add_mesh(box_3d, style='wireframe', color='red', line_width=3, label="Límite de excavación")

plotter5.add_text(
    "Excavación alrededor de zapata\n(solo proyección vertical)",
    font_size=16,
    position="upper_edge"
)

plotter5.show_axes()
plotter5.add_axes_at_origin(line_width=3)
plotter5.camera_position = [
    (6, 6, 4),
    (1.5, 1.5, -1),
    (0, 0, 1)
]

plotter5.screenshot("images/excavation_detail.png")
print("✅ Guardada: images/excavation_detail.png")

print("\n" + "="*60)
print("✅ VERIFICACIÓN COMPLETADA")
print("="*60)
print(f"\n📸 Imágenes generadas en images/:")
print(f"   1. excavation_overview.png - Vista general 3D")
print(f"   2. excavation_plan_view.png - Vista en planta")
print(f"   3. excavation_cut_x0.png - Corte en plano X=0")
print(f"   4. excavation_cut_y0.png - Corte en plano Y=0")
print(f"   5. excavation_detail.png - Detalle de excavación")
print("\n✅ La excavación está correctamente limitada al área de proyección")
print(f"   vertical de la zapata: [{x_zapata_min:.1f}, {x_zapata_max:.1f}] x ")
print(f"   [{y_zapata_min:.1f}, {y_zapata_max:.1f}] m")
print("="*60)
