"""
Visor Interactivo 3D en HTML
==============================
Genera una visualización interactiva de la malla que se puede rotar, hacer zoom y explorar
"""

import openseespy.opensees as ops
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import *
from mesh_generator import MeshGenerator

def create_interactive_viewer(mesh):
    """
    Crea visualización interactiva 3D con Plotly

    Parameters:
    -----------
    mesh : MeshGenerator
        Objeto con la malla generada
    """
    print("\n--- Generando visor interactivo 3D ---")

    # Inicializar figura
    fig = go.Figure()

    # Colores para estratos
    layer_colors = {
        0: 'rgb(139, 69, 19)',   # Marrón oscuro
        1: 'rgb(218, 165, 32)',  # Dorado
        2: 'rgb(244, 164, 96)'   # Arena
    }

    # ==========================================
    # 1. ARISTAS DE ELEMENTOS DE SUELO
    # ==========================================
    print("  Procesando aristas de elementos de suelo...")

    # Sampling para eficiencia
    sampling_rate = max(1, len(mesh.soil_elements) // 800)
    soil_elements_list = list(mesh.soil_elements.items())
    sampled_elements = soil_elements_list[::sampling_rate]

    # Recopilar todas las aristas por estrato
    edges_by_layer = {i: {'x': [], 'y': [], 'z': []} for i in range(len(SOIL_LAYERS))}

    for elem_tag, elem_info in sampled_elements:
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Definir aristas del hexaedro
        edge_indices = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Cara inferior
            [4, 5], [5, 6], [6, 7], [7, 4],  # Cara superior
            [0, 4], [1, 5], [2, 6], [3, 7]   # Verticales
        ]

        for edge in edge_indices:
            p1, p2 = coords[edge[0]], coords[edge[1]]
            edges_by_layer[layer_idx]['x'].extend([p1[0], p2[0], None])
            edges_by_layer[layer_idx]['y'].extend([p1[1], p2[1], None])
            edges_by_layer[layer_idx]['z'].extend([p1[2], p2[2], None])

    # Agregar aristas de suelo por estrato
    for i, layer in enumerate(SOIL_LAYERS):
        fig.add_trace(go.Scatter3d(
            x=edges_by_layer[i]['x'],
            y=edges_by_layer[i]['y'],
            z=edges_by_layer[i]['z'],
            mode='lines',
            name=f'Estrato {i+1}: {layer["name"]}',
            line=dict(color=layer_colors[i], width=1),
            opacity=0.2,
            hoverinfo='name'
        ))

    # ==========================================
    # 2. ARISTAS DE ELEMENTOS DE ZAPATA
    # ==========================================
    print("  Procesando aristas de zapata...")

    footing_edges = {'x': [], 'y': [], 'z': []}
    for elem in mesh.footing_elements:
        nodes = elem['nodes']
        coords = np.array([mesh.nodes[n] for n in nodes])

        edge_indices = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7]
        ]

        for edge in edge_indices:
            p1, p2 = coords[edge[0]], coords[edge[1]]
            footing_edges['x'].extend([p1[0], p2[0], None])
            footing_edges['y'].extend([p1[1], p2[1], None])
            footing_edges['z'].extend([p1[2], p2[2], None])

    fig.add_trace(go.Scatter3d(
        x=footing_edges['x'],
        y=footing_edges['y'],
        z=footing_edges['z'],
        mode='lines',
        name='Aristas de zapata',
        line=dict(color='darkred', width=2),
        opacity=0.7,
        hoverinfo='name'
    ))

    # ==========================================
    # 3. NODOS POR TIPO
    # ==========================================
    print("  Procesando nodos...")

    # Identificar nodos por tipo
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    contact_nodes = set(mesh.footing_nodes)
    footing_only = footing_node_tags - contact_nodes

    # Nodos de suelo por estrato (sampling para reducir cantidad)
    node_sampling = max(1, len(mesh.nodes) // 3000)
    soil_nodes_by_layer = {i: [] for i in range(len(SOIL_LAYERS))}

    for idx, (node_tag, (x, y, z)) in enumerate(mesh.nodes.items()):
        if idx % node_sampling != 0:
            continue
        if node_tag not in footing_node_tags and node_tag not in contact_nodes:
            depth = abs(z)
            for i, layer in enumerate(SOIL_LAYERS):
                if layer['depth_top'] <= depth < layer['depth_bottom']:
                    soil_nodes_by_layer[i].append([x, y, z])
                    break

    # Agregar nodos de suelo por estrato
    for i, nodes_list in soil_nodes_by_layer.items():
        if nodes_list:
            nodes_array = np.array(nodes_list)
            fig.add_trace(go.Scatter3d(
                x=nodes_array[:, 0],
                y=nodes_array[:, 1],
                z=nodes_array[:, 2],
                mode='markers',
                name=f'Nodos {SOIL_LAYERS[i]["name"]}',
                marker=dict(size=2, color=layer_colors[i], opacity=0.3),
                hovertemplate='Estrato %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.2f}',
                text=[f'{i+1}'] * len(nodes_array)
            ))

    # Nodos de zapata
    if footing_only:
        footing_coords = np.array([mesh.nodes[n] for n in footing_only])
        fig.add_trace(go.Scatter3d(
            x=footing_coords[:, 0],
            y=footing_coords[:, 1],
            z=footing_coords[:, 2],
            mode='markers',
            name='Nodos de zapata',
            marker=dict(size=4, color='red', symbol='circle',
                       line=dict(color='darkred', width=1)),
            hovertemplate='Zapata<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.2f}'
        ))

    # Nodos de contacto (los más importantes)
    if contact_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in contact_nodes])
        fig.add_trace(go.Scatter3d(
            x=contact_coords[:, 0],
            y=contact_coords[:, 1],
            z=contact_coords[:, 2],
            mode='markers',
            name='⭐ Nodos de CONTACTO',
            marker=dict(size=8, color='yellow', symbol='diamond',
                       line=dict(color='black', width=2)),
            hovertemplate='<b>CONTACTO Suelo-Zapata</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.2f}'
        ))

    # ==========================================
    # 4. CONFIGURACIÓN DE LA FIGURA
    # ==========================================

    fig.update_layout(
        title={
            'text': '<b>Visor Interactivo 3D - Malla de Ensayo de Carga de Zapata</b><br>' +
                   f'<sub>Zapata {FOOTING_WIDTH}×{FOOTING_LENGTH}m a Df={EMBEDMENT_DEPTH}m | ' +
                   f'{len(mesh.nodes)} nodos | {len(mesh.soil_elements)} elem. suelo | ' +
                   f'{len(mesh.footing_elements)} elem. zapata</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='rgb(230, 230,230)',
                      gridcolor='white', showbackground=True),
            yaxis=dict(title='Y (m)', backgroundcolor='rgb(230, 230,230)',
                      gridcolor='white', showbackground=True),
            zaxis=dict(title='Z (m)', backgroundcolor='rgb(230, 230,230)',
                      gridcolor='white', showbackground=True),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                center=dict(x=0, y=0, z=-0.3)
            )
        ),
        width=1400,
        height=900,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='black',
            borderwidth=1
        ),
        hovermode='closest'
    )

    return fig

