"""
Visualización de la Malla 3D
=============================
Script para visualizar la malla generada del suelo y la zapata
"""

import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from config import *
from mesh_generator import MeshGenerator
from materials import MaterialManager

def plot_mesh_3d(mesh):
    """
    Visualiza la malla 3D generada

    Parameters:
    -----------
    mesh : MeshGenerator
        Objeto con la malla generada
    """
    fig = plt.figure(figsize=(16, 12))

    # Crear subplots
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222, projection='3d')
    ax3 = fig.add_subplot(223, projection='3d')
    ax4 = fig.add_subplot(224, projection='3d')

    axes = [ax1, ax2, ax3, ax4]

    # Colores para estratos
    layer_colors = plt.cm.viridis(np.linspace(0, 1, len(SOIL_LAYERS)))

    # 1. Vista completa con nodos
    print("\nGraficando vista completa...")
    ax1.set_title('Vista Completa - Nodos', fontsize=12, fontweight='bold')

    # Plotear nodos del suelo por estratos
    for i, layer in enumerate(SOIL_LAYERS):
        layer_nodes = []
        for node_tag, (x, y, z) in mesh.nodes.items():
            depth = abs(z)
            if layer['depth_top'] <= depth < layer['depth_bottom']:
                layer_nodes.append([x, y, z])

        if layer_nodes:
            layer_nodes = np.array(layer_nodes)
            ax1.scatter(layer_nodes[:, 0], layer_nodes[:, 1], layer_nodes[:, 2],
                       c=[layer_colors[i]], s=2, alpha=0.4, label=f"Estrato {i+1}")

    ax1.legend(fontsize=8)

    # 2. Vista de elementos de suelo
    print("Graficando elementos de suelo...")
    ax2.set_title('Elementos de Suelo por Estrato', fontsize=12, fontweight='bold')

    # Plotear algunos elementos de cada estrato (sampling para no saturar)
    for elem_tag, elem_info in list(mesh.soil_elements.items())[::50]:  # Cada 50 elementos
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']

        # Obtener coordenadas de los 8 nodos
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Dibujar las aristas del elemento
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Base inferior
            [4, 5], [5, 6], [6, 7], [7, 4],  # Base superior
            [0, 4], [1, 5], [2, 6], [3, 7]   # Aristas verticales
        ]

        for edge in edges:
            points = coords[edge]
            ax2.plot3D(points[:, 0], points[:, 1], points[:, 2],
                      color=layer_colors[layer_idx], alpha=0.3, linewidth=0.5)

    # 3. Vista de la zapata
    print("Graficando zapata...")
    ax3.set_title('Detalle de la Zapata', fontsize=12, fontweight='bold')

    # Nodos de la zapata
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    footing_coords = np.array([mesh.nodes[n] for n in footing_node_tags])
    ax3.scatter(footing_coords[:, 0], footing_coords[:, 1], footing_coords[:, 2],
               c='red', s=20, label='Nodos de zapata', alpha=0.8)

    # Elementos de zapata
    for elem in mesh.footing_elements:
        nodes = elem['nodes']
        coords = np.array([mesh.nodes[n] for n in nodes])

        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7]
        ]

        for edge in edges:
            points = coords[edge]
            ax3.plot3D(points[:, 0], points[:, 1], points[:, 2],
                      'r-', linewidth=1.5, alpha=0.7)

    # Nodos de contacto suelo-zapata
    if mesh.footing_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in mesh.footing_nodes])
        ax3.scatter(contact_coords[:, 0], contact_coords[:, 1], contact_coords[:, 2],
                   c='yellow', s=30, marker='*', label='Contacto', alpha=1.0, edgecolors='black')

    ax3.legend(fontsize=8)

    # 4. Vista lateral (corte vertical)
    print("Graficando vista lateral...")
    ax4.set_title('Vista Lateral - Corte YZ', fontsize=12, fontweight='bold')

    # Seleccionar nodos cercanos al plano central X
    x_center = SOIL_WIDTH_X / 2
    tolerance = 0.5

    for i, layer in enumerate(SOIL_LAYERS):
        layer_nodes = []
        for node_tag, (x, y, z) in mesh.nodes.items():
            if abs(x - x_center) < tolerance:
                depth = abs(z)
                if layer['depth_top'] <= depth < layer['depth_bottom']:
                    layer_nodes.append([x, y, z])

        if layer_nodes:
            layer_nodes = np.array(layer_nodes)
            ax4.scatter(layer_nodes[:, 1], layer_nodes[:, 2], layer_nodes[:, 0],
                       c=[layer_colors[i]], s=10, alpha=0.6, label=f"Estrato {i+1}")

    # Zapata en vista lateral
    footing_coords_filtered = []
    for n in footing_node_tags:
        x, y, z = mesh.nodes[n]
        if abs(x - x_center) < tolerance:
            footing_coords_filtered.append([x, y, z])

    if footing_coords_filtered:
        footing_coords_filtered = np.array(footing_coords_filtered)
        ax4.scatter(footing_coords_filtered[:, 1], footing_coords_filtered[:, 2],
                   footing_coords_filtered[:, 0],
                   c='red', s=50, marker='s', label='Zapata', edgecolors='black')

    ax4.legend(fontsize=8)
    ax4.set_xlabel('Y (m)')
    ax4.set_ylabel('Z (m)')

    # Configurar todos los ejes
    for ax in axes:
        ax.set_xlabel('X (m)', fontsize=10)
        ax.set_ylabel('Y (m)', fontsize=10)
        ax.set_zlabel('Z (m)', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Establecer límites
        ax.set_xlim([0, SOIL_WIDTH_X])
        ax.set_ylim([0, SOIL_WIDTH_Y])
        ax.set_zlim([-SOIL_DEPTH, 1])

    # Diferentes ángulos de vista
    ax1.view_init(elev=25, azim=45)
    ax2.view_init(elev=20, azim=60)
    ax3.view_init(elev=30, azim=135)
    ax4.view_init(elev=15, azim=0)

    plt.tight_layout()

    # Guardar figura
    plt.savefig('mesh_visualization.png', dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualización guardada en: mesh_visualization.png")

    plt.show()

def print_mesh_statistics(mesh):
    """Imprime estadísticas de la malla"""
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE LA MALLA")
    print("="*70)

    print(f"\nNODOS:")
    print(f"  Total de nodos: {len(mesh.nodes)}")

    # Contar nodos por estrato
    print(f"\n  Nodos por estrato:")
    for i, layer in enumerate(SOIL_LAYERS):
        count = 0
        for node_tag, (x, y, z) in mesh.nodes.items():
            depth = abs(z)
            if layer['depth_top'] <= depth < layer['depth_bottom']:
                count += 1
        print(f"    Estrato {i+1} ({layer['name']}): {count} nodos")

    print(f"\nELEMENTOS:")
    print(f"  Total de elementos de suelo: {len(mesh.soil_elements)}")

    # Contar elementos por estrato
    print(f"\n  Elementos por estrato:")
    elem_by_layer = {}
    for elem_tag, elem_info in mesh.soil_elements.items():
        layer_idx = elem_info['layer']
        elem_by_layer[layer_idx] = elem_by_layer.get(layer_idx, 0) + 1

    for i, layer in enumerate(SOIL_LAYERS):
        count = elem_by_layer.get(i, 0)
        print(f"    Estrato {i+1} ({layer['name']}): {count} elementos")

    print(f"\n  Total de elementos de zapata: {len(mesh.footing_elements)}")
    print(f"  Nodos de contacto suelo-zapata: {len(mesh.footing_nodes)}")

    # Rangos de coordenadas
    all_x = [coord[0] for coord in mesh.nodes.values()]
    all_y = [coord[1] for coord in mesh.nodes.values()]
    all_z = [coord[2] for coord in mesh.nodes.values()]

    print(f"\nRANGOS DE COORDENADAS:")
    print(f"  X: [{min(all_x):.2f}, {max(all_x):.2f}] m")
    print(f"  Y: [{min(all_y):.2f}, {max(all_y):.2f}] m")
    print(f"  Z: [{min(all_z):.2f}, {max(all_z):.2f}] m")

    print("\n" + "="*70)

if __name__ == '__main__':
    print("="*70)
    print("VISUALIZACIÓN DE MALLA 3D")
    print("="*70)

    # Mostrar configuración
    print_configuration()

    # Inicializar modelo
    print("\nInicializando modelo OpenSees...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    # Generar malla
    print("\nGenerando malla...")
    mesh = MeshGenerator()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()

    # Mostrar estadísticas
    print_mesh_statistics(mesh)

    # Visualizar
    print("\nGenerando visualización 3D...")
    plot_mesh_3d(mesh)

    print("\n✅ Proceso completado!")
