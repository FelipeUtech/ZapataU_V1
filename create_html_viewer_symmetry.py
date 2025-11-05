"""
Visor Interactivo 3D en HTML para Modelo 1/4 con Simetría
===========================================================
Muestra superficies de zapata, interfaces entre estratos y ejes de simetría
"""

import openseespy.opensees as ops
import numpy as np
import plotly.graph_objects as go
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def create_footing_surfaces(mesh):
    """
    Crea superficies externas de la zapata en gris
    """
    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    if not footing_node_tags:
        return []

    # Obtener coordenadas de nodos de zapata
    footing_coords = {tag: mesh.nodes[tag] for tag in footing_node_tags}

    # Identificar caras externas de la zapata
    surfaces = []

    # Cara superior (z máximo)
    z_max = max(coord[2] for coord in footing_coords.values())
    top_nodes = [tag for tag, (x, y, z) in footing_coords.items()
                 if abs(z - z_max) < 0.01]

    if top_nodes:
        top_coords = np.array([footing_coords[n] for n in top_nodes])
        surfaces.append({
            'name': 'Superficie superior zapata',
            'coords': top_coords,
            'color': 'lightgray',
            'opacity': 0.9
        })

    # Caras laterales en X=0, Y=0, X=max, Y=max
    x_min = min(coord[0] for coord in footing_coords.values())
    x_max = max(coord[0] for coord in footing_coords.values())
    y_min = min(coord[1] for coord in footing_coords.values())
    y_max = max(coord[1] for coord in footing_coords.values())

    tolerance = 0.01

    # Cara X=0 (simetría)
    x0_nodes = [tag for tag, (x, y, z) in footing_coords.items()
                if abs(x - x_min) < tolerance]
    if x0_nodes:
        x0_coords = np.array([footing_coords[n] for n in x0_nodes])
        surfaces.append({
            'name': 'Cara zapata X=0',
            'coords': x0_coords,
            'color': 'gray',
            'opacity': 0.7
        })

    # Cara Y=0 (simetría)
    y0_nodes = [tag for tag, (x, y, z) in footing_coords.items()
                if abs(y - y_min) < tolerance]
    if y0_nodes:
        y0_coords = np.array([footing_coords[n] for n in y0_nodes])
        surfaces.append({
            'name': 'Cara zapata Y=0',
            'coords': y0_coords,
            'color': 'gray',
            'opacity': 0.7
        })

    # Cara X=max
    xmax_nodes = [tag for tag, (x, y, z) in footing_coords.items()
                  if abs(x - x_max) < tolerance]
    if xmax_nodes:
        xmax_coords = np.array([footing_coords[n] for n in xmax_nodes])
        surfaces.append({
            'name': 'Cara zapata X=max',
            'coords': xmax_coords,
            'color': 'darkgray',
            'opacity': 0.8
        })

    # Cara Y=max
    ymax_nodes = [tag for tag, (x, y, z) in footing_coords.items()
                  if abs(y - y_max) < tolerance]
    if ymax_nodes:
        ymax_coords = np.array([footing_coords[n] for n in ymax_nodes])
        surfaces.append({
            'name': 'Cara zapata Y=max',
            'coords': ymax_coords,
            'color': 'darkgray',
            'opacity': 0.8
        })

    return surfaces

def create_stratum_interfaces(mesh):
    """
    Crea superficies de contacto entre estratos
    """
    interfaces = []

    # Para cada límite entre estratos
    for i in range(len(SOIL_LAYERS) - 1):
        z_interface = -SOIL_LAYERS[i]['depth_bottom']

        # Buscar nodos cercanos a esta profundidad
        interface_nodes = []
        for tag, (x, y, z) in mesh.nodes.items():
            if abs(z - z_interface) < 0.2:  # Tolerancia
                interface_nodes.append([x, y, z])

        if interface_nodes:
            interface_coords = np.array(interface_nodes)
            interfaces.append({
                'name': f'Interfaz Estrato {i+1}-{i+2}',
                'coords': interface_coords,
                'z': z_interface,
                'layer_top': i,
                'layer_bottom': i + 1
            })

    return interfaces

