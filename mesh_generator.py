"""
Generador de Malla 3D para Ensayo de Carga de Zapata
======================================================
Crea malla refinada bajo la zapata y malla más gruesa en zonas alejadas
"""

import openseespy.opensees as ops
import numpy as np
from config import *

class MeshGenerator:
    """Clase para generar malla 3D de suelo y zapata"""

    def __init__(self):
        self.nodes = {}  # Diccionario {node_tag: (x, y, z)}
        self.soil_elements = {}  # {elem_tag: [nodes], layer_index}
        self.footing_elements = []  # Lista de tags de elementos de zapata
        self.footing_nodes = []  # Lista de nodos en contacto con zapata
        self.node_counter = 1
        self.element_counter = 1

    def generate_soil_mesh(self):
        """
        Genera malla 3D del suelo con refinamiento bajo la zapata
        """
        print("\n--- Generando malla de suelo ---")

        # Calcular límites de la zapata
        x_foot_min = FOOTING_CENTER_X - FOOTING_WIDTH / 2
        x_foot_max = FOOTING_CENTER_X + FOOTING_WIDTH / 2
        y_foot_min = FOOTING_CENTER_Y - FOOTING_LENGTH / 2
        y_foot_max = FOOTING_CENTER_Y + FOOTING_LENGTH / 2
        z_foot = -EMBEDMENT_DEPTH

        # Generar coordenadas en X (con refinamiento bajo zapata)
        x_coords = self._generate_refined_coords(
            0, SOIL_WIDTH_X,
            x_foot_min, x_foot_max,
            NX_LATERAL, NX_UNDER_FOOTING
        )

        # Generar coordenadas en Y (con refinamiento bajo zapata)
        y_coords = self._generate_refined_coords(
            0, SOIL_WIDTH_Y,
            y_foot_min, y_foot_max,
            NY_LATERAL, NY_UNDER_FOOTING
        )

        # Generar coordenadas en Z (desde superficie hasta profundidad total)
        z_coords = self._generate_depth_coords(0, -SOIL_DEPTH, NZ_UNDER_FOOTING + NZ_DEEP)

        print(f"  Nodos en X: {len(x_coords)}")
        print(f"  Nodos en Y: {len(y_coords)}")
        print(f"  Nodos en Z: {len(z_coords)}")

        # Crear nodos
        node_map = {}  # Mapeo (i,j,k) -> node_tag

        for k, z in enumerate(z_coords):
            for j, y in enumerate(y_coords):
                for i, x in enumerate(x_coords):
                    ops.node(self.node_counter, x, y, z)
                    self.nodes[self.node_counter] = (x, y, z)
                    node_map[(i, j, k)] = self.node_counter
                    self.node_counter += 1

        print(f"  Total de nodos creados: {self.node_counter - 1}")

        # Crear elementos de suelo
        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1

        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Obtener los 8 nodos del elemento brick
                    n1 = node_map[(i, j, k)]
                    n2 = node_map[(i+1, j, k)]
                    n3 = node_map[(i+1, j+1, k)]
                    n4 = node_map[(i, j+1, k)]
                    n5 = node_map[(i, j, k+1)]
                    n6 = node_map[(i+1, j, k+1)]
                    n7 = node_map[(i+1, j+1, k+1)]
                    n8 = node_map[(i, j+1, k+1)]

                    # Determinar el estrato de este elemento
                    z_center = (z_coords[k] + z_coords[k+1]) / 2
                    layer_index = get_layer_at_depth(z_center)

                    # Guardar información del elemento
                    self.soil_elements[self.element_counter] = {
                        'nodes': [n1, n2, n3, n4, n5, n6, n7, n8],
                        'layer': layer_index
                    }

                    self.element_counter += 1

        print(f"  Total de elementos de suelo: {len(self.soil_elements)}")

        # Identificar nodos en la superficie donde irá la zapata
        self._identify_footing_contact_nodes(x_foot_min, x_foot_max,
                                            y_foot_min, y_foot_max,
                                            z_foot, x_coords, y_coords, z_coords)

        return x_coords, y_coords, z_coords, node_map

    def generate_footing_mesh(self):
        """
        Genera malla de la zapata
        """
        print("\n--- Generando malla de zapata ---")

        # Coordenadas de la zapata
        x_min = FOOTING_CENTER_X - FOOTING_WIDTH / 2
        x_max = FOOTING_CENTER_X + FOOTING_WIDTH / 2
        y_min = FOOTING_CENTER_Y - FOOTING_LENGTH / 2
        y_max = FOOTING_CENTER_Y + FOOTING_LENGTH / 2
        z_bottom = -EMBEDMENT_DEPTH
        z_top = z_bottom + FOOTING_THICKNESS

        # Discretización
        x_footing = np.linspace(x_min, x_max, NX_FOOTING + 1)
        y_footing = np.linspace(y_min, y_max, NY_FOOTING + 1)
        z_footing = np.linspace(z_bottom, z_top, NZ_FOOTING + 1)

        # Crear nodos de la zapata
        footing_node_map = {}

        for k, z in enumerate(z_footing):
            for j, y in enumerate(y_footing):
                for i, x in enumerate(x_footing):
                    # Si está en la base de la zapata, ya existen nodos del suelo
                    if k == 0:
                        # Buscar nodo existente más cercano
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

        print(f"  Nodos de zapata creados: {len(footing_node_map)}")
        print(f"  Elementos de zapata: {len(self.footing_elements)}")

    def _generate_refined_coords(self, x_min, x_max, refine_min, refine_max,
                                n_coarse, n_refined):
        """
        Genera coordenadas con refinamiento en una región específica
        """
        coords = []

        # Región izquierda (gruesa)
        if x_min < refine_min:
            coords.extend(np.linspace(x_min, refine_min, n_coarse + 1)[:-1])

        # Región refinada
        coords.extend(np.linspace(refine_min, refine_max, n_refined + 1)[:-1])

        # Región derecha (gruesa)
        if refine_max < x_max:
            coords.extend(np.linspace(refine_max, x_max, n_coarse + 1))
        else:
            coords.append(x_max)

        return np.array(coords)

    def _generate_depth_coords(self, z_top, z_bottom, n_elements):
        """
        Genera coordenadas en profundidad (más refinado cerca de superficie)
        """
        # Usar distribución senoidal para refinamiento cerca de superficie
        theta = np.linspace(0, np.pi/2, n_elements + 1)
        normalized = np.sin(theta)
        z_coords = z_top + (z_bottom - z_top) * normalized
        return z_coords

    def _identify_footing_contact_nodes(self, x_min, x_max, y_min, y_max, z_foot,
                                       x_coords, y_coords, z_coords):
        """
        Identifica nodos en contacto con la zapata
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

    def apply_boundary_conditions(self):
        """
        Aplica condiciones de borde al modelo
        """
        print("\n--- Aplicando condiciones de borde ---")

        # Fijar base (z mínimo)
        z_min = min(coord[2] for coord in self.nodes.values())
        base_nodes = [tag for tag, coord in self.nodes.items()
                     if abs(coord[2] - z_min) < 0.01]

        for node in base_nodes:
            ops.fix(node, 1, 1, 1)  # Fijo en x, y, z

        print(f"  Nodos fijos en la base: {len(base_nodes)}")

        # Bordes laterales con rodillos (permitir desplazamiento vertical)
        x_min = min(coord[0] for coord in self.nodes.values())
        x_max = max(coord[0] for coord in self.nodes.values())
        y_min = min(coord[1] for coord in self.nodes.values())
        y_max = max(coord[1] for coord in self.nodes.values())

        lateral_nodes = []
        for node, (x, y, z) in self.nodes.items():
            if node in base_nodes:
                continue
            if (abs(x - x_min) < 0.01 or abs(x - x_max) < 0.01 or
                abs(y - y_min) < 0.01 or abs(y - y_max) < 0.01):
                ops.fix(node, 1, 1, 0)  # Fijo en x, y, libre en z
                lateral_nodes.append(node)

        print(f"  Nodos con rodillos laterales: {len(lateral_nodes)}")

    def get_load_application_nodes(self):
        """
        Retorna los nodos donde se aplicará la carga (superficie de zapata)
        """
        # Nodos en la superficie superior de la zapata
        z_max = max(coord[2] for tag, coord in self.nodes.items()
                   if any(elem['nodes'].count(tag) for elem in self.footing_elements if 'nodes' in elem))

        load_nodes = [tag for tag, coord in self.nodes.items()
                     if abs(coord[2] - z_max) < 0.01 and
                     any(tag in elem['nodes'] for elem in self.footing_elements)]

        return load_nodes

if __name__ == '__main__':
    # Test de generación de malla
    print_configuration()

    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    mesh = MeshGenerator()
    mesh.generate_soil_mesh()
    mesh.generate_footing_mesh()
    mesh.apply_boundary_conditions()

    load_nodes = mesh.get_load_application_nodes()
    print(f"\nNodos para aplicación de carga: {len(load_nodes)}")
    print(f"Total de nodos en el modelo: {len(mesh.nodes)}")
    print(f"Total de elementos de suelo: {len(mesh.soil_elements)}")
    print(f"Total de elementos de zapata: {len(mesh.footing_elements)}")
