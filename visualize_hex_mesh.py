"""
Script de visualización de malla hexaédrica con PyVista
Útil para verificar la malla antes de correr análisis en OpenSees
"""
import pyvista as pv
import numpy as np

# Cargar la malla hexaédrica estructurada
vtu_path = "mallas/zapata_3D_cuarto_hex_structured.vtu"
print(f"📂 Cargando malla: {vtu_path}")

grid = pv.read(vtu_path)

# Información de la malla
print(f"\n📊 Información de la malla:")
print(f"   - Número de puntos: {grid.n_points:,}")
print(f"   - Número de celdas: {grid.n_cells:,}")
print(f"   - Tipo de celdas: {grid.get_cell(0).type}")
print(f"   - Bounds X: [{grid.bounds[0]:.2f}, {grid.bounds[1]:.2f}]")
print(f"   - Bounds Y: [{grid.bounds[2]:.2f}, {grid.bounds[3]:.2f}]")
print(f"   - Bounds Z: [{grid.bounds[4]:.2f}, {grid.bounds[5]:.2f}]")

# Contar elementos por dominio
dominios = grid.cell_data["dominio"]
print(f"\n📊 Distribución de elementos:")
print(f"   - SOIL_1: {np.sum(dominios == 1):,} hexaedros")
print(f"   - SOIL_2: {np.sum(dominios == 2):,} hexaedros")
print(f"   - SOIL_3: {np.sum(dominios == 3):,} hexaedros")
print(f"   - FOOTING: {np.sum(dominios == 4):,} hexaedros")

# Crear visualizaciones
print(f"\n🎨 Creando visualización...")

# ===========================
# Visualización 1: Malla completa con dominios
# ===========================
plotter = pv.Plotter(window_size=[1200, 800])

# Agregar malla con colores por dominio
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
        'title_font_size': 14,
        'label_font_size': 12,
        'n_labels': 5,
        'fmt': '%.0f',
        'position_x': 0.85,
        'position_y': 0.3,
    }
)

# Añadir título y ejes
plotter.add_text(
    "Malla Hexaédrica Estructurada - Zapata 3D (1/4 Dominio)",
    font_size=14,
    color="black",
    position="upper_edge"
)

plotter.show_axes()
plotter.add_axes_at_origin(labels_off=False)

# Añadir grid de referencia
plotter.show_grid(
    color="gray",
    xlabel="X [m]",
    ylabel="Y [m]",
    zlabel="Z [m]"
)

# Configurar cámara para buena vista
plotter.camera_position = [
    (8, 8, 5),    # posición de la cámara
    (1.5, 1.5, -5),  # punto focal
    (0, 0, 1)     # vector up
]

print("✅ Mostrando visualización principal...")
print("\n💡 Controles:")
print("   - Click izquierdo + arrastrar: Rotar")
print("   - Click derecho + arrastrar: Zoom")
print("   - Scroll: Zoom")
print("   - 'q': Cerrar ventana")

plotter.show()

# ===========================
# Visualización 2: Solo la zapata
# ===========================
print("\n🔍 Mostrando solo la zapata...")
zapata = grid.threshold([3.5, 4.5], scalars="dominio")

plotter2 = pv.Plotter(window_size=[1000, 800])
plotter2.add_mesh(
    zapata,
    color="orange",
    show_edges=True,
    edge_color="black",
    line_width=1.0,
    label="Zapata"
)

plotter2.add_text("Zapata (FOOTING) - Vista Detallada", font_size=14, position="upper_edge")
plotter2.show_axes()
plotter2.add_axes_at_origin()
plotter2.show()

# ===========================
# Visualización 3: Corte transversal
# ===========================
print("\n✂️ Mostrando corte transversal...")
slice_mesh = grid.slice(normal='y', origin=[1.5, 1.5, -5])

plotter3 = pv.Plotter(window_size=[1000, 800])
plotter3.add_mesh(
    slice_mesh,
    scalars="dominio",
    show_edges=True,
    edge_color="black",
    cmap="Set3",
    scalar_bar_args={'title': 'Dominio'}
)

plotter3.add_text("Corte Transversal (Plano Y)", font_size=14, position="upper_edge")
plotter3.show_axes()
plotter3.camera_position = 'yz'
plotter3.show()

print("\n✅ Visualización completada")
print(f"\n📝 Siguiente paso:")
print(f"   - La malla está lista para usar en OpenSees")
print(f"   - Archivos disponibles:")
print(f"     * {vtu_path} (ParaView)")
print(f"     * mallas/zapata_3D_cuarto_hex_structured.xdmf (OpenSees)")
print(f"     * mallas/zapata_3D_cuarto_hex_structured.msh (Gmsh)")
