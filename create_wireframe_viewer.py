"""
Visualizador de Verificación de Malla - Solo Nodos y Aristas
=============================================================
Muestra estructura wireframe para verificar continuidad
"""

import openseespy.opensees as ops
import numpy as np
import plotly.graph_objects as go
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def create_wireframe_viewer(mesh):
    """
    Crea visualización tipo wireframe con solo nodos y aristas
    """
    print("\n--- Generando visualización wireframe ---")

    fig = go.Figure()

    # Colores para aristas por estrato (gama de cafés/marrones)
    edge_colors = {
        0: 'rgb(101, 67, 33)',    # Marrón oscuro
        1: 'rgb(139, 90, 43)',    # Marrón medio
        2: 'rgb(180, 120, 60)',   # Marrón claro
    }

    footing_edge_color = 'rgb(128, 128, 128)'  # Gris

    # ==========================================
    # 1. ARISTAS DE ELEMENTOS DE SUELO
    # ==========================================
    print("  Procesando aristas de elementos de suelo...")

    # Agrupar aristas por estrato
    edges_by_layer = {i: {'x': [], 'y': [], 'z': []} for i in range(len(SOIL_LAYERS))}

    for elem_tag, elem_info in mesh.soil_elements.items():
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']

        # Obtener coordenadas de los 8 nodos
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Definir las 12 aristas de un hexaedro
        edge_indices = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Cara inferior
            [4, 5], [5, 6], [6, 7], [7, 4],  # Cara superior
            [0, 4], [1, 5], [2, 6], [3, 7]   # Aristas verticales
        ]

        # Agregar cada arista
        for edge in edge_indices:
            p1, p2 = coords[edge[0]], coords[edge[1]]
            edges_by_layer[layer_idx]['x'].extend([p1[0], p2[0], None])
            edges_by_layer[layer_idx]['y'].extend([p1[1], p2[1], None])
            edges_by_layer[layer_idx]['z'].extend([p1[2], p2[2], None])

    # Crear trazas de aristas por estrato
    for i, layer in enumerate(SOIL_LAYERS):
        if len(edges_by_layer[i]['x']) > 0:
            print(f"    Estrato {i+1}: {len(edges_by_layer[i]['x'])//3} aristas")

            fig.add_trace(go.Scatter3d(
                x=edges_by_layer[i]['x'],
                y=edges_by_layer[i]['y'],
                z=edges_by_layer[i]['z'],
                mode='lines',
                name=f'Estrato {i+1}: {layer["name"]}',
                line=dict(
                    color=edge_colors[i],
                    width=0.8
                ),
                opacity=0.4,
                hoverinfo='name',
                showlegend=True
            ))

    # ==========================================
    # 2. ARISTAS DE ELEMENTOS DE ZAPATA (GRIS)
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

    print(f"    Zapata: {len(footing_edges['x'])//3} aristas")

    fig.add_trace(go.Scatter3d(
        x=footing_edges['x'],
        y=footing_edges['y'],
        z=footing_edges['z'],
        mode='lines',
        name='Zapata (Concreto)',
        line=dict(
            color=footing_edge_color,
            width=3
        ),
        hoverinfo='name',
        showlegend=True
    ))

    # ==========================================
    # 3. NODOS (PEQUEÑOS, SEMI-TRANSPARENTES)
    # ==========================================
    print("  Procesando nodos...")

    # Identificar tipos de nodos
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    contact_nodes = set(mesh.footing_nodes)
    footing_only = footing_node_tags - contact_nodes

    # Nodos de suelo (sampling para no saturar)
    soil_nodes = []
    sampling = max(1, len(mesh.nodes) // 2000)

    for idx, (node_tag, (x, y, z)) in enumerate(mesh.nodes.items()):
        if idx % sampling == 0 and node_tag not in footing_node_tags:
            soil_nodes.append([x, y, z])

    if soil_nodes:
        soil_coords = np.array(soil_nodes)
        print(f"    Nodos de suelo: {len(soil_coords)} (con sampling)")

        fig.add_trace(go.Scatter3d(
            x=soil_coords[:, 0],
            y=soil_coords[:, 1],
            z=soil_coords[:, 2],
            mode='markers',
            name='Nodos de suelo',
            marker=dict(
                size=1.5,
                color='rgb(100, 100, 100)',
                opacity=0.3
            ),
            hoverinfo='skip',
            showlegend=True
        ))

    # Nodos de zapata (no contacto)
    if footing_only:
        footing_coords = np.array([mesh.nodes[n] for n in footing_only])
        print(f"    Nodos de zapata: {len(footing_coords)}")

        fig.add_trace(go.Scatter3d(
            x=footing_coords[:, 0],
            y=footing_coords[:, 1],
            z=footing_coords[:, 2],
            mode='markers',
            name='Nodos zapata',
            marker=dict(
                size=2,
                color='gray',
                opacity=0.6
            ),
            hoverinfo='skip',
            showlegend=True
        ))

    # ==========================================
    # 4. NODOS DE CONTACTO (AMARILLO BRILLANTE)
    # ==========================================
    print("  Procesando nodos de contacto...")

    if contact_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in contact_nodes])
        print(f"    Nodos de contacto: {len(contact_coords)}")

        fig.add_trace(go.Scatter3d(
            x=contact_coords[:, 0],
            y=contact_coords[:, 1],
            z=contact_coords[:, 2],
            mode='markers',
            name='⭐ NODOS DE CONTACTO ⭐',
            marker=dict(
                size=8,
                color='yellow',
                symbol='diamond',
                line=dict(
                    color='orange',
                    width=2
                ),
                opacity=1.0
            ),
            hovertemplate='<b>CONTACTO Suelo-Zapata</b><br>Nodo: %{text}<br>X: %{x:.3f}m<br>Y: %{y:.3f}m<br>Z: %{z:.3f}m',
            text=[str(n) for n in contact_nodes],
            showlegend=True
        ))

    # ==========================================
    # 5. EJES DE SIMETRÍA
    # ==========================================
    print("  Agregando ejes de simetría...")

    # Eje X
    fig.add_trace(go.Scatter3d(
        x=[0, SOIL_WIDTH_X],
        y=[0, 0],
        z=[0, 0],
        mode='lines',
        name='Eje Simetría X',
        line=dict(color='blue', width=6, dash='dash'),
        showlegend=True
    ))

    # Eje Y
    fig.add_trace(go.Scatter3d(
        x=[0, 0],
        y=[0, SOIL_WIDTH_Y],
        z=[0, 0],
        mode='lines',
        name='Eje Simetría Y',
        line=dict(color='green', width=6, dash='dash'),
        showlegend=True
    ))

    # ==========================================
    # 6. CONFIGURACIÓN
    # ==========================================

    fig.update_layout(
        title=dict(
            text='<b>Verificación de Malla - Wireframe (Nodos y Aristas)</b><br>' +
                 f'<sub>Modelo 1/4 Simetría | Zapata {FOOTING_WIDTH}×{FOOTING_LENGTH}m | ' +
                 f'Df={EMBEDMENT_DEPTH}m | {len(mesh.nodes)} nodos | ' +
                 f'{len(mesh.soil_elements)} elem. suelo | {len(mesh.footing_elements)} elem. zapata</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=16, family='Arial Black')
        ),
        scene=dict(
            xaxis=dict(
                title='<b>X (m)</b>',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='rgb(220, 220, 220)',
                showbackground=True,
                zerolinecolor='rgb(200, 200, 200)',
            ),
            yaxis=dict(
                title='<b>Y (m)</b>',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='rgb(220, 220, 220)',
                showbackground=True,
                zerolinecolor='rgb(200, 200, 200)',
            ),
            zaxis=dict(
                title='<b>Z (m)</b>',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='rgb(220, 220, 220)',
                showbackground=True,
                zerolinecolor='rgb(200, 200, 200)',
            ),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                center=dict(x=0, y=0, z=-0.3)
            )
        ),
        width=1600,
        height=1000,
        showlegend=True,
        legend=dict(
            x=1.01,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='black',
            borderwidth=2,
            font=dict(size=11, family='Arial')
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='closest'
    )

    return fig