def generate_html_viewer():
    """Genera el archivo HTML completo"""
    print("="*70)
    print("GENERANDO VISOR INTERACTIVO HTML 3D")
    print("="*70)

    # Configuración
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

    # Estadísticas
    print(f"\nEstadísticas:")
    print(f"  Nodos totales: {len(mesh.nodes)}")
    print(f"  Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos de zapata: {len(mesh.footing_elements)}")
    print(f"  Nodos de contacto: {len(mesh.footing_nodes)}")

    # Crear visualización
    fig = create_interactive_viewer(mesh)

    # Exportar a HTML
    html_file = 'mesh_viewer_3d.html'
    print(f"\n  Exportando a {html_file}...")

    fig.write_html(
        html_file,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['toImage'],
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
        },
        include_plotlyjs='cdn'
    )

    print(f"\n✅ Visor HTML generado: {html_file}")
    print(f"\n📖 INSTRUCCIONES:")
    print(f"  1. Abre el archivo '{html_file}' en tu navegador")
    print(f"  2. Usa el mouse para:")
    print(f"     - Rotar: Click izquierdo y arrastra")
    print(f"     - Zoom: Rueda del mouse")
    print(f"     - Pan: Click derecho y arrastra")
    print(f"  3. Haz hover sobre los elementos para ver información")
    print(f"  4. Usa la leyenda para mostrar/ocultar capas")

    print("\n" + "="*70)

    return html_file

if __name__ == '__main__':
    generate_html_viewer()
    print("\n✅ Proceso completado!")
