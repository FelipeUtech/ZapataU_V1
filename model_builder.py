"""
Constructor del Modelo Completo
=================================
Integra malla, materiales y condiciones de borde
"""

import openseespy.opensees as ops
import numpy as np
from config import *
from mesh_generator_symmetry import MeshGeneratorSymmetry
from materials import MaterialManager

class ModelBuilder:
    """Clase principal para construir el modelo completo"""

    def __init__(self):
        self.mesh = None
        self.materials = None
        self.load_nodes = []
        self.is_built = False

    def build_model(self):
        """
        Construye el modelo completo paso a paso
        """
        print("\n" + "="*70)
        print("CONSTRUCCIÓN DEL MODELO DE ENSAYO DE CARGA")
        print("="*70)

        # 1. Inicializar OpenSees
        print("\n[1/6] Inicializando modelo OpenSees...")
        ops.wipe()
        ops.model('basic', '-ndm', 3, '-ndf', 3)
        print("  Modelo 3D con 3 grados de libertad por nodo")

        # 2. Generar malla
        print("\n[2/6] Generando malla...")
        self.mesh = MeshGeneratorSymmetry()
        self.mesh.generate_soil_mesh()
        self.mesh.generate_footing_mesh()

        # 3. Aplicar condiciones de borde
        print("\n[3/6] Aplicando condiciones de borde...")
        self.mesh.apply_boundary_conditions()

        # 4. Definir materiales
        print("\n[4/6] Definiendo materiales...")
        self.materials = MaterialManager()
        self.materials.define_all_materials()

        # 5. Crear elementos
        print("\n[5/6] Creando elementos...")
        self.materials.create_soil_elements(self.mesh.soil_elements)
        self.materials.create_footing_elements(self.mesh.footing_elements)

        # 6. Identificar nodos de carga
        print("\n[6/6] Identificando nodos de aplicación de carga...")
        self.load_nodes = self.mesh.get_load_application_nodes()
        print(f"  Nodos donde se aplicará la carga: {len(self.load_nodes)}")

        self.is_built = True

        print("\n" + "="*70)
        print("MODELO CONSTRUIDO EXITOSAMENTE")
        print("="*70)
        self._print_model_summary()

    def _print_model_summary(self):
        """Imprime resumen del modelo"""
        print("\nRESUMEN DEL MODELO:")
        print(f"  Total de nodos: {len(self.mesh.nodes)}")
        print(f"  Total de elementos de suelo: {len(self.mesh.soil_elements)}")
        print(f"  Total de elementos de zapata: {len(self.mesh.footing_elements)}")
        print(f"  Número de estratos: {len(SOIL_LAYERS)}")
        print(f"  Dimensiones de zapata: {FOOTING_WIDTH}m x {FOOTING_LENGTH}m")
        print(f"  Profundidad de desplante: {EMBEDMENT_DEPTH}m")
        print(f"  Dimensiones de dominio: {SOIL_WIDTH_X}m x {SOIL_WIDTH_Y}m x {SOIL_DEPTH}m")

    def get_load_nodes(self):
        """Retorna los nodos donde se aplicará la carga"""
        if not self.is_built:
            raise RuntimeError("El modelo no ha sido construido. Ejecuta build_model() primero.")
        return self.load_nodes

    def get_monitoring_nodes(self):
        """
        Retorna nodos clave para monitoreo durante el análisis

        Returns:
        --------
        dict : Diccionario con nodos de monitoreo
            - 'center': nodo central de la zapata
            - 'corners': nodos en esquinas de zapata
            - 'edges': nodos en bordes laterales
        """
        if not self.is_built:
            raise RuntimeError("El modelo no ha sido construido.")

        # En modelo de simetría 1/4:
        # - Origen (0,0) está en el plano de simetría
        # - Zapata va de (0,0) a (1.0, 1.0) en planta
        if USE_SYMMETRY:
            center_x = FOOTING_WIDTH / 4  # Centro del modelo 1/4
            center_y = FOOTING_LENGTH / 4
            z_top = -EMBEDMENT_DEPTH  # Superficie superior de zapata

            x_min = FOOTING_START_X
            x_max = FOOTING_END_X
            y_min = FOOTING_START_Y
            y_max = FOOTING_END_Y
        else:
            center_x = FOOTING_CENTER_X
            center_y = FOOTING_CENTER_Y
            z_top = -EMBEDMENT_DEPTH

            x_min = FOOTING_CENTER_X - FOOTING_WIDTH / 2
            x_max = FOOTING_CENTER_X + FOOTING_WIDTH / 2
            y_min = FOOTING_CENTER_Y - FOOTING_LENGTH / 2
            y_max = FOOTING_CENTER_Y + FOOTING_LENGTH / 2

        monitoring = {
            'center': None,
            'corners': [],
            'edges': []
        }

        # Buscar nodo más cercano al centro superior
        min_dist = float('inf')
        for node, (x, y, z) in self.mesh.nodes.items():
            if abs(z - z_top) < 0.1:  # Nodos en superficie superior
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    monitoring['center'] = node

        # Buscar nodos en esquinas (solo relevante para modelo completo)
        if USE_SYMMETRY:
            corners = [
                (x_min, y_min), (x_max, y_min),
                (x_max, y_max), (x_min, y_max)
            ]
        else:
            corners = [
                (x_min, y_min), (x_max, y_min),
                (x_max, y_max), (x_min, y_max)
            ]

        for cx, cy in corners:
            min_dist = float('inf')
            corner_node = None
            for node, (x, y, z) in self.mesh.nodes.items():
                if abs(z - z_top) < 0.1:
                    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                    if dist < min_dist:
                        min_dist = dist
                        corner_node = node
            if corner_node and min_dist < 0.5:
                monitoring['corners'].append(corner_node)

        return monitoring

    def export_model_info(self, filename='model_info.txt'):
        """
        Exporta información del modelo a un archivo

        Parameters:
        -----------
        filename : str
            Nombre del archivo de salida
        """
        if not self.is_built:
            raise RuntimeError("El modelo no ha sido construido.")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("INFORMACIÓN DEL MODELO DE ENSAYO DE CARGA\n")
            f.write("="*70 + "\n\n")

            f.write("GEOMETRÍA DE ZAPATA:\n")
            f.write(f"  Ancho (B): {FOOTING_WIDTH} m\n")
            f.write(f"  Largo (L): {FOOTING_LENGTH} m\n")
            f.write(f"  Espesor: {FOOTING_THICKNESS} m\n")
            f.write(f"  Profundidad de desplante (Df): {EMBEDMENT_DEPTH} m\n")
            f.write(f"  Área: {FOOTING_WIDTH * FOOTING_LENGTH} m²\n\n")

            f.write("DOMINIO DE SUELO:\n")
            f.write(f"  Dimensiones: {SOIL_WIDTH_X} x {SOIL_WIDTH_Y} x {SOIL_DEPTH} m\n\n")

            f.write("ESTRATOS DE SUELO:\n")
            for i, layer in enumerate(SOIL_LAYERS):
                f.write(f"\n  Estrato {i+1}: {layer['name']}\n")
                f.write(f"    Profundidad: {layer['depth_top']} - {layer['depth_bottom']} m\n")
                f.write(f"    E = {layer['E']/1000:.1f} MPa\n")
                f.write(f"    ν = {layer['nu']}\n")
                f.write(f"    ρ = {layer['rho']} kg/m³\n")
                f.write(f"    c = {layer['cohesion']} kPa\n")
                f.write(f"    φ = {layer['friction_angle']}°\n")

            f.write("\nMALLA:\n")
            f.write(f"  Total de nodos: {len(self.mesh.nodes)}\n")
            f.write(f"  Elementos de suelo: {len(self.mesh.soil_elements)}\n")
            f.write(f"  Elementos de zapata: {len(self.mesh.footing_elements)}\n")
            f.write(f"  Nodos de aplicación de carga: {len(self.load_nodes)}\n")

            f.write("\nPARÁMETROS DE ENSAYO:\n")
            f.write(f"  Carga máxima: {LOAD_TEST['max_load']} kN\n")
            f.write(f"  Número de incrementos: {LOAD_TEST['num_steps']}\n")

        print(f"\nInformación del modelo exportada a: {filename}")

if __name__ == '__main__':
    # Test de construcción del modelo
    builder = ModelBuilder()
    builder.build_model()
    builder.export_model_info()

    monitoring = builder.get_monitoring_nodes()
    print(f"\nNodos de monitoreo:")
    print(f"  Centro: {monitoring['center']}")
    print(f"  Esquinas: {monitoring['corners']}")
