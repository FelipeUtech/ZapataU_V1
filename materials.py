"""
Definición de Materiales No Lineales
=====================================
Define materiales constitutivos para suelo y zapata
"""

import openseespy.opensees as ops
import numpy as np
from config import *

class MaterialManager:
    """Clase para gestionar materiales del modelo"""

    def __init__(self):
        self.soil_material_tags = {}  # {layer_index: material_tag}
        self.footing_material_tag = None

    def define_soil_materials(self):
        """
        Define materiales no lineales para cada estrato de suelo
        Utiliza modelo Drucker-Prager
        """
        print("\n--- Definiendo materiales de suelo ---")

        for i, layer in enumerate(SOIL_LAYERS):
            mat_tag = i + 1

            E = layer['E']
            nu = layer['nu']
            rho = layer['rho']
            cohesion = layer['cohesion']
            friction_angle = layer['friction_angle']

            # Calcular parámetros de Drucker-Prager
            # K = E / (3 * (1 - 2*nu))  # Módulo volumétrico
            # G = E / (2 * (1 + nu))      # Módulo de corte

            # Convertir ángulo de fricción a radianes
            phi_rad = np.radians(friction_angle)

            # Parámetros de Drucker-Prager
            # alpha y k relacionados con cohesión y fricción
            # Para aproximación de Mohr-Coulomb:
            # alpha = (2*sin(phi)) / (sqrt(3)*(3-sin(phi)))
            # k = (6*c*cos(phi)) / (sqrt(3)*(3-sin(phi)))

            alpha = (2 * np.sin(phi_rad)) / (np.sqrt(3) * (3 - np.sin(phi_rad)))
            k = (6 * cohesion * np.cos(phi_rad)) / (np.sqrt(3) * (3 - np.sin(phi_rad)))

            # Usar modelo DruckerPrager3D
            # Sintaxis: nDMaterial('DruckerPrager', matTag, K, G, sigma_y, rho, rho_bar,
            #                      K_inf, delta, H, theta, density, atm_pressure)

            # Calcular módulos
            K = E / (3.0 * (1.0 - 2.0 * nu))
            G = E / (2.0 * (1.0 + nu))

            try:
                # Intentar usar DruckerPrager
                ops.nDMaterial('DruckerPrager', mat_tag, K, G,
                             alpha,      # alpha
                             k,          # k (cohesión)
                             rho)        # densidad

                print(f"  Estrato {i+1} ({layer['name']}): Material DruckerPrager")
                print(f"    Tag: {mat_tag}, K={K:.1f} kPa, G={G:.1f} kPa")
                print(f"    alpha={alpha:.4f}, k={k:.1f} kPa")

            except:
                # Si DruckerPrager no está disponible, usar ElasticIsotropic
                print(f"  ADVERTENCIA: DruckerPrager no disponible")
                print(f"  Usando ElasticIsotropic para estrato {i+1}")

                # No pasar rho para evitar problemas de unidades
                ops.nDMaterial('ElasticIsotropic', mat_tag, E, nu)

                print(f"  Estrato {i+1} ({layer['name']}): Material ElasticIsotropic")
                print(f"    Tag: {mat_tag}, E={E/1000:.1f} MPa, nu={nu}")

            self.soil_material_tags[i] = mat_tag

        return self.soil_material_tags

    def define_footing_material(self):
        """
        Define material elástico para la zapata (concreto)
        """
        print("\n--- Definiendo material de zapata ---")

        mat_tag = len(SOIL_LAYERS) + 1

        E = FOOTING_MATERIAL['E']
        nu = FOOTING_MATERIAL['nu']
        rho = FOOTING_MATERIAL['rho']

        ops.nDMaterial('ElasticIsotropic', mat_tag, E, nu, rho)

        self.footing_material_tag = mat_tag

        print(f"  Concreto: Material ElasticIsotropic")
        print(f"    Tag: {mat_tag}")
        print(f"    E = {E/1e6:.1f} GPa")
        print(f"    nu = {nu}")
        print(f"    rho = {rho} kg/m³")

        return mat_tag

    def create_soil_elements(self, soil_elements_dict):
        """
        Crea elementos de suelo con sus respectivos materiales

        Parameters:
        -----------
        soil_elements_dict : dict
            Diccionario con información de elementos {elem_tag: {'nodes': [...], 'layer': i}}
        """
        print("\n--- Creando elementos de suelo ---")

        elem_count_by_layer = {i: 0 for i in range(len(SOIL_LAYERS))}

        for elem_tag, elem_info in soil_elements_dict.items():
            nodes = elem_info['nodes']
            layer_index = elem_info['layer']
            mat_tag = self.soil_material_tags[layer_index]

            # Crear elemento brick de 8 nodos
            # Sintaxis: element('stdBrick', eleTag, *eleNodes, matTag)
            ops.element('stdBrick', elem_tag, *nodes, mat_tag)

            elem_count_by_layer[layer_index] += 1

        print("  Elementos creados por estrato:")
        for i, count in elem_count_by_layer.items():
            print(f"    Estrato {i+1} ({SOIL_LAYERS[i]['name']}): {count} elementos")

    def create_footing_elements(self, footing_elements_list):
        """
        Crea elementos de la zapata

        Parameters:
        -----------
        footing_elements_list : list
            Lista de diccionarios con información de elementos
        """
        print("\n--- Creando elementos de zapata ---")

        for elem_info in footing_elements_list:
            elem_tag = elem_info['tag']
            nodes = elem_info['nodes']

            ops.element('stdBrick', elem_tag, *nodes, self.footing_material_tag)

        print(f"  Total elementos de zapata creados: {len(footing_elements_list)}")

    def define_all_materials(self):
        """Define todos los materiales del modelo"""
        self.define_soil_materials()
        self.define_footing_material()

