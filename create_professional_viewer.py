"""
Visualizador Profesional 3D Estilo Abaqus
=========================================
Renderizado de superficies sólidas con calidad profesional
"""

import openseespy.opensees as ops
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry

def extract_element_faces(nodes_coords):
    """
    Extrae las 6 caras de un elemento hexaédrico (brick)

    Parameters:
    -----------
    nodes_coords : array (8, 3)
        Coordenadas de los 8 nodos del elemento

    Returns:
    --------
    faces : list of arrays
        Lista de 6 caras, cada una con 4 vértices
    """
    # Definición de las 6 caras de un hexaedro
    # Cada cara tiene 4 nodos en orden antihorario
    face_indices = [
        [0, 3, 2, 1],  # Cara inferior (z min)
        [4, 5, 6, 7],  # Cara superior (z max)
        [0, 1, 5, 4],  # Cara frontal (y min)
        [2, 3, 7, 6],  # Cara trasera (y max)
        [0, 4, 7, 3],  # Cara izquierda (x min)
        [1, 2, 6, 5],  # Cara derecha (x max)
    ]

    faces = []
    for indices in face_indices:
        face = nodes_coords[indices]
        faces.append(face)

    return faces

def is_external_face(face_center, domain_bounds, tolerance=0.1):
    """
    Determina si una cara está en la superficie externa del dominio

    Parameters:
    -----------
    face_center : array (3,)
        Centro de la cara
    domain_bounds : dict
        Límites del dominio {'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max'}
    tolerance : float
        Tolerancia para determinar si está en el borde

    Returns:
    --------
    bool : True si la cara está en superficie externa
    """
    x, y, z = face_center

    # Verificar si está en algún borde del dominio
    on_boundary = (
        abs(x - domain_bounds['x_min']) < tolerance or
        abs(x - domain_bounds['x_max']) < tolerance or
        abs(y - domain_bounds['y_min']) < tolerance or
        abs(y - domain_bounds['y_max']) < tolerance or
        abs(z - domain_bounds['z_min']) < tolerance or
        abs(z - domain_bounds['z_max']) < tolerance
    )

    return on_boundary

def create_mesh3d_from_faces(faces, color, name, opacity=1.0, show_edges=True):
    """
    Crea un objeto Mesh3d de Plotly a partir de una lista de caras

    Parameters:
    -----------
    faces : list of arrays
        Lista de caras, cada una con 4 vértices
    color : str
        Color de las superficies
    name : str
        Nombre de la traza
    opacity : float
        Opacidad (0-1)
    show_edges : bool
        Mostrar aristas

    Returns:
    --------
    go.Mesh3d : Objeto Mesh3d de Plotly
    """
    # Recopilar todos los vértices
    vertices = []
    triangles_i = []
    triangles_j = []
    triangles_k = []

    vertex_idx = 0
    for face in faces:
        # Cada cara cuadrilateral se divide en 2 triángulos
        # Triángulo 1: vértices 0, 1, 2
        # Triángulo 2: vértices 0, 2, 3

        for i in range(4):
            vertices.append(face[i])

        # Primer triángulo
        triangles_i.append(vertex_idx + 0)
        triangles_j.append(vertex_idx + 1)
        triangles_k.append(vertex_idx + 2)

        # Segundo triángulo
        triangles_i.append(vertex_idx + 0)
        triangles_j.append(vertex_idx + 2)
        triangles_k.append(vertex_idx + 3)

        vertex_idx += 4

    vertices = np.array(vertices)

    # Crear Mesh3d
    mesh = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=triangles_i,
        j=triangles_j,
        k=triangles_k,
        color=color,
        opacity=opacity,
        name=name,
        flatshading=True,  # Sombreado plano para apariencia más técnica
        lighting=dict(
            ambient=0.6,
            diffuse=0.8,
            specular=0.4,
            roughness=0.5,
            fresnel=0.2
        ),
        lightposition=dict(
            x=1000,
            y=1000,
            z=2000
        ),
        hoverinfo='name',
        showlegend=True
    )

    if show_edges:
        mesh.update(
            contour=dict(
                show=True,
                color='rgba(0, 0, 0, 0.3)',
                width=1
            )
        )

    return mesh

