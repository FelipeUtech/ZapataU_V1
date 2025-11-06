#!/usr/bin/env python3
"""
===================================================================================
MÓDULO DE UTILIDADES - ANÁLISIS DE ZAPATAS CON OPENSEESPY
===================================================================================
Funciones auxiliares para generación de mallas, visualización y procesamiento
de resultados.
===================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import openseespy.opensees as ops

# ===================================================================================
# FUNCIONES DE GENERACIÓN DE MALLAS
# ===================================================================================

def geometric_grading(start, end, n_elements, first_size, last_size=None, return_coords=True):
    """
    Genera coordenadas con crecimiento geométrico para mallas graduales.

    Parameters:
    -----------
    start : float
        Coordenada inicial
    end : float
        Coordenada final
    n_elements : int
        Número de elementos deseados
    first_size : float
        Tamaño del primer elemento
    last_size : float, optional
        Tamaño del último elemento (si None, se calcula automáticamente)
    return_coords : bool
        Si True retorna coordenadas, si False retorna tamaños

    Returns:
    --------
    coords : np.array
        Coordenadas de los nodos o tamaños de elementos
    """
    L = abs(end - start)

    if last_size is None:
        # Calcular ratio óptimo para n_elements
        ratio = 1.1  # Valor inicial

        for _ in range(100):  # Iteraciones para converger
            sum_sizes = first_size * (1 - ratio**n_elements) / (1 - ratio)
            if abs(sum_sizes - L) < 1e-6:
                break
            # Ajustar ratio
            if sum_sizes < L:
                ratio += 0.001
            else:
                ratio -= 0.001
    else:
        # Calcular ratio dado first_size y last_size
        ratio = (last_size / first_size) ** (1.0 / (n_elements - 1))

    # Generar tamaños de elementos
    sizes = [first_size * (ratio ** i) for i in range(n_elements)]

    # Normalizar para que sumen exactamente L
    actual_sum = sum(sizes)
    sizes = [s * L / actual_sum for s in sizes]

    if return_coords:
        # Generar coordenadas
        coords = [start]
        for size in sizes:
            coords.append(coords[-1] + size * np.sign(end - start))
        return np.array(coords)
    else:
        return np.array(sizes)


def generar_malla_uniforme(dominio, nx, ny, nz):
    """
    Genera malla uniforme.

    Parameters:
    -----------
    dominio : dict
        {'Lx': float, 'Ly': float, 'Lz': float}
    nx, ny, nz : int
        Número de elementos en cada dirección

    Returns:
    --------
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos en cada dirección
    """
    x_coords = np.linspace(0, dominio['Lx'], nx + 1)
    y_coords = np.linspace(0, dominio['Ly'], ny + 1)
    z_coords = np.linspace(0, -dominio['Lz'], nz + 1)

    return x_coords, y_coords, z_coords


def generar_malla_refinada(dominio, zapata, params):
    """
    Genera malla refinada con zona fina en zapata y gruesa afuera.

    Parameters:
    -----------
    dominio : dict
        {'Lx': float, 'Ly': float, 'Lz': float}
    zapata : dict
        {'B': float, 'L': float}
    params : dict
        Parámetros de malla refinada desde config

    Returns:
    --------
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos en cada dirección
    """
    dx_zapata = params['dx_zapata']
    dx_exterior = params['dx_exterior']
    dz_shallow = params['dz_shallow']
    dz_deep = params['dz_deep']
    depth_transition = params['depth_transition']

    # Coordenadas X (similar para Y si zapata es cuadrada)
    x_zapata = np.arange(0, zapata['B'] + 0.01, dx_zapata)
    x_start_exterior = zapata['B'] + dx_exterior
    x_exterior = np.arange(x_start_exterior, dominio['Lx'] + 0.01, dx_exterior)
    x_coords = np.concatenate([x_zapata, x_exterior])

    # Coordenadas Y
    y_zapata = np.arange(0, zapata['L'] + 0.01, dx_zapata)
    y_start_exterior = zapata['L'] + dx_exterior
    y_exterior = np.arange(y_start_exterior, dominio['Ly'] + 0.01, dx_exterior)
    y_coords = np.concatenate([y_zapata, y_exterior])

    # Coordenadas Z con transición considerando profundidad de desplante Df
    Df = zapata.get('Df', 0.0)  # Profundidad de desplante

    # Zona excavada: desde z=0 hasta z=-Df (no crear nodos/elementos aquí para suelo)
    # Suelo empieza desde z=-Df hacia abajo
    z_shallow = np.arange(-Df, -depth_transition - Df - 0.01, -dz_shallow)
    z_start_deep = -depth_transition - Df - dz_deep
    z_deep = np.arange(z_start_deep, -dominio['Lz'] - 0.01, -dz_deep)
    z_coords = np.concatenate([z_shallow, z_deep])
    z_coords = np.unique(z_coords)[::-1]  # Eliminar duplicados y ordenar

    return x_coords, y_coords, z_coords


def generar_malla_gradual(dominio, zapata, params):
    """
    Genera malla con transición gradual geométrica.

    Parameters:
    -----------
    dominio : dict
        {'Lx': float, 'Ly': float, 'Lz': float}
    zapata : dict
        {'B': float, 'L': float}
    params : dict
        Parámetros de malla gradual desde config

    Returns:
    --------
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos en cada dirección
    """
    dx_min = params['dx_min']
    ratio = params['ratio']

    # Estimar número de elementos necesarios
    # Zona refinada: elementos pequeños cerca de zapata
    n_fine = int(zapata['B'] / dx_min) + 1
    n_coarse = int((dominio['Lx'] - zapata['B']) / (dx_min * ratio**3)) + 1

    # Generar coordenadas con transición geométrica
    x_fine = np.linspace(0, zapata['B'], n_fine)
    x_coarse = geometric_grading(zapata['B'], dominio['Lx'], n_coarse, dx_min * ratio, None, True)
    x_coords = np.concatenate([x_fine, x_coarse[1:]])
    x_coords = np.unique(x_coords)

    # Similar para Y
    n_fine_y = int(zapata['L'] / dx_min) + 1
    n_coarse_y = int((dominio['Ly'] - zapata['L']) / (dx_min * ratio**3)) + 1

    y_fine = np.linspace(0, zapata['L'], n_fine_y)
    y_coarse = geometric_grading(zapata['L'], dominio['Ly'], n_coarse_y, dx_min * ratio, None, True)
    y_coords = np.concatenate([y_fine, y_coarse[1:]])
    y_coords = np.unique(y_coords)

    # Coordenadas Z con transición
    dz_surface = params['dz_surface']
    dz_deep = params['dz_deep']
    depth_transition = params['depth_transition']

    # Agregar planos para zapata considerando profundidad de desplante Df
    h_zapata = zapata.get('h', 0.4)  # Altura de zapata
    Df = zapata.get('Df', 0.0)  # Profundidad de desplante (0 = superficial)

    # Zapata enterrada a profundidad Df:
    # - Tope de zapata en z = -Df
    # - Base de zapata en z = -Df - h_zapata
    z_zapata_top = -Df
    z_zapata_bottom = -Df - h_zapata

    # Planos de la zapata
    z_zapata = np.array([z_zapata_bottom, z_zapata_top])

    # Capas de suelo: desde z=-Df (base de excavación) hacia abajo
    # No crear nodos/elementos en zona excavada (0 a -Df)
    z_shallow = np.arange(z_zapata_top, -depth_transition - Df - 0.01, -dz_surface)
    z_start_deep = -depth_transition - Df - dz_deep
    z_deep = np.arange(z_start_deep, -dominio['Lz'] - 0.01, -dz_deep)
    z_soil = np.concatenate([z_shallow, z_deep])
    z_soil = np.unique(z_soil)

    # Combinar zapata y suelo
    z_coords = np.concatenate([z_zapata, z_soil[1:]])  # Excluir z=-Df duplicado
    z_coords = np.unique(z_coords)[::-1]  # Ordenar descendente

    return x_coords, y_coords, z_coords


# ===================================================================================
# FUNCIONES DE CREACIÓN DE MODELO
# ===================================================================================

def crear_nodos(x_coords, y_coords, z_coords):
    """
    Crea nodos en OpenSeesPy basado en coordenadas.

    Parameters:
    -----------
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos

    Returns:
    --------
    node_coords : dict
        Diccionario {nodeTag: (x, y, z)}
    surface_nodes : list
        Lista de nodos en superficie (z=0 o z=max)
    """
    nodeCounter = 1
    node_coords = {}
    surface_nodes = []

    # Encontrar el índice de z máximo (superficie)
    z_max_idx = 0  # Asumiendo que z_coords está ordenado descendente

    for k, z in enumerate(z_coords):
        for j, y in enumerate(y_coords):
            for i, x in enumerate(x_coords):
                ops.node(nodeCounter, x, y, z)
                node_coords[nodeCounter] = (x, y, z)

                if k == z_max_idx:
                    surface_nodes.append(nodeCounter)

                nodeCounter += 1

    return node_coords, surface_nodes


def identificar_nodos_zapata(surface_nodes, node_coords, zapata):
    """
    Identifica nodos bajo la zapata.

    Parameters:
    -----------
    surface_nodes : list
        Lista de nodos en superficie
    node_coords : dict
        Diccionario de coordenadas de nodos
    zapata : dict
        {'B': float, 'L': float, 'x_min': float, 'y_min': float}

    Returns:
    --------
    zapata_nodes : list
        Lista de nodos bajo la zapata
    """
    zapata_nodes = []
    x_min = zapata.get('x_min', 0.0)
    y_min = zapata.get('y_min', 0.0)
    x_max = x_min + zapata['B']
    y_max = y_min + zapata['L']

    for node in surface_nodes:
        x, y, z = node_coords[node]
        if x_min <= x <= x_max and y_min <= y <= y_max:
            zapata_nodes.append(node)

    return zapata_nodes


def identificar_nodos_en_cota(node_coords, z_target, zapata, tolerancia=0.01):
    """
    Identifica nodos en una cota z específica dentro del área de la zapata.

    Parameters:
    -----------
    node_coords : dict
        Diccionario de coordenadas de nodos {nodeTag: (x, y, z)}
    z_target : float
        Cota z donde buscar nodos
    zapata : dict
        {'B': float, 'L': float, 'x_min': float, 'y_min': float}
    tolerancia : float
        Tolerancia para buscar nodos cerca de z_target

    Returns:
    --------
    nodos_encontrados : list
        Lista de nodos en la cota especificada
    """
    nodos_encontrados = []
    x_min = zapata.get('x_min', 0.0)
    y_min = zapata.get('y_min', 0.0)
    x_max = x_min + zapata['B']
    y_max = y_min + zapata['L']

    for node_tag, (x, y, z) in node_coords.items():
        # Verificar si está en la cota z correcta y dentro del área de zapata
        if (abs(z - z_target) < tolerancia and
            x_min <= x <= x_max and
            y_min <= y <= y_max):
            nodos_encontrados.append(node_tag)

    return nodos_encontrados


def aplicar_condiciones_borde(n_layers, nodes_per_layer, nx, ny, usar_simetria=False):
    """
    Aplica condiciones de borde al modelo.

    Parameters:
    -----------
    n_layers : int
        Número de capas en Z
    nodes_per_layer : int
        Nodos por capa
    nx, ny : int
        Número de elementos en X e Y
    usar_simetria : bool
        Si True, aplica condiciones de simetría
    """
    # Fijar base (última capa)
    base_nodes = list(range(nodes_per_layer * (n_layers - 1) + 1, nodes_per_layer * n_layers + 1))
    for node in base_nodes:
        ops.fix(node, 1, 1, 1)

    if usar_simetria:
        # Condiciones de simetría
        for k in range(n_layers):
            current_layer = k * nodes_per_layer

            # Plano x=0 (simetría)
            for j in range(ny + 1):
                node_tag = current_layer + j * (nx + 1) + 1
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 1, 0, 0)

            # Plano y=0 (simetría)
            for i in range(nx + 1):
                node_tag = current_layer + i + 1
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 0, 1, 0)
    else:
        # Rodillos en bordes laterales
        for k in range(n_layers):
            current_layer = k * nodes_per_layer

            # Bordes X
            for j in range(ny + 1):
                # x = 0
                node_tag = current_layer + j * (nx + 1) + 1
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 1, 0, 0)
                # x = Lx
                node_tag = current_layer + j * (nx + 1) + (nx + 1)
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 1, 0, 0)

            # Bordes Y
            for i in range(nx + 1):
                # y = 0
                node_tag = current_layer + i + 1
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 0, 1, 0)
                # y = Ly
                node_tag = current_layer + ny * (nx + 1) + i + 1
                if node_tag not in base_nodes:
                    ops.fix(node_tag, 0, 1, 0)


def crear_elementos(nx, ny, nz, nodes_per_layer, mat_tag=1):
    """
    Crea elementos brick8 en OpenSeesPy.

    Parameters:
    -----------
    nx, ny, nz : int
        Número de elementos en cada dirección
    nodes_per_layer : int
        Nodos por capa
    mat_tag : int
        Tag del material

    Returns:
    --------
    n_elements : int
        Número total de elementos creados
    """
    element_counter = 1

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                node1 = 1 + i + j * (nx + 1) + k * nodes_per_layer
                node2 = node1 + 1
                node3 = node2 + nx + 1
                node4 = node3 - 1
                node5 = node1 + nodes_per_layer
                node6 = node2 + nodes_per_layer
                node7 = node3 + nodes_per_layer
                node8 = node4 + nodes_per_layer

                ops.element('stdBrick', element_counter, node1, node2, node3, node4,
                           node5, node6, node7, node8, mat_tag)
                element_counter += 1

    return element_counter - 1


def crear_elementos_con_zapata(nx, ny, nz, nodes_per_layer, x_coords, y_coords, z_coords,
                                 zapata, mat_tag_zapata=2, estratos_suelo=None, mat_tag_suelo=1):
    """
    Crea elementos brick8 diferenciando zapata rígida y estratos de suelo.

    Parameters:
    -----------
    nx, ny, nz : int
        Número de elementos en cada dirección
    nodes_per_layer : int
        Nodos por capa
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos
    zapata : dict
        Geometría de zapata {'B', 'L', 'h'}
    mat_tag_zapata : int
        Tag del material de la zapata
    estratos_suelo : list of dict
        Lista de estratos con 'espesor' y mat_tag. Si None, usa mat_tag_suelo único
    mat_tag_suelo : int
        Tag del material del suelo (si estratos_suelo es None)

    Returns:
    --------
    n_elements_suelo : int (o list)
        Número de elementos de suelo creados (por estrato si estratos_suelo)
    n_elements_zapata : int
        Número de elementos de zapata creados
    """
    element_counter = 1
    n_elements_zapata = 0

    # Obtener profundidad de desplante
    Df = zapata.get('Df', 0.0)

    # Calcular límites de estratos (desde z=-Df hacia abajo, no desde z=0)
    # Los estratos empiezan desde el fondo de la excavación
    if estratos_suelo:
        limites_estratos = []
        z_acum = -Df  # Empezar desde base de excavación
        for estrato in estratos_suelo:
            z_sup = z_acum
            z_inf = z_acum - estrato['espesor']
            limites_estratos.append({
                'z_sup': z_sup,
                'z_inf': z_inf,
                'mat_tag': estrato['mat_tag']
            })
            z_acum = z_inf
        n_elements_por_estrato = [0] * len(estratos_suelo)
    else:
        n_elements_suelo = 0

    h_zapata = zapata['h']
    B_zapata = zapata['B']
    L_zapata = zapata['L']
    Df = zapata.get('Df', 0.0)  # Profundidad de desplante

    # Zapata enterrada: tope en z=-Df, base en z=-Df-h
    z_zapata_top = -Df
    z_zapata_bottom = -Df - h_zapata

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                # Calcular nodos del elemento
                node1 = 1 + i + j * (nx + 1) + k * nodes_per_layer
                node2 = node1 + 1
                node3 = node2 + nx + 1
                node4 = node3 - 1
                node5 = node1 + nodes_per_layer
                node6 = node2 + nodes_per_layer
                node7 = node3 + nodes_per_layer
                node8 = node4 + nodes_per_layer

                # Coordenadas del centro del elemento
                x_elem = (x_coords[i] + x_coords[i+1]) / 2.0
                y_elem = (y_coords[j] + y_coords[j+1]) / 2.0
                z_elem = (z_coords[k] + z_coords[k+1]) / 2.0

                # Determinar si el elemento está en la zona de zapata
                # Zapata va desde z=-Df (tope) hasta z=-Df-h (base)
                es_zapata = (x_elem <= B_zapata and y_elem <= L_zapata and
                            z_zapata_bottom <= z_elem <= z_zapata_top)

                if es_zapata:
                    mat_tag = mat_tag_zapata
                    n_elements_zapata += 1
                else:
                    # Determinar material según estrato (basado en z_elem)
                    if estratos_suelo:
                        # Buscar en qué estrato está el elemento
                        mat_tag = mat_tag_suelo  # default
                        for idx, limite in enumerate(limites_estratos):
                            if limite['z_inf'] <= z_elem <= limite['z_sup']:
                                mat_tag = limite['mat_tag']
                                n_elements_por_estrato[idx] += 1
                                break
                    else:
                        mat_tag = mat_tag_suelo
                        n_elements_suelo += 1

                ops.element('stdBrick', element_counter, node1, node2, node3, node4,
                           node5, node6, node7, node8, mat_tag)
                element_counter += 1

    if estratos_suelo:
        return n_elements_por_estrato, n_elements_zapata
    else:
        return n_elements_suelo, n_elements_zapata


# ===================================================================================
# FUNCIONES DE ANÁLISIS Y RESULTADOS
# ===================================================================================

def aplicar_cargas(zapata_nodes, P_column, zapata_geom, material_zapata, incluir_peso_propio=True):
    """
    Aplica cargas a los nodos de la zapata.

    Parameters:
    -----------
    zapata_nodes : list
        Nodos bajo la zapata
    P_column : float
        Carga de columna (kN)
    zapata_geom : dict
        Geometría de zapata {'B', 'L', 'h'}
    material_zapata : dict
        Material zapata {'rho'}
    incluir_peso_propio : bool
        Si incluir peso propio de zapata

    Returns:
    --------
    carga_total : float
        Carga total aplicada (kN)
    """
    # Calcular peso propio
    if incluir_peso_propio:
        volumen = zapata_geom['B'] * zapata_geom['L'] * zapata_geom['h']
        peso_zapata = volumen * material_zapata['rho'] * 9.81 / 1000  # kN
    else:
        peso_zapata = 0.0

    carga_total = P_column + peso_zapata

    # Distribuir carga en nodos
    carga_por_nodo = -carga_total / len(zapata_nodes)  # Negativa (hacia abajo)

    for node in zapata_nodes:
        ops.load(node, 0.0, 0.0, carga_por_nodo)

    return carga_total


def extraer_asentamientos(node_coords):
    """
    Extrae asentamientos de todos los nodos.

    Parameters:
    -----------
    node_coords : dict
        Diccionario de coordenadas de nodos

    Returns:
    --------
    df : pd.DataFrame
        DataFrame con columnas ['X', 'Y', 'Z', 'Settlement_mm']
    """
    data = []

    for node_tag, (x, y, z) in node_coords.items():
        try:
            disp_z = ops.nodeDisp(node_tag, 3)  # Desplazamiento en Z
            settlement_mm = abs(disp_z * 1000)  # Convertir a mm
            data.append([x, y, z, settlement_mm])
        except:
            pass

    df = pd.DataFrame(data, columns=['X', 'Y', 'Z', 'Settlement_mm'])
    return df


def generar_reporte(datos_modelo, datos_resultados, archivo_salida):
    """
    Genera reporte de texto con resumen del análisis.

    Parameters:
    -----------
    datos_modelo : dict
        Información del modelo
    datos_resultados : dict
        Resultados del análisis
    archivo_salida : str
        Nombre del archivo de salida
    """
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE ANÁLISIS DE ZAPATA\n")
        f.write("=" * 80 + "\n\n")

        f.write("MODELO:\n")
        for key, value in datos_modelo.items():
            f.write(f"  {key}: {value}\n")

        f.write("\nRESULTADOS:\n")
        for key, value in datos_resultados.items():
            f.write(f"  {key}: {value}\n")

        f.write("\n" + "=" * 80 + "\n")

    print(f"✓ Reporte guardado en: {archivo_salida}")


# ===================================================================================
# FUNCIONES DE VISUALIZACIÓN
# ===================================================================================

def plot_surface_settlements(df_surface, zapata, archivo_salida=None):
    """
    Grafica mapa de contornos de asentamientos en superficie.

    Parameters:
    -----------
    df_surface : pd.DataFrame
        DataFrame con asentamientos en superficie
    zapata : dict
        Geometría de zapata
    archivo_salida : str, optional
        Nombre de archivo para guardar
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Crear grid para contornos
    x = df_surface['X'].values
    y = df_surface['Y'].values
    z = df_surface['Settlement_mm'].values

    scatter = ax.tricontourf(x, y, z, levels=20, cmap='jet')
    plt.colorbar(scatter, label='Asentamiento (mm)')

    # Marcar zapata
    B = zapata['B']
    L = zapata['L']
    x_min = zapata.get('x_min', 0.0)
    y_min = zapata.get('y_min', 0.0)

    ax.add_patch(plt.Rectangle((x_min, y_min), B, L,
                               fill=False, edgecolor='red', linewidth=2, label='Zapata'))

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Mapa de Asentamientos en Superficie')
    ax.legend()
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    if archivo_salida:
        plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfica guardada: {archivo_salida}")

    plt.show()


