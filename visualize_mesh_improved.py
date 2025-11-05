"""
Visualización Mejorada de la Malla 3D
======================================
Muestra elementos rectangulares con aristas tenues y nodos diferenciados por colores
"""

import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from config import *
from mesh_generator import MeshGenerator
from materials import MaterialManager

def plot_mesh_improved(mesh):
    """
    Visualización mejorada de la malla 3D con aristas y nodos coloreados

    Parameters:
    -----------
    mesh : MeshGenerator
        Objeto con la malla generada
    """
    fig = plt.figure(figsize=(20, 10))

    # Crear subplots
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')

    axes = [ax1, ax2]

    # Colores para estratos
    layer_colors = ['#8B4513', '#DAA520', '#F4A460']  # Marrón oscuro, dorado, arena

    print("\n--- Generando visualización mejorada ---")

    # ==========================================
    # VISTA 1: MALLA COMPLETA CON ARISTAS
    # ==========================================
    print("Graficando malla completa con aristas...")
    ax1.set_title('Malla Completa - Elementos con Aristas', fontsize=14, fontweight='bold')

    # 1. Dibujar aristas de elementos de suelo (con sampling para eficiencia)
    # Sampling: dibujar solo cada N elementos para mantener performance
    sampling_rate = max(1, len(mesh.soil_elements) // 500)  # Máximo 500 elementos
    soil_elements_list = list(mesh.soil_elements.items())
    sampled_elements = soil_elements_list[::sampling_rate]

    print(f"  Dibujando aristas de {len(sampled_elements)} elementos de suelo (sampling {sampling_rate})...")
    for elem_tag, elem_info in sampled_elements:
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']

        # Obtener coordenadas de los 8 nodos
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Definir las 12 aristas de un hexaedro
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Cara inferior
            [4, 5], [5, 6], [6, 7], [7, 4],  # Cara superior
            [0, 4], [1, 5], [2, 6], [3, 7]   # Aristas verticales
        ]

        # Dibujar cada arista con línea muy tenue
        for edge in edges:
            points = coords[edge]
            ax1.plot3D(points[:, 0], points[:, 1], points[:, 2],
                      color=layer_colors[layer_idx],
                      alpha=0.15,          # Muy transparente
                      linewidth=0.3)       # Muy delgada

    # 2. Dibujar aristas de elementos de zapata (líneas más visibles)
    print(f"  Dibujando aristas de {len(mesh.footing_elements)} elementos de zapata...")
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
            ax1.plot3D(points[:, 0], points[:, 1], points[:, 2],
                      color='darkred', alpha=0.6, linewidth=0.8)

    # 3. Dibujar NODOS por tipo
    print("  Dibujando nodos por tipo...")

    # Identificar nodos de zapata (excluyendo contacto)
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    # Nodos de contacto (interfaz suelo-zapata)
    contact_nodes = set(mesh.footing_nodes)

    # Nodos de zapata que NO son de contacto
    footing_only_nodes = footing_node_tags - contact_nodes

    # Nodos de suelo por estrato (excluyendo contacto)
    soil_nodes_by_layer = {i: [] for i in range(len(SOIL_LAYERS))}
    for node_tag, (x, y, z) in mesh.nodes.items():
        if node_tag not in footing_node_tags and node_tag not in contact_nodes:
            depth = abs(z)
            for i, layer in enumerate(SOIL_LAYERS):
                if layer['depth_top'] <= depth < layer['depth_bottom']:
                    soil_nodes_by_layer[i].append([x, y, z])
                    break

    # Graficar nodos de suelo por estrato (pequeños)
    for i, nodes_list in soil_nodes_by_layer.items():
        if nodes_list:
            nodes_array = np.array(nodes_list)
            ax1.scatter(nodes_array[:, 0], nodes_array[:, 1], nodes_array[:, 2],
                       c=layer_colors[i], s=2, alpha=0.4,
                       label=f'Estrato {i+1}')

    # Graficar nodos de zapata (medianos, rojos)
    if footing_only_nodes:
        footing_coords = np.array([mesh.nodes[n] for n in footing_only_nodes])
        ax1.scatter(footing_coords[:, 0], footing_coords[:, 1], footing_coords[:, 2],
                   c='red', s=15, alpha=0.8, edgecolors='darkred', linewidths=0.5,
                   label='Nodos zapata')

    # Graficar nodos de CONTACTO (grandes, amarillo brillante con borde negro)
    if contact_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in contact_nodes])
        ax1.scatter(contact_coords[:, 0], contact_coords[:, 1], contact_coords[:, 2],
                   c='yellow', s=50, alpha=1.0, marker='*',
                   edgecolors='black', linewidths=1.5,
                   label='Nodos contacto', zorder=10)

    ax1.legend(fontsize=10, loc='upper left')

    # ==========================================
    # VISTA 2: CORTE DETALLADO
    # ==========================================
    print("Graficando vista de corte detallada...")
    ax2.set_title('Corte Central - Detalle de Estratos y Zapata', fontsize=14, fontweight='bold')

    # Seleccionar elementos en el plano central
    x_center = SOIL_WIDTH_X / 2
    tolerance = 1.0

    # Dibujar aristas de elementos en el corte (con sampling)
    sampling_rate_cut = max(1, len(mesh.soil_elements) // 300)
    sampled_cut_elements = soil_elements_list[::sampling_rate_cut]

    for elem_tag, elem_info in sampled_cut_elements:
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Verificar si el elemento está cerca del plano central
        x_coords = coords[:, 0]
        if np.any(np.abs(x_coords - x_center) < tolerance):
            edges = [
                [0, 1], [1, 2], [2, 3], [3, 0],
                [4, 5], [5, 6], [6, 7], [7, 4],
                [0, 4], [1, 5], [2, 6], [3, 7]
            ]

            for edge in edges:
                points = coords[edge]
                ax2.plot3D(points[:, 0], points[:, 1], points[:, 2],
                          color=layer_colors[layer_idx],
                          alpha=0.3, linewidth=0.5)

    # Aristas de zapata en el corte
    for elem in mesh.footing_elements:
        nodes = elem['nodes']
        coords = np.array([mesh.nodes[n] for n in nodes])

        x_coords = coords[:, 0]
        if np.any(np.abs(x_coords - x_center) < tolerance):
            edges = [
                [0, 1], [1, 2], [2, 3], [3, 0],
                [4, 5], [5, 6], [6, 7], [7, 4],
                [0, 4], [1, 5], [2, 6], [3, 7]
            ]

            for edge in edges:
                points = coords[edge]
                ax2.plot3D(points[:, 0], points[:, 1], points[:, 2],
                          color='darkred', alpha=0.7, linewidth=1.0)

    # Nodos en el corte
    for node_tag, (x, y, z) in mesh.nodes.items():
        if abs(x - x_center) < tolerance:
            depth = abs(z)

            # Color según tipo
            if node_tag in contact_nodes:
                color, size, marker = 'yellow', 80, '*'
                ax2.scatter([x], [y], [z], c=color, s=size, marker=marker,
                           edgecolors='black', linewidths=2, alpha=1.0, zorder=10)
            elif node_tag in footing_node_tags:
                color, size, marker = 'red', 25, 'o'
                ax2.scatter([x], [y], [z], c=color, s=size, marker=marker,
                           edgecolors='darkred', linewidths=0.5, alpha=0.9)
            else:
                # Nodo de suelo
                for i, layer in enumerate(SOIL_LAYERS):
                    if layer['depth_top'] <= depth < layer['depth_bottom']:
                        color, size, marker = layer_colors[i], 10, 'o'
                        ax2.scatter([x], [y], [z], c=color, s=size, marker=marker,
                                   alpha=0.5)
                        break

    # Añadir líneas horizontales para marcar estratos
    y_min, y_max = 0, SOIL_WIDTH_Y
    x_line = x_center
    for i, layer in enumerate(SOIL_LAYERS[:-1]):  # Excepto el último
        z_boundary = -layer['depth_bottom']
        ax2.plot([x_line, x_line], [y_min, y_max], [z_boundary, z_boundary],
                'k--', linewidth=1.5, alpha=0.5, label=f'Límite estrato {i+1}-{i+2}')

    ax2.legend(fontsize=9, loc='upper right')

    # ==========================================
    # CONFIGURACIÓN DE EJES
    # ==========================================
    for ax in axes:
        ax.set_xlabel('X (m)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Y (m)', fontsize=11, fontweight='bold')
        ax.set_zlabel('Z (m)', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle=':')

        # Límites
        ax.set_xlim([0, SOIL_WIDTH_X])
        ax.set_ylim([0, SOIL_WIDTH_Y])
        ax.set_zlim([-SOIL_DEPTH, 1])

        # Aspecto
        ax.set_box_aspect([SOIL_WIDTH_X, SOIL_WIDTH_Y, SOIL_DEPTH])

    # Ángulos de vista
    ax1.view_init(elev=20, azim=45)
    ax2.view_init(elev=15, azim=0)

    plt.tight_layout()

    # Guardar figura
    plt.savefig('mesh_visualization_improved.png', dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualización mejorada guardada en: mesh_visualization_improved.png")

    plt.show()

def print_mesh_statistics(mesh):
    """Imprime estadísticas detalladas de la malla"""
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE LA MALLA MEJORADA")
    print("="*70)

    print(f"\nNODOS:")
    print(f"  Total de nodos: {len(mesh.nodes)}")

    # Contar nodos por tipo
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    contact_nodes = set(mesh.footing_nodes)
    footing_only = footing_node_tags - contact_nodes

    print(f"  Nodos de suelo: {len(mesh.nodes) - len(footing_node_tags)}")
    print(f"  Nodos de zapata: {len(footing_only)}")
    print(f"  Nodos de contacto: {len(contact_nodes)}")

    # Por estrato
    print(f"\n  Nodos por estrato:")
    for i, layer in enumerate(SOIL_LAYERS):
        count = 0
        for node_tag, (x, y, z) in mesh.nodes.items():
            if node_tag not in footing_node_tags:
                depth = abs(z)
                if layer['depth_top'] <= depth < layer['depth_bottom']:
                    count += 1
        print(f"    Estrato {i+1} ({layer['name']}): {count} nodos")

    print(f"\nELEMENTOS:")
    print(f"  Total de elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Total de elementos de zapata: {len(mesh.footing_elements)}")

    # Contar aristas totales
    total_edges = (len(mesh.soil_elements) + len(mesh.footing_elements)) * 12
    print(f"  Total de aristas dibujadas: {total_edges}")

    # Elementos por estrato
    elem_by_layer = {}
    for elem_tag, elem_info in mesh.soil_elements.items():
        layer_idx = elem_info['layer']
        elem_by_layer[layer_idx] = elem_by_layer.get(layer_idx, 0) + 1

    print(f"\n  Elementos por estrato:")
    for i, layer in enumerate(SOIL_LAYERS):
        count = elem_by_layer.get(i, 0)
        print(f"    Estrato {i+1} ({layer['name']}): {count} elementos")

    print("\n" + "="*70)

if __name__ == '__main__':
    print("="*70)
    print("VISUALIZACIÓN MEJORADA DE MALLA 3D")
    print("="*70)

    # Mostrar configuración
    print_configuration()

    # Inicializar modelo
    print("\nInicializando modelo OpenSees...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    # Generar malla
    print("\nGenerando malla con elementos rectangulares...")
    mesh = MeshGenerator()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()

    # Estadísticas
    print_mesh_statistics(mesh)

    # Visualizar
    print("\nGenerando visualización 3D mejorada...")
    plot_mesh_improved(mesh)

    print("\n✅ Proceso completado!")