def create_professional_viewer(mesh):
    """
    Crea visualización profesional tipo Abaqus con superficies sólidas
    """
    print("\n--- Generando visualización profesional tipo Abaqus ---")

    # Crear subplots para múltiples vistas
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'scene'}, {'type': 'scene'}],
               [{'type': 'scene'}, {'type': 'scene'}]],
        subplot_titles=('Vista Isométrica', 'Vista Frontal (YZ)',
                       'Vista Superior (XY)', 'Vista Lateral (XZ)'),
        vertical_spacing=0.08,
        horizontal_spacing=0.05
    )

    # Colores profesionales tipo Abaqus
    layer_colors = {
        0: 'rgb(139, 90, 43)',    # Marrón tierra
        1: 'rgb(205, 170, 125)',  # Arena clara
        2: 'rgb(244, 200, 150)'   # Arena brillante
    }

    footing_color = 'rgb(180, 180, 180)'  # Gris concreto

    # Límites del dominio
    domain_bounds = {
        'x_min': 0.0,
        'x_max': SOIL_WIDTH_X,
        'y_min': 0.0,
        'y_max': SOIL_WIDTH_Y,
        'z_min': -SOIL_DEPTH,
        'z_max': FREE_SPACE_HEIGHT - EMBEDMENT_DEPTH
    }

    # ==========================================
    # 1. PROCESAR ELEMENTOS DE SUELO
    # ==========================================
    print("  Procesando elementos de suelo...")

    # Recopilar caras externas por estrato
    external_faces_by_layer = {i: [] for i in range(len(SOIL_LAYERS))}

    # Sampling para eficiencia (procesar 1 de cada N elementos)
    sampling = max(1, len(mesh.soil_elements) // 800)

    for idx, (elem_tag, elem_info) in enumerate(mesh.soil_elements.items()):
        if idx % sampling != 0:
            continue

        nodes = elem_info['nodes']
        layer_idx = elem_info['layer']

        # Obtener coordenadas de los 8 nodos
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Extraer las 6 caras del elemento
        faces = extract_element_faces(coords)

        # Determinar cuáles caras son externas
        for face in faces:
            face_center = np.mean(face, axis=0)
            if is_external_face(face_center, domain_bounds):
                external_faces_by_layer[layer_idx].append(face)

    # Crear Mesh3d para cada estrato
    for i, layer in enumerate(SOIL_LAYERS):
        if len(external_faces_by_layer[i]) > 0:
            print(f"  Estrato {i+1}: {len(external_faces_by_layer[i])} caras externas")

            mesh3d = create_mesh3d_from_faces(
                external_faces_by_layer[i],
                layer_colors[i],
                f'Estrato {i+1}: {layer["name"]}',
                opacity=0.95,
                show_edges=True
            )

            # Agregar a las 4 vistas
            for row in range(1, 3):
                for col in range(1, 3):
                    fig.add_trace(mesh3d, row=row, col=col)

    # ==========================================
    # 2. PROCESAR ELEMENTOS DE ZAPATA
    # ==========================================
    print("  Procesando elementos de zapata...")

    footing_faces = []
    for elem in mesh.footing_elements:
        nodes = elem['nodes']
        coords = np.array([mesh.nodes[n] for n in nodes])

        # Extraer todas las caras externas de la zapata
        faces = extract_element_faces(coords)
        for face in faces:
            face_center = np.mean(face, axis=0)
            # Para zapata, considerar todas las caras menos la inferior enterrada
            if face_center[2] > -EMBEDMENT_DEPTH - FOOTING_THICKNESS + 0.05:
                footing_faces.append(face)

    if len(footing_faces) > 0:
        print(f"  Zapata: {len(footing_faces)} caras")

        mesh3d_footing = create_mesh3d_from_faces(
            footing_faces,
            footing_color,
            'Zapata (Concreto)',
            opacity=1.0,
            show_edges=True
        )

        # Agregar a las 4 vistas
        for row in range(1, 3):
            for col in range(1, 3):
                fig.add_trace(mesh3d_footing, row=row, col=col)

    # ==========================================
    # 3. NODOS DE CONTACTO
    # ==========================================
    print("  Procesando nodos de contacto...")

    if mesh.footing_nodes:
        contact_coords = np.array([mesh.nodes[n] for n in mesh.footing_nodes])

        contact_trace = go.Scatter3d(
            x=contact_coords[:, 0],
            y=contact_coords[:, 1],
            z=contact_coords[:, 2],
            mode='markers',
            name='Interfaz Contacto',
            marker=dict(
                size=6,
                color='red',
                symbol='diamond',
                line=dict(color='darkred', width=2)
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

    # Eje X
    axis_x = go.Scatter3d(
        x=[0, SOIL_WIDTH_X],
        y=[0, 0],
        z=[0, 0],
        mode='lines',
        name='Eje Simetría X',
        line=dict(color='blue', width=6, dash='dash'),
        showlegend=True
    )

    # Eje Y
    axis_y = go.Scatter3d(
        x=[0, 0],
        y=[0, SOIL_WIDTH_Y],
        z=[0, 0],
        mode='lines',
        name='Eje Simetría Y',
        line=dict(color='green', width=6, dash='dash'),
        showlegend=True
    )

    for row in range(1, 3):
        for col in range(1, 3):
            fig.add_trace(axis_x, row=row, col=col)
            fig.add_trace(axis_y, row=row, col=col)

    # ==========================================
    # 5. CONFIGURACIÓN DE VISTAS
    # ==========================================

    # Configuración común de ejes
    axis_config = dict(
        backgroundcolor='rgb(245, 245, 245)',
        gridcolor='rgb(200, 200, 200)',
        showbackground=True,
        zerolinecolor='rgb(150, 150, 150)',
    )

    # Configurar las 4 escenas
    fig.update_layout(
        # Vista 1: Isométrica
        scene=dict(
            xaxis=dict(title='X (m)', **axis_config),
            yaxis=dict(title='Y (m)', **axis_config),
            zaxis=dict(title='Z (m)', **axis_config),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                center=dict(x=0, y=0, z=-0.2)
            )
        ),
        # Vista 2: Frontal (YZ)
        scene2=dict(
            xaxis=dict(title='X (m)', **axis_config),
            yaxis=dict(title='Y (m)', **axis_config),
            zaxis=dict(title='Z (m)', **axis_config),
            aspectmode='data',
            camera=dict(
                eye=dict(x=3, y=0, z=0),
                center=dict(x=0, y=0, z=-0.2)
            )
        ),
        # Vista 3: Superior (XY)
        scene3=dict(
            xaxis=dict(title='X (m)', **axis_config),
            yaxis=dict(title='Y (m)', **axis_config),
            zaxis=dict(title='Z (m)', **axis_config),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=0, z=3),
                center=dict(x=0, y=0, z=-0.2)
            )
        ),
        # Vista 4: Lateral (XZ)
        scene4=dict(
            xaxis=dict(title='X (m)', **axis_config),
            yaxis=dict(title='Y (m)', **axis_config),
            zaxis=dict(title='Z (m)', **axis_config),
            aspectmode='data',
            camera=dict(
                eye=dict(x=0, y=3, z=0),
                center=dict(x=0, y=0, z=-0.2)
            )
        )
    )

    # Layout general
    fig.update_layout(
        title=dict(
            text=f'<b>Modelo 3D - Análisis de Ensayo de Carga de Zapata</b><br>' +
                 f'<sub>Zapata {FOOTING_WIDTH}×{FOOTING_LENGTH}m (1/4 modelo) | ' +
                 f'Df={EMBEDMENT_DEPTH}m | {len(mesh.nodes)} nodos | ' +
                 f'{len(mesh.soil_elements)} elementos de suelo</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=18, family='Arial Black')
        ),
        width=1800,
        height=1400,
        showlegend=True,
        legend=dict(
            x=1.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='black',
            borderwidth=2,
            font=dict(size=11, family='Arial')
        ),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    return fig

def generate_professional_html():
    """Genera visualización profesional en HTML"""
    print("="*70)
    print("GENERADOR DE VISUALIZACIÓN PROFESIONAL TIPO ABAQUS")
    print("="*70)

    # Configuración
    print_configuration()

    # Inicializar modelo
    print("\nInicializando modelo...")
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    # Generar malla
    print("\nGenerando malla 1/4...")
    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    print(f"\nEstadísticas:")
    print(f"  Nodos: {len(mesh.nodes)}")
    print(f"  Elementos de suelo: {len(mesh.soil_elements)}")
    print(f"  Elementos de zapata: {len(mesh.footing_elements)}")
    print(f"  Nodos de contacto: {len(mesh.footing_nodes)}")

    # Crear visualización
    fig = create_professional_viewer(mesh)

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
                'filename': 'mesh_visualization',
                'height': 1400,
                'width': 1800,
                'scale': 2
            }
        },
        include_plotlyjs='cdn'
    )

    print(f"\n✅ Visualización profesional generada: {html_file}")
    print(f"\n📖 CARACTERÍSTICAS:")
    print(f"  • Superficies sólidas renderizadas (tipo Abaqus)")
    print(f"  • 4 vistas simultáneas (isométrica, frontal, superior, lateral)")
    print(f"  • Colores profesionales por estrato")
    print(f"  • Iluminación y sombreado realista")
    print(f"  • Aristas visibles en negro")
    print(f"  • Interfaz de contacto destacada")
    print(f"  • Alta resolución y legibilidad")

    print("\n" + "="*70)
    return html_file

if __name__ == '__main__':
    generate_professional_html()
    print("\n✅ Proceso completado!")