def create_interactive_viewer_symmetry(mesh):
    """
    Crea visualización interactiva 3D del modelo 1/4
    """
    print("\n--- Generando visor interactivo 3D (modelo 1/4) ---")

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

    sampling_rate = max(1, len(mesh.soil_elements) // 400)
    soil_elements_list = list(mesh.soil_elements.items())
    sampled_elements = soil_elements_list[::sampling_rate]

    edges_by_layer = {i: {'x': [], 'y': [], 'z': []} for i in range(len(SOIL_LAYERS))}

    for elem_tag, elem_info in sampled_elements:
        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']
        coords = np.array([mesh.nodes[n] for n in nodes])

        edge_indices = [
            [0, 1], [1, 2], [2, 3], [3, 0],
            [4, 5], [5, 6], [6, 7], [7, 4],
            [0, 4], [1, 5], [2, 6], [3, 7]
        ]

        for edge in edge_indices:
            p1, p2 = coords[edge[0]], coords[edge[1]]
            edges_by_layer[layer_idx]['x'].extend([p1[0], p2[0], None])
            edges_by_layer[layer_idx]['y'].extend([p1[1], p2[1], None])
            edges_by_layer[layer_idx]['z'].extend([p1[2], p2[2], None])

    for i, layer in enumerate(SOIL_LAYERS):
        fig.add_trace(go.Scatter3d(
            x=edges_by_layer[i]['x'],
            y=edges_by_layer[i]['y'],
            z=edges_by_layer[i]['z'],
            mode='lines',
            name=f'Estrato {i+1}: {layer["name"]}',
            line=dict(color=layer_colors[i], width=0.8),
            opacity=0.15,
            hoverinfo='name'
        ))

    # ==========================================
    # 2. SUPERFICIES DE LA ZAPATA (GRIS)
    # ==========================================
    print("  Creando superficies de zapata...")

    footing_surfaces = create_footing_surfaces(mesh)

    for surface in footing_surfaces:
        coords = surface['coords']
        fig.add_trace(go.Mesh3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            alphahull=0,
            color=surface['color'],
            opacity=surface['opacity'],
            name=surface['name'],
            hoverinfo='name'
        ))

    # ==========================================
    # 3. INTERFACES ENTRE ESTRATOS
    # ==========================================
    print("  Creando interfaces entre estratos...")

    interfaces = create_stratum_interfaces(mesh)

    interface_colors = ['red', 'orange']
    for idx, interface in enumerate(interfaces):
        coords = interface['coords']
        fig.add_trace(go.Scatter3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            mode='markers',
            name=interface['name'],
            marker=dict(size=2, color=interface_colors[idx % len(interface_colors)],
                       symbol='square'),
            opacity=0.6,
            hovertemplate=f"<b>{interface['name']}</b><br>Z={interface['z']:.2f} m<br>X: %{{x:.2f}}<br>Y: %{{y:.2f}}"
        ))

    # ==========================================
    # 4. NODOS (MÁS PEQUEÑOS)
    # ==========================================
    print("  Procesando nodos...")

    footing_node_tags = set()
    for elem in mesh.footing_elements:
        footing_node_tags.update(elem['nodes'])

    contact_nodes = set(mesh.footing_nodes)

    # Nodos de contacto (diamantes amarillos)
    if contact_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in contact_nodes])
        fig.add_trace(go.Scatter3d(
            x=contact_coords[:, 0],
            y=contact_coords[:, 1],
            z=contact_coords[:, 2],
            mode='markers',
            name='⭐ Nodos CONTACTO',
            marker=dict(size=4, color='yellow', symbol='diamond',
                       line=dict(color='black', width=1)),
            hovertemplate='<b>CONTACTO Suelo-Zapata</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.2f}'
        ))

    # ==========================================
    # 5. EJES DE SIMETRÍA
    # ==========================================
    print("  Agregando ejes de simetría...")

    # Eje X (Y=0, Z=0)
    fig.add_trace(go.Scatter3d(
        x=[0, SOIL_WIDTH_X],
        y=[0, 0],
        z=[0, 0],
        mode='lines',
        name='Eje simetría X',
        line=dict(color='blue', width=4, dash='dash'),
        hoverinfo='name'
    ))

    # Eje Y (X=0, Z=0)
    fig.add_trace(go.Scatter3d(
        x=[0, 0],
        y=[0, SOIL_WIDTH_Y],
        z=[0, 0],
        mode='lines',
        name='Eje simetría Y',
        line=dict(color='green', width=4, dash='dash'),
        hoverinfo='name'
    ))

    # Plano XY en z=0 (superficie)
    surface_x = [0, SOIL_WIDTH_X, SOIL_WIDTH_X, 0]
    surface_y = [0, 0, SOIL_WIDTH_Y, SOIL_WIDTH_Y]
    surface_z = [0, 0, 0, 0]

    fig.add_trace(go.Mesh3d(
        x=surface_x,
        y=surface_y,
        z=surface_z,
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color='lightblue',
        opacity=0.1,
        name='Superficie terreno',
        hoverinfo='name'
    ))

    # ==========================================
    # 6. CONFIGURACIÓN
    # ==========================================

    fig.update_layout(
        title={
            'text': f'<b>Modelo 1/4 con Simetría - Malla de Ensayo de Carga</b><br>' +
                   f'<sub>Zapata {FOOTING_WIDTH}×{FOOTING_LENGTH}m (total) | ' +
                   f'Modelo: {FOOTING_END_X}×{FOOTING_END_Y}m | Df={EMBEDMENT_DEPTH}m | ' +
                   f'{len(mesh.nodes)} nodos | {len(mesh.soil_elements)} elem. suelo</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='rgb(240, 240,240)',
                      gridcolor='white', showbackground=True,
                      range=[0, SOIL_WIDTH_X]),
            yaxis=dict(title='Y (m)', backgroundcolor='rgb(240, 240,240)',
                      gridcolor='white', showbackground=True,
                      range=[0, SOIL_WIDTH_Y]),
            zaxis=dict(title='Z (m)', backgroundcolor='rgb(240, 240,240)',
                      gridcolor='white', showbackground=True,
                      range=[-SOIL_DEPTH, FREE_SPACE_HEIGHT]),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.0),
                center=dict(x=0, y=0, z=-0.3)
            )
        ),
        width=1600,
        height=1000,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='black',
            borderwidth=1,
            font=dict(size=10)
        ),
        hovermode='closest'
    )

    return fig