def generate_wireframe_viewer():
    """Genera visualización wireframe para verificación"""
    print("="*70)
    print("VISUALIZADOR WIREFRAME - VERIFICACIÓN DE CONTINUIDAD")
    print("="*70)

    print_configuration()

    print("\nInicializando modelo...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    print("\nGenerando malla...")
    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    print(f"\nEstadísticas:")
    print(f"  Nodos totales: {len(mesh.nodes)}")
    print(f"  Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos de zapata: {len(mesh.footing_elements)}")
    print(f"  Nodos de contacto: {len(mesh.footing_nodes)}")

    # Crear visualización
    fig = create_wireframe_viewer(mesh)

    # Exportar
    html_file = 'mesh_viewer_wireframe.html'
    print(f"\n  Exportando a {html_file}...")

    fig.write_html(
        html_file,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'mesh_wireframe',
                'height': 1000,
                'width': 1600,
                'scale': 2
            }
        },
        include_plotlyjs='cdn'
    )

    print(f"\n✅ Visualización wireframe generada: {html_file}")
    print(f"\n📖 CARACTERÍSTICAS:")
    print(f"  • Solo nodos y aristas (wireframe)")
    print(f"  • Aristas de zapata en GRIS")
    print(f"  • Aristas de suelo en gama de CAFÉS por estrato")
    print(f"  • Nodos de contacto en AMARILLO brillante")
    print(f"  • Verificación de continuidad de malla")
    print(f"  • Totalmente interactivo (rotar, zoom, pan)")

    print("\n" + "="*70)
    return html_file

if __name__ == '__main__':
    generate_wireframe_viewer()
    print("\n✅ Completado!")