def plot_3d_model(x_coords, y_coords, z_coords, zapata, archivo_salida=None):
    """
    Grafica vista 3D del modelo.

    Parameters:
    -----------
    x_coords, y_coords, z_coords : np.array
        Coordenadas de nodos
    zapata : dict
        Geometría de zapata
    archivo_salida : str, optional
        Nombre de archivo para guardar
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Graficar malla de nodos
    X, Y = np.meshgrid(x_coords, y_coords)
    for z in z_coords[::2]:  # Cada 2 niveles para no saturar
        ax.plot_wireframe(X, Y, np.full_like(X, z), alpha=0.2, color='gray')

    # Marcar zapata
    B = zapata['B']
    L = zapata['L']
    x_min = zapata.get('x_min', 0.0)
    y_min = zapata.get('y_min', 0.0)

    x_zap = [x_min, x_min + B, x_min + B, x_min, x_min]
    y_zap = [y_min, y_min, y_min + L, y_min + L, y_min]
    z_zap = [0, 0, 0, 0, 0]

    ax.plot(x_zap, y_zap, z_zap, 'r-', linewidth=3, label='Zapata')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title('Vista Isométrica del Modelo')
    ax.legend()

    if archivo_salida:
        plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
        print(f"✓ Gráfica guardada: {archivo_salida}")

    plt.show()
