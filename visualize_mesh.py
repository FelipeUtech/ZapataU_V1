import pyvista as pv
import numpy as np

# Cargar la malla desde el archivo VTU
mesh_path = "mallas/zapata_3D_cuarto.vtu"
grid = pv.read(mesh_path)

print(f"✅ Malla cargada: {mesh_path}")
print(f"   - Número de puntos: {grid.n_points}")
print(f"   - Número de celdas: {grid.n_cells}")
print(f"   - Datos disponibles: {list(grid.cell_data.keys())}")

# ---------------------------------
# Visualización básica
# ---------------------------------
def visualize_basic():
    """Visualización básica con colores por dominio"""
    plotter = pv.Plotter()
    plotter.add_mesh(grid, scalars="dominio", show_edges=True, opacity=0.85,
                     cmap='viridis', scalar_bar_args={'title': 'Dominio'})
    plotter.add_text("Malla 3D - 1/4 de zapata empotrada", font_size=12)
    plotter.show_axes()
    plotter.show()

# ---------------------------------
# Visualización avanzada con cortes
# ---------------------------------
def visualize_with_slices():
    """Visualización con planos de corte"""
    plotter = pv.Plotter()

    # Malla completa con transparencia
    plotter.add_mesh(grid, scalars="dominio", opacity=0.3, show_edges=False)

    # Corte en X
    slice_x = grid.slice(normal='x')
    plotter.add_mesh(slice_x, scalars="dominio", show_edges=True,
                     cmap='viridis', scalar_bar_args={'title': 'Dominio'})

    # Corte en Y
    slice_y = grid.slice(normal='y')
    plotter.add_mesh(slice_y, scalars="dominio", show_edges=True, opacity=0.5)

    plotter.add_text("Cortes de la malla", font_size=12)
    plotter.show_axes()
    plotter.show()

# ---------------------------------
# Visualización por dominios separados
# ---------------------------------
def visualize_by_domains():
    """Visualización de cada dominio por separado"""
    plotter = pv.Plotter(shape=(2, 2))

    # Dominio 1 - SOIL_1
    plotter.subplot(0, 0)
    soil1 = grid.threshold([0.5, 1.5], scalars="dominio")
    plotter.add_mesh(soil1, color='brown', show_edges=True)
    plotter.add_text("SOIL_1 (Capa Superior)", font_size=10)
    plotter.show_axes()

    # Dominio 2 - SOIL_2
    plotter.subplot(0, 1)
    soil2 = grid.threshold([1.5, 2.5], scalars="dominio")
    plotter.add_mesh(soil2, color='tan', show_edges=True)
    plotter.add_text("SOIL_2 (Capa Media)", font_size=10)
    plotter.show_axes()

    # Dominio 3 - SOIL_3
    plotter.subplot(1, 0)
    soil3 = grid.threshold([2.5, 3.5], scalars="dominio")
    plotter.add_mesh(soil3, color='yellow', show_edges=True)
    plotter.add_text("SOIL_3 (Capa Inferior)", font_size=10)
    plotter.show_axes()

    # Dominio 4 - FOOTING
    plotter.subplot(1, 1)
    footing = grid.threshold([3.5, 4.5], scalars="dominio")
    plotter.add_mesh(footing, color='gray', show_edges=True)
    plotter.add_text("FOOTING (Zapata)", font_size=10)
    plotter.show_axes()

    plotter.show()

# ---------------------------------
# Exportar imagen estática
# ---------------------------------
def save_screenshot(filename="mallas/mesh_visualization.png"):
    """Guardar visualización como imagen"""
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(grid, scalars="dominio", show_edges=True, opacity=0.85,
                     cmap='viridis', scalar_bar_args={'title': 'Dominio'})
    plotter.add_text("Malla 3D - 1/4 de zapata empotrada", font_size=12)
    plotter.show_axes()
    plotter.screenshot(filename)
    print(f"✅ Imagen guardada: {filename}")

# ---------------------------------
# Menú principal
# ---------------------------------
if __name__ == "__main__":
    print("\n=== Opciones de Visualización ===")
    print("1. Visualización básica")
    print("2. Visualización con cortes")
    print("3. Visualización por dominios")
    print("4. Guardar imagen PNG")
    print("5. Todas las visualizaciones")

    opcion = input("\nSelecciona una opción (1-5): ").strip()

    if opcion == "1":
        visualize_basic()
    elif opcion == "2":
        visualize_with_slices()
    elif opcion == "3":
        visualize_by_domains()
    elif opcion == "4":
        save_screenshot()
    elif opcion == "5":
        visualize_basic()
        visualize_with_slices()
        visualize_by_domains()
        save_screenshot()
    else:
        print("Opción no válida. Mostrando visualización básica...")
        visualize_basic()