def calculate_drucker_prager_params(cohesion, friction_angle_deg):
    """
    Calcula parámetros de Drucker-Prager desde cohesión y ángulo de fricción

    Parameters:
    -----------
    cohesion : float
        Cohesión (kPa)
    friction_angle_deg : float
        Ángulo de fricción interna (grados)

    Returns:
    --------
    alpha, k : floats
        Parámetros del modelo Drucker-Prager
    """
    phi = np.radians(friction_angle_deg)

    # Aproximación de Mohr-Coulomb a Drucker-Prager
    alpha = (2 * np.sin(phi)) / (np.sqrt(3) * (3 - np.sin(phi)))
    k = (6 * cohesion * np.cos(phi)) / (np.sqrt(3) * (3 - np.sin(phi)))

    return alpha, k

def print_material_info():
    """Imprime información de los materiales"""
    print("\n" + "="*60)
    print("MATERIALES DEL MODELO")
    print("="*60)

    print("\nESTRATOS DE SUELO:")
    for i, layer in enumerate(SOIL_LAYERS):
        print(f"\n  Estrato {i+1}: {layer['name']}")
        print(f"    Profundidad: {layer['depth_top']} - {layer['depth_bottom']} m")
        print(f"    E = {layer['E']/1000:.1f} MPa")
        print(f"    ν = {layer['nu']}")
        print(f"    ρ = {layer['rho']} kg/m³")
        print(f"    c = {layer['cohesion']} kPa")
        print(f"    φ = {layer['friction_angle']}°")

        alpha, k = calculate_drucker_prager_params(layer['cohesion'],
                                                   layer['friction_angle'])
        print(f"    Drucker-Prager: α = {alpha:.4f}, k = {k:.2f} kPa")

    print("\nZAPATA (CONCRETO):")
    print(f"    E = {FOOTING_MATERIAL['E']/1e6:.1f} GPa")
    print(f"    ν = {FOOTING_MATERIAL['nu']}")
    print(f"    ρ = {FOOTING_MATERIAL['rho']} kg/m³")

    print("="*60)

if __name__ == '__main__':
    print_material_info()