def generate_html_viewer_symmetry():
    """Genera el archivo HTML completo para modelo 1/4"""
    print("="*70)
    print("GENERANDO VISOR INTERACTIVO HTML 3D - MODELO 1/4")
    print("="*70)

    # Configuración
    print_configuration()

    # Inicializar modelo
    print("\nInicializando modelo OpenSees...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    # Generar malla
    print("\nGenerando malla 1/4...")
    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    # Estadísticas
    print(f"\nEstadísticas del modelo 1/4:")
    print(f"  Nodos totales: {len(mesh.nodes)}")
    print(f"  Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos de zapata: {len(mesh.footing_elements)}")
    print(f"  Nodos de contacto: {len(mesh.footing_nodes)}")

    # Crear visualización
    fig = create_interactive_viewer_symmetry(mesh)

    # Exportar a HTML
    html_file = 'mesh_viewer_3d_symmetry.html'
    print(f"\n  Exportando a {html_file}...")

    fig.write_html(
        html_file,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['toImage'],
        },
        include_plotlyjs='cdn'
    )

    print(f"\n✅ Visor HTML generado: {html_file}")
    print(f"\n📖 CARACTERÍSTICAS:")
    print(f"  • Modelo 1/4 con simetría en X=0 y Y=0")
    print(f"  • Superficies de zapata en gris")
    print(f"  • Interfaces entre estratos marcadas")
    print(f"  • Nodos de contacto destacados")
    print(f"  • Espacio libre sobre zapata visible")
    print(f"\n📖 CONTROLES:")
    print(f"  • Rotar: Click izquierdo + arrastrar")
    print(f"  • Zoom: Rueda del mouse")
    print(f"  • Pan: Click derecho + arrastrar")
    print(f"  • Click en leyenda para mostrar/ocultar elementos")

    print("\n" + "="*70)

    return html_file

if __name__ == '__main__':
    generate_html_viewer_symmetry()
    print("\n✅ Proceso completado!")
