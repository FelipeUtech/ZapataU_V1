#!/usr/bin/env python3
"""
Verificar orientación del modelo VTU y crear imagen de referencia
"""
import pyvista as pv
import numpy as np

# Leer modelo
grid = pv.read('resultados_2phases.vtu')

# Crear visualización
plotter = pv.Plotter(off_screen=True, window_size=[1200, 800])

# Añadir el modelo con asentamientos
plotter.add_mesh(grid, scalars='Settlement_total_mm',
                cmap='jet',
                show_edges=False,
                scalar_bar_args={'title': 'Asentamiento Total (mm)',
                                'vertical': True,
                                'position_x': 0.85,
                                'position_y': 0.1})

# Añadir ejes de referencia
plotter.add_axes(xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)',
                line_width=5, color='black')

# Añadir texto con información
max_settlement = grid.point_data['Settlement_total_mm'].max()
max_idx = np.argmax(grid.point_data['Settlement_total_mm'])
max_point = grid.points[max_idx]

info_text = f"Máximo: {max_settlement:.1f} mm\n"
info_text += f"Ubicación: ({max_point[0]:.1f}, {max_point[1]:.1f}, {max_point[2]:.1f})\n"
info_text += f"Dominio: X=[0, 4.5m], Y=[0, 4.5m], Z=[-20, 0m]\n"
info_text += f"Zapata en origen (0,0)"

plotter.add_text(info_text, position='upper_left', font_size=10, color='black')

# Añadir marcador en el punto de máximo asentamiento
plotter.add_points(np.array([[0, 0, 0]]), color='red', point_size=20,
                  render_points_as_spheres=True)

# Vista isométrica
plotter.camera_position = [(8, -8, 5), (2.25, 2.25, -10), (0, 0, 1)]
plotter.camera.zoom(1.2)

# Guardar imagen
plotter.screenshot('verificacion_orientacion_vtu.png', transparent_background=False)
print("✓ Imagen guardada: verificacion_orientacion_vtu.png")

# Vista desde arriba (planta)
plotter2 = pv.Plotter(off_screen=True, window_size=[800, 800])
plotter2.add_mesh(grid, scalars='Settlement_total_mm',
                 cmap='jet',
                 show_edges=True,
                 scalar_bar_args={'title': 'Asentamiento (mm)', 'vertical': False})

# Solo mostrar la superficie (Z=0)
surface = grid.extract_surface()
plotter2.add_mesh(surface, scalars='Settlement_total_mm', cmap='jet', opacity=1.0)
plotter2.view_xy()
plotter2.camera.zoom(1.3)
plotter2.add_text('Vista en Planta (desde arriba)\nRojo = Máximo asentamiento',
                 position='upper_left', font_size=12, color='black')
plotter2.screenshot('vista_planta_asentamientos.png')
print("✓ Vista en planta guardada: vista_planta_asentamientos.png")

print("\nInformación del modelo:")
print(f"  Origen (0,0,0): ZAPATA - Máximo asentamiento")
print(f"  Esquina (4.5, 4.5, 0): LEJOS de zapata - Menor asentamiento")
print(f"  El modelo es 1/4 con simetría en X=0 y Y=0")
