"""
Generador de Malla 3D para Modelo 1/4 con Simetría
===================================================
Crea malla de 1/4 con condiciones de simetría y espacio libre sobre zapata
"""

import openseespy.opensees as ops
import numpy as np
from config import *

class MeshGeneratorSymmetry:
    """Clase para generar malla 3D con simetría 1/4"""

    def __init__(self):
        self.nodes = {}  # Diccionario {node_tag: (x, y, z)}
        self.soil_elements = {}  # {elem_tag: {'nodes': [nodes], 'layer': layer_index}}
        self.footing_elements = []  # Lista de elementos de zapata
        self.footing_nodes = []  # Nodos en contacto suelo-zapata
        self.node_counter = 1
        self.element_counter = 1

    def generate_soil_mesh(self):
        """
        Genera malla 3D del suelo (modelo 1/4)
        Dominio: X=[0, SOIL_WIDTH_X], Y=[0, SOIL_WIDTH_Y], Z=[-SOIL_DEPTH, 0]
        """
        print("\n--- Generando malla de suelo (modelo 1/4) ---")

        # Límites de la zapata
        x_foot_min = FOOTING_START_X
        x_foot_max = FOOTING_END_X
        y_foot_min = FOOTING_START_Y
        y_foot_max = FOOTING_END_Y
        z_foot = -EMBEDMENT_DEPTH

        # Generar coordenadas en X (refinamiento bajo zapata)
        x_coords = self._generate_refined_coords_1d(
            0, SOIL_WIDTH_X,
            x_foot_min, x_foot_max,
            NX_LATERAL, NX_UNDER_FOOTING
        )

        # Generar coordenadas en Y (refinamiento bajo zapata)
        y_coords = self._generate_refined_coords_1d(
            0, SOIL_WIDTH_Y,
            y_foot_min, y_foot_max,
            NY_LATERAL, NY_UNDER_FOOTING
        )

        # Generar coordenadas en Z (superficie hasta profundidad total)
        z_coords = self._generate_depth_coords(0, -SOIL_DEPTH, NZ_UNDER_FOOTING + NZ_DEEP)

        print(f"  Nodos en X: {len(x_coords)}")
        print(f"  Nodos en Y: {len(y_coords)}")
        print(f"  Nodos en Z: {len(z_coords)}")

        # Crear nodos (excluyendo la zona encima de la zapata)
        node_map = {}  # Mapeo (i,j,k) -> node_tag
        z_footing_bottom = -EMBEDMENT_DEPTH - FOOTING_THICKNESS
        z_surface = 0.0

        for k, z in enumerate(z_coords):
            for j, y in enumerate(y_coords):
                for i, x in enumerate(x_coords):
                    # Verificar si el nodo está en la zona encima de la zapata
                    in_footing_x = (x >= x_foot_min and x <= x_foot_max)
                    in_footing_y = (y >= y_foot_min and y <= y_foot_max)
                    in_footing_z = (z >= z_footing_bottom and z <= z_surface)

                    # No crear nodo si está en la zona de la zapata o encima
                    if in_footing_x and in_footing_y and in_footing_z:
                        continue

                    ops.node(self.node_counter, x, y, z)
                    self.nodes[self.node_counter] = (x, y, z)
                    node_map[(i, j, k)] = self.node_counter
                    self.node_counter += 1

        print(f"  Total de nodos de suelo creados: {self.node_counter - 1}")

        # Crear elementos de suelo
        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1

        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Calcular centro del elemento
                    x_elem_center = (x_coords[i] + x_coords[i+1]) / 2
                    y_elem_center = (y_coords[j] + y_coords[j+1]) / 2
                    z_elem_center = (z_coords[k] + z_coords[k+1]) / 2

                    # Verificar si el elemento está en la zona de la zapata o encima de ella
                    # Eliminar elementos desde el fondo de la zapata hasta la superficie
                    z_footing_bottom = -EMBEDMENT_DEPTH - FOOTING_THICKNESS
                    z_surface = 0.0

                    in_footing_x = (x_elem_center >= x_foot_min and x_elem_center <= x_foot_max)
                    in_footing_y = (y_elem_center >= y_foot_min and y_elem_center <= y_foot_max)
                    in_footing_z = (z_elem_center >= z_footing_bottom and z_elem_center <= z_surface)

                    # Si el elemento está en la zona de la zapata o encima, no crearlo
                    if in_footing_x and in_footing_y and in_footing_z:
                        continue

                    # Verificar que todos los 8 nodos del elemento existan
                    node_indices = [
                        (i, j, k), (i+1, j, k), (i+1, j+1, k), (i, j+1, k),
                        (i, j, k+1), (i+1, j, k+1), (i+1, j+1, k+1), (i, j+1, k+1)
                    ]

                    # Si algún nodo no existe, no crear el elemento
                    if not all(idx in node_map for idx in node_indices):
                        continue

                    # Obtener los 8 nodos del elemento brick
                    n1 = node_map[(i, j, k)]
                    n2 = node_map[(i+1, j, k)]
                    n3 = node_map[(i+1, j+1, k)]
                    n4 = node_map[(i, j+1, k)]
                    n5 = node_map[(i, j, k+1)]
                    n6 = node_map[(i+1, j, k+1)]
                    n7 = node_map[(i+1, j+1, k+1)]
                    n8 = node_map[(i, j+1, k+1)]

                    # Determinar el estrato
                    layer_index = get_layer_at_depth(z_elem_center)

                    # Guardar información del elemento
                    self.soil_elements[self.element_counter] = {
                        'nodes': [n1, n2, n3, n4, n5, n6, n7, n8],
                        'layer': layer_index
                    }

                    self.element_counter += 1

        print(f"  Total de elementos de suelo: {len(self.soil_elements)}")

        # Identificar nodos en contacto
        self._identify_footing_contact_nodes(x_foot_min, x_foot_max,
                                            y_foot_min, y_foot_max,
                                            z_foot, x_coords, y_coords, z_coords)

        return x_coords, y_coords, z_coords, node_map

    def generate_footing_mesh(self):
        """
        Genera malla de la zapata (modelo 1/4)
        La zapata va desde (0,0,-Df-t) hasta (B/2, L/2, -Df)
        Con espacio libre desde z=-Df hasta z=FREE_SPACE_HEIGHT-Df
        """
        print("\n--- Generando malla de zapata (modelo 1/4) ---")

        # Coordenadas de la zapata
        x_min = FOOTING_START_X
        x_max = FOOTING_END_X
        y_min = FOOTING_START_Y
        y_max = FOOTING_END_Y
        z_bottom = -EMBEDMENT_DEPTH - FOOTING_THICKNESS
        z_top = -EMBEDMENT_DEPTH

        print(f"  Zapata en X: [{x_min}, {x_max}] m")
        print(f"  Zapata en Y: [{y_min}, {y_max}] m")
        print(f"  Zapata en Z: [{z_bottom}, {z_top}] m")
        print(f"  Espacio libre: [{z_top}, {z_top + FREE_SPACE_HEIGHT}] m")

        # Discretización
        x_footing = np.linspace(x_min, x_max, NX_FOOTING + 1)
        y_footing = np.linspace(y_min, y_max, NY_FOOTING + 1)
        z_footing = np.linspace(z_bottom, z_top, NZ_FOOTING + 1)

        # Crear nodos de la zapata
        footing_node_map = {}

        for k, z in enumerate(z_footing):
            for j, y in enumerate(y_footing):
                for i, x in enumerate(x_footing):
                    # Si está en la base (z=z_top), conectar con nodos existentes del suelo
                    if k == NZ_FOOTING:  # Superior de zapata
                        existing_node = self._find_nearest_node(x, y, z)
                        if existing_node:
                            footing_node_map[(i, j, k)] = existing_node
                            continue

                    ops.node(self.node_counter, x, y, z)
                    self.nodes[self.node_counter] = (x, y, z)
                    footing_node_map[(i, j, k)] = self.node_counter
                    self.node_counter += 1

        # Crear elementos de la zapata
        for k in range(NZ_FOOTING):
            for j in range(NY_FOOTING):
                for i in range(NX_FOOTING):
                    n1 = footing_node_map[(i, j, k)]
                    n2 = footing_node_map[(i+1, j, k)]
                    n3 = footing_node_map[(i+1, j+1, k)]
                    n4 = footing_node_map[(i, j+1, k)]
                    n5 = footing_node_map[(i, j, k+1)]
                    n6 = footing_node_map[(i+1, j, k+1)]
                    n7 = footing_node_map[(i+1, j+1, k+1)]
                    n8 = footing_node_map[(i, j+1, k+1)]

                    self.footing_elements.append({
                        'tag': self.element_counter,
                        'nodes': [n1, n2, n3, n4, n5, n6, n7, n8]
                    })

                    self.element_counter += 1

        print(f"  Nodos totales (suelo + zapata): {len(self.nodes)}")
        print(f"  Elementos de zapata: {len(self.footing_elements)}")

    def apply_boundary_conditions(self):
        """
        Aplica condiciones de borde al modelo 1/4
        - Base fija (z mínimo)
        - Bordes X=SOIL_WIDTH_X y Y=SOIL_WIDTH_Y con rodillos
        - SIMETRÍA en X=0 y Y=0
        """
        print("\n--- Aplicando condiciones de borde ---")

        tolerance = 0.01

        # 1. Fijar base (z mínimo)
        z_min = min(coord[2] for coord in self.nodes.values())
        base_nodes = [tag for tag, (x, y, z) in self.nodes.items()
                     if abs(z - z_min) < tolerance]

        for node in base_nodes:
            ops.fix(node, 1, 1, 1)  # Fijo en x, y, z

        print(f"  Nodos fijos en la base (z={z_min:.2f}): {len(base_nodes)}")

        # 2. Identificar nodos en esquina X=0, Y=0 (necesitan ambas restricciones)
        corner_nodes = set()
        for tag, (x, y, z) in self.nodes.items():
            if abs(x - 0.0) < tolerance and abs(y - 0.0) < tolerance and tag not in base_nodes:
                corner_nodes.add(tag)

        # 3. Condiciones de SIMETRÍA en X=0 (restringir desplazamiento en X)
        symmetry_x_nodes = [tag for tag, (x, y, z) in self.nodes.items()
                           if abs(x - 0.0) < tolerance and tag not in base_nodes]

        for node in symmetry_x_nodes:
            if node in corner_nodes:
                # Nodos en esquina: restringir X e Y
                ops.fix(node, 1, 1, 0)
            else:
                # Solo en plano X=0: restringir solo X
                ops.fix(node, 1, 0, 0)

        print(f"  Nodos de simetría en X=0: {len(symmetry_x_nodes)} (incluye {len(corner_nodes)} en esquina)")

        # 4. Condiciones de SIMETRÍA en Y=0 (restringir desplazamiento en Y)
        # Excluir nodos ya procesados en esquina
        symmetry_y_nodes = [tag for tag, (x, y, z) in self.nodes.items()
                           if abs(y - 0.0) < tolerance and tag not in base_nodes and tag not in corner_nodes]

        for node in symmetry_y_nodes:
            ops.fix(node, 0, 1, 0)  # Restringir Y, libres X y Z

        print(f"  Nodos de simetría en Y=0: {len(symmetry_y_nodes)}")

        # 5. Bordes laterales (X=max y Y=max) con rodillos
        x_max = max(coord[0] for coord in self.nodes.values())
        y_max = max(coord[1] for coord in self.nodes.values())

        constrained_nodes = set(base_nodes) | set(symmetry_x_nodes) | set(symmetry_y_nodes)

        lateral_nodes = []
        for node, (x, y, z) in self.nodes.items():
            if node in constrained_nodes:
                continue
            if abs(x - x_max) < tolerance or abs(y - y_max) < tolerance:
                ops.fix(node, 1, 1, 0)  # Fijo en X e Y, libre en Z
                lateral_nodes.append(node)

        print(f"  Nodos con rodillos laterales: {len(lateral_nodes)}")

    def _generate_refined_coords_1d(self, start, end, refine_start, refine_end,
                                    n_coarse, n_refined):
        """
        Genera coordenadas 1D con refinamiento en una región

        Parameters:
        -----------
        start, end : float
            Inicio y fin del dominio
        refine_start, refine_end : float
            Inicio y fin de la región refinada
        n_coarse : int
            Número de elementos fuera de zona refinada
        n_refined : int
            Número de elementos en zona refinada
        """
        coords = []

        # Región refinada (zapata)
        coords_refined = np.linspace(refine_start, refine_end, n_refined + 1)
        coords.extend(coords_refined[:-1])

        # Región lateral (desde fin de zapata hasta fin de dominio)
        if refine_end < end:
            coords_lateral = np.linspace(refine_end, end, n_coarse + 1)
            coords.extend(coords_lateral)
        else:
            coords.append(end)

        return np.array(coords)

    def _generate_depth_coords(self, z_top, z_bottom, n_elements):
        """
        Genera coordenadas en profundidad con refinamiento cerca de superficie
        """
        theta = np.linspace(0, np.pi/2, n_elements + 1)
        normalized = np.sin(theta)
        z_coords = z_top + (z_bottom - z_top) * normalized
        return z_coords

    def _identify_footing_contact_nodes(self, x_min, x_max, y_min, y_max, z_foot,
                                       x_coords, y_coords, z_coords):
        """
        Identifica nodos en la interfaz suelo-zapata
        """
        tolerance = 0.1
        z_surface_idx = np.argmin(np.abs(z_coords - z_foot))

        for node_tag, (x, y, z) in self.nodes.items():
            if (abs(z - z_coords[z_surface_idx]) < tolerance and
                x_min <= x <= x_max and y_min <= y <= y_max):
                self.footing_nodes.append(node_tag)

        print(f"  Nodos de contacto suelo-zapata: {len(self.footing_nodes)}")

    def _find_nearest_node(self, x, y, z, tolerance=0.1):
        """
        Busca el nodo más cercano a las coordenadas dadas
        """
        for node_tag, (nx, ny, nz) in self.nodes.items():
            dist = np.sqrt((x-nx)**2 + (y-ny)**2 + (z-nz)**2)
            if dist < tolerance:
                return node_tag
        return None

    def get_load_application_nodes(self):
        """
        Retorna los nodos donde se aplicará la carga (superficie superior de zapata)
        """
        # Encontrar z máximo de la zapata
        footing_node_tags = set()
        for elem in self.footing_elements:
            footing_node_tags.update(elem['nodes'])

        if not footing_node_tags:
            return []

        footing_coords = [self.nodes[n] for n in footing_node_tags]
        z_max = max(coord[2] for coord in footing_coords)

        load_nodes = [tag for tag in footing_node_tags
                     if abs(self.nodes[tag][2] - z_max) < 0.01]

        return load_nodes

if __name__ == '__main__':
    # Test de generación de malla
    print_configuration()

    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    mesh = MeshGeneratorSymmetry()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    load_nodes = mesh.get_load_application_nodes()
    print(f"\nNodos para aplicación de carga: {len(load_nodes)}")
    print(f"Total de nodos en el modelo: {len(mesh.nodes)}")
    print(f"Total de elementos de suelo: {len(mesh.soil_elements)}")
    print(f"Total de elementos de zapata: {len(mesh.footing_elements)}")
