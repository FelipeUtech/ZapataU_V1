import pyvista as pv

# Configurar PyVista para modo off-screen (sin GUI)
pv.set_plot_theme("document")

# Cargar la malla
grid = pv.read("mallas/zapata_3D_cuarto.vtu")

# Crear plotter off-screen
plotter = pv.Plotter(off_screen=True, window_size=[1920, 1080])

# Agregar malla con configuración visual
plotter.add_mesh(
    grid,
    scalars="dominio",
    show_edges=True,
    opacity=0.85,
    cmap='viridis',
    scalar_bar_args={
        'title': 'Dominio',
        'title_font_size': 20,
        'label_font_size': 16,
        'n_labels': 4
    }
)

# Agregar texto y ejes
plotter.add_text("Malla 3D - 1/4 de zapata empotrada", font_size=14, position='upper_edge')
plotter.show_axes()

# Configurar cámara para mejor vista
plotter.camera_position = [(5, 5, 5), (1.5, 1.5, -5), (0, 0, 1)]

# Guardar imagen
output_file = "mallas/mesh_visualization.png"
plotter.screenshot(output_file)
print(f"✅ Imagen guardada: {output_file}")

# También guardar una vista de corte
plotter2 = pv.Plotter(off_screen=True, window_size=[1920, 1080])
slice_x = grid.slice(normal='x', origin=(1.5, 1.5, -5))
plotter2.add_mesh(slice_x, scalars="dominio", show_edges=True, cmap='viridis')
plotter2.add_text("Corte en X - Vista interna", font_size=14, position='upper_edge')
plotter2.show_axes()
plotter2.screenshot("mallas/mesh_slice_x.png")
print(f"✅ Imagen de corte guardada: mallas/mesh_slice_x.png")
