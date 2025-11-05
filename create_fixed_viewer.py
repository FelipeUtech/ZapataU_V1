"""
Visualizador Profesional 3D con Superficies Continuas
======================================================
Renderizado de superficies unificadas sin efecto de ajedrez
"""

import openseespy.opensees as ops
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def create_unified_surface_mesh(elements_dict, mesh_nodes, layer_idx=None):
    """
    Crea una malla unificada con superficies continuas

    Parameters:
    -----------
    elements_dict : dict
        Diccionario de elementos
    mesh_nodes : dict
        Diccionario de nodos {tag: (x, y, z)}
    layer_idx : int or None
        Índice del estrato a filtrar (None = todos)

    Returns:
    --------
    vertices, i_indices, j_indices, k_indices : arrays
        Datos para Mesh3d
    """

    # Recopilar todas las caras externas
    all_vertices = []
    all_faces = []

    # Límites del dominio
    x_min, x_max = 0.0, SOIL_WIDTH_X
    y_min, y_max = 0.0, SOIL_WIDTH_Y
    z_min, z_max = -SOIL_DEPTH, FREE_SPACE_HEIGHT - EMBEDMENT_DEPTH

    tolerance = 0.1

    # Definición de caras de un hexaedro (brick)
    # Cada cara: 4 nodos en orden que define la normal hacia afuera
    face_definitions = [
        ([0, 3, 2, 1], 'z_min'),   # Cara inferior
        ([4, 5, 6, 7], 'z_max'),   # Cara superior
        ([0, 1, 5, 4], 'y_min'),   # Cara frontal
        ([2, 3, 7, 6], 'y_max'),   # Cara trasera
        ([0, 4, 7, 3], 'x_min'),   # Cara izquierda
        ([1, 2, 6, 5], 'x_max'),   # Cara derecha
    ]

    # Sampling para eficiencia
    items = list(elements_dict.items())
    sampling = max(1, len(items) // 600)

    for idx, (elem_tag, elem_info) in enumerate(items):
        if idx % sampling != 0:
            continue

        # Filtrar por estrato si se especifica
        if layer_idx is not None and elem_info.get('layer') != layer_idx:
            continue

        nodes = elem_info['nodes']
        coords = np.array([mesh_nodes[n] for n in nodes])

        # Verificar cada cara del elemento
        for face_indices, face_type in face_definitions:
            face_coords = coords[face_indices]
            face_center = np.mean(face_coords, axis=0)

            # Determinar si la cara está en borde externo
            is_external = False

            if face_type == 'z_min' and abs(face_center[2] - z_min) < tolerance:
                is_external = True
            elif face_type == 'z_max' and abs(face_center[2] - z_max) < tolerance:
                is_external = True
            elif face_type == 'x_min' and abs(face_center[0] - x_min) < tolerance:
                is_external = True
            elif face_type == 'x_max' and abs(face_center[0] - x_max) < tolerance:
                is_external = True
            elif face_type == 'y_min' and abs(face_center[1] - y_min) < tolerance:
                is_external = True
            elif face_type == 'y_max' and abs(face_center[1] - y_max) < tolerance:
                is_external = True

            if is_external:
                all_faces.append(face_coords)

    if len(all_faces) == 0:
        return None, None, None, None

    # Crear arrays de vértices e índices
    vertices = []
    i_indices = []
    j_indices = []
    k_indices = []

    for face in all_faces:
        base_idx = len(vertices)

        # Agregar los 4 vértices de la cara
        for v in face:
            vertices.append(v)

        # Crear 2 triángulos por cara cuadrilátera
        # Triángulo 1: 0-1-2
        i_indices.append(base_idx + 0)
        j_indices.append(base_idx + 1)
        k_indices.append(base_idx + 2)

        # Triángulo 2: 0-2-3
        i_indices.append(base_idx + 0)
        j_indices.append(base_idx + 2)
        k_indices.append(base_idx + 3)

    vertices = np.array(vertices)

    return vertices, np.array(i_indices), np.array(j_indices), np.array(k_indices)

def create_professional_viewer_fixed(mesh):
    """
    Crea visualización profesional con superficies continuas
    """
    print("\n--- Generando visualización con superficies continuas ---")

    # Crear figura con 4 vistas
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'scene'}, {'type': 'scene'}],
               [{'type': 'scene'}, {'type': 'scene'}]],
        subplot_titles=('Vista Isométrica', 'Vista Frontal',
                       'Vista Superior', 'Vista Lateral'),
        vertical_spacing=0.08,
        horizontal_spacing=0.05
    )

    # Colores profesionales
    layer_colors = {
        0: '#8B5A2B',  # Marrón tierra
        1: '#D2B48C',  # Tan (arena media)
        2: '#F4C896',  # Arena clara
    }

    footing_color = '#B8B8B8'  # Gris concreto

    # ==========================================
    # 1. SUELO - Una malla por estrato
    # ==========================================
    print("  Creando mallas de suelo...")

    for i, layer in enumerate(SOIL_LAYERS):
        print(f"    Estrato {i+1}: {layer['name']}")

        vertices, i_idx, j_idx, k_idx = create_unified_surface_mesh(
            mesh.soil_elements,
            mesh.nodes,
            layer_idx=i
        )

        if vertices is not None and len(vertices) > 0:
            print(f"      {len(vertices)} vértices, {len(i_idx)} triángulos")

            # Crear malla unificada
            mesh_trace = go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=i_idx,
                j=j_idx,
                k=k_idx,
                color=layer_colors[i],
                opacity=0.95,
                name=f'{layer["name"]}',
                flatshading=False,  # Sombreado suave
                lighting=dict(
                    ambient=0.7,
                    diffuse=0.9,
                    specular=0.3,
                    roughness=0.6,
                ),
                lightposition=dict(x=1000, y=1000, z=2000),
                hovertemplate=f'<b>{layer["name"]}</b><br>X: %{{x:.2f}}m<br>Y: %{{y:.2f}}m<br>Z: %{{z:.2f}}m',
                showlegend=True
            )

            # Agregar a todas las vistas
            for row in range(1, 3):
                for col in range(1, 3):
                    fig.add_trace(mesh_trace, row=row, col=col)

    # ==========================================
    # 2. ZAPATA - Malla unificada
    # ==========================================
    print("  Creando malla de zapata...")

    # Convertir footing_elements al formato esperado
    footing_dict = {}
    for elem in mesh.footing_elements:
        footing_dict[elem['tag']] = {'nodes': elem['nodes']}

    vertices, i_idx, j_idx, k_idx = create_unified_surface_mesh(
        footing_dict,
        mesh.nodes,
        layer_idx=None
    )

    if vertices is not None and len(vertices) > 0:
        print(f"    {len(vertices)} vértices, {len(i_idx)} triángulos")

        mesh_footing = go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=i_idx,
            j=j_idx,
            k=k_idx,
            color=footing_color,
            opacity=1.0,
            name='Zapata',
            flatshading=False,
            lighting=dict(
                ambient=0.8,
                diffuse=0.9,
                specular=0.5,
                roughness=0.4,
            ),
            lightposition=dict(x=1000, y=1000, z=2000),
            hovertemplate='<b>Zapata</b><br>X: %{x:.2f}m<br>Y: %{y:.2f}m<br>Z: %{z:.2f}m',
            showlegend=True
        )

        for row in range(1, 3):
            for col in range(1, 3):
                fig.add_trace(mesh_footing, row=row, col=col)

    # ==========================================
    # 3. NODOS DE CONTACTO
    # ==========================================
    print("  Agregando nodos de contacto...")

    if mesh.footing_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in mesh.footing_nodes])

        contact_trace = go.Scatter3d(
            x=contact_coords[:, 0],
            y=contact_coords[:, 1],
            z=contact_coords[:, 2],
            mode='markers',
            name='Interfaz Contacto',
            marker=dict(
                size=5,
                color='red',
                symbol='circle',
                line=dict(color='darkred', width=1)
            ),
            hovertemplate='<b>Contacto</b><br>X: %{x:.2f}m<br>Y: %{y:.2f}m<br>Z: %{z:.2f}m'
        )

        for row in range(1, 3):
            for col in range(1, 3):
                fig.add_trace(contact_trace, row=row, col=col)

    # ==========================================
    # 4. EJES DE SIMETRÍA
    # ==========================================
    print("  Agregando ejes de simetría...")

    axis_x = go.Scatter3d(
        x=[0, SOIL_WIDTH_X], y=[0, 0], z=[0, 0],
        mode='lines',
        name='Simetría X',
        line=dict(color='blue', width=8, dash='dash')
    )

    axis_y = go.Scatter3d(
        x=[0, 0], y=[0, SOIL_WIDTH_Y], z=[0, 0],
        mode='lines',
        name='Simetría Y',
        line=dict(color='green', width=8, dash='dash')
    )

    for row in range(1, 3):
        for col in range(1, 3):
            fig.add_trace(axis_x, row=row, col=col)
            fig.add_trace(axis_y, row=row, col=col)

    # ==========================================
    # 5. CONFIGURACIÓN
    # ==========================================

    axis_config = dict(
        backgroundcolor='rgb(250, 250, 250)',
        gridcolor='rgb(220, 220, 220)',
        showbackground=True,
        zerolinecolor='rgb(180, 180, 180)',
    )

    fig.update_layout(
        # Vista 1: Isométrica
        scene=dict(
            xaxis=dict(title='<b>X (m)</b>', **axis_config),
            yaxis=dict(title='<b>Y (m)</b>', **axis_config),
            zaxis=dict(title='<b>Z (m)</b>', **axis_config),
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        # Vista 2: Frontal
        scene2=dict(
            xaxis=dict(title='<b>X (m)</b>', **axis_config),
            yaxis=dict(title='<b>Y (m)</b>', **axis_config),
            zaxis=dict(title='<b>Z (m)</b>', **axis_config),
            aspectmode='data',
            camera=dict(eye=dict(x=2.5, y=0, z=0))
        ),
        # Vista 3: Superior
        scene3=dict(
            xaxis=dict(title='<b>X (m)</b>', **axis_config),
            yaxis=dict(title='<b>Y (m)</b>', **axis_config),
            zaxis=dict(title='<b>Z (m)</b>', **axis_config),
            aspectmode='data',
            camera=dict(eye=dict(x=0, y=0, z=2.5))
        ),
        # Vista 4: Lateral
        scene4=dict(
            xaxis=dict(title='<b>X (m)</b>', **axis_config),
            yaxis=dict(title='<b>Y (m)</b>', **axis_config),
            zaxis=dict(title='<b>Z (m)</b>', **axis_config),
            aspectmode='data',
            camera=dict(eye=dict(x=0, y=2.5, z=0))
        ),
        title=dict(
            text='<b>Modelo 3D - Análisis de Ensayo de Carga de Zapata (1/4 Simetría)</b><br>' +
                 f'<sub>Zapata {FOOTING_WIDTH}×{FOOTING_LENGTH}m | Df={EMBEDMENT_DEPTH}m | ' +
                 f'{len(mesh.nodes)} nodos | {len(mesh.soil_elements)} elementos</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=18, family='Arial')
        ),
        width=1900,
        height=1200,
        showlegend=True,
        legend=dict(
            x=1.01,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='black',
            borderwidth=2,
            font=dict(size=12)
        ),
        paper_bgcolor='white'
    )

    return fig

def generate_fixed_viewer():
    """Genera visualización corregida"""
    print("="*70)
    print("VISUALIZADOR PROFESIONAL CON SUPERFICIES CONTINUAS")
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
    print(f"  Nodos: {len(mesh.nodes)}")
    print(f"  Elementos suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos zapata: {len(mesh.footing_elements)}")
    print(f"  Contacto: {len(mesh.footing_nodes)}")

    # Crear visualización
    fig = create_professional_viewer_fixed(mesh)

    # Exportar
    html_file = 'mesh_viewer_professional.html'
    print(f"\n  Exportando a {html_file}...")

    fig.write_html(
        html_file,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'mesh_3d',
                'height': 1200,
                'width': 1900,
                'scale': 2
            }
        },
        include_plotlyjs='cdn'
    )

    print(f"\n✅ Visualización generada: {html_file}")
    print(f"\n📖 MEJORAS:")
    print(f"  • Superficies continuas unificadas (sin efecto ajedrez)")
    print(f"  • Sombreado suave para mejor apariencia")
    print(f"  • Colores profesionales por estrato")
    print(f"  • 4 vistas simultáneas")
    print(f"  • Totalmente interactivo")

    print("\n" + "="*70)
    return html_file

if __name__ == '__main__':
    generate_fixed_viewer()
    print("\n✅ Completado!")
