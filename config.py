"""
Configuración del modelo de ensayo de carga de zapata
========================================================
Define todos los parámetros geométricos, de materiales y de análisis
"""

import numpy as np

# =============================
# GEOMETRÍA DE LA ZAPATA
# =============================
FOOTING_WIDTH = 2.0      # Ancho de la zapata B (m) - TOTAL (modelo completo)
FOOTING_LENGTH = 2.0     # Largo de la zapata L (m) - TOTAL (modelo completo)
FOOTING_THICKNESS = 0.5  # Espesor de la zapata (m)
EMBEDMENT_DEPTH = 1.5    # Profundidad de desplante Df (m)

# =============================
# MODELO DE SIMETRÍA (1/4)
# =============================
USE_SYMMETRY = True      # Usar modelo de 1/4 con simetría
SYMMETRY_PLANES = ['X', 'Y']  # Planos de simetría en X=0 y Y=0

# =============================
# GEOMETRÍA DEL DOMINIO DE SUELO
# =============================
# Dominio de 1/4 (por simetría)
# El modelo va desde (0,0) hasta (SOIL_WIDTH_X, SOIL_WIDTH_Y)
SOIL_WIDTH_X = 10.0      # Ancho del dominio 1/4 en X (m)
SOIL_WIDTH_Y = 10.0      # Ancho del dominio 1/4 en Y (m)
SOIL_DEPTH = 15.0        # Profundidad total del suelo (m)

# Espacio libre sobre la zapata
FREE_SPACE_HEIGHT = 0.5  # Altura del espacio libre sobre zapata (m)

# Posición de la zapata (en esquina por simetría)
# La zapata empieza en (0, 0) y se extiende a (FOOTING_WIDTH/2, FOOTING_LENGTH/2)
FOOTING_START_X = 0.0
FOOTING_START_Y = 0.0
FOOTING_END_X = FOOTING_WIDTH / 2.0   # 1.0 m
FOOTING_END_Y = FOOTING_LENGTH / 2.0  # 1.0 m

# =============================
# DISCRETIZACIÓN DE LA MALLA
# =============================
# Zona debajo de la zapata (malla refinada) - Modelo 1/4
# Elementos rectangulares: más pequeños en X,Y y más alargados en Z
NX_UNDER_FOOTING = 5     # Elementos en X bajo zapata (1/4 modelo)
NY_UNDER_FOOTING = 5     # Elementos en Y bajo zapata (1/4 modelo)
NZ_UNDER_FOOTING = 15    # Elementos en Z bajo zapata (más alargados verticalmente)

# Zona lateral (malla más gruesa) - Modelo 1/4
NX_LATERAL = 9           # Elementos desde borde de zapata hasta límite en X
NY_LATERAL = 9           # Elementos desde borde de zapata hasta límite en Y
NZ_DEEP = 10             # Elementos en profundidad (zona profunda)

# Discretización de la zapata - Modelo 1/4
NX_FOOTING = 5           # Elementos en X de la zapata (1/4 modelo)
NY_FOOTING = 5           # Elementos en Y de la zapata (1/4 modelo)
NZ_FOOTING = 3           # Elementos en Z de la zapata (más capas)

# =============================
# ESTRATOS DE SUELO
# =============================
# Cada estrato se define como un diccionario con:
# - 'depth': profundidad desde la superficie (m)
# - 'E': Módulo de Young (kPa)
# - 'nu': Coeficiente de Poisson
# - 'rho': Densidad (kg/m³)
# - 'cohesion': Cohesión (kPa)
# - 'friction_angle': Ángulo de fricción (grados)
# - 'name': Nombre del estrato

SOIL_LAYERS = [
    {
        'name': 'Arcilla blanda',
        'depth_top': 0.0,      # Profundidad superior (m)
        'depth_bottom': 3.0,   # Profundidad inferior (m)
        'E': 10000.0,          # Módulo de Young (kPa)
        'nu': 0.35,            # Coeficiente de Poisson
        'rho': 1700.0,         # Densidad (kg/m³)
        'cohesion': 25.0,      # Cohesión (kPa)
        'friction_angle': 15.0,# Ángulo de fricción (grados)
    },
    {
        'name': 'Arena limosa',
        'depth_top': 3.0,
        'depth_bottom': 8.0,
        'E': 30000.0,
        'nu': 0.30,
        'rho': 1900.0,
        'cohesion': 5.0,
        'friction_angle': 30.0,
    },
    {
        'name': 'Arena densa',
        'depth_top': 8.0,
        'depth_bottom': 15.0,
        'E': 50000.0,
        'nu': 0.28,
        'rho': 2000.0,
        'cohesion': 0.0,
        'friction_angle': 38.0,
    }
]

# =============================
# MATERIAL DE LA ZAPATA
# =============================
FOOTING_MATERIAL = {
    'E': 25e6,              # Módulo de Young del concreto (kPa) - 25 GPa
    'nu': 0.20,             # Coeficiente de Poisson
    'rho': 2400.0,          # Densidad del concreto (kg/m³)
}

# =============================
# PARÁMETROS DEL ENSAYO DE CARGA
# =============================
LOAD_TEST = {
    'max_load': 1000.0,     # Carga máxima a aplicar (kN)
    'num_steps': 20,        # Número de incrementos de carga
    'load_type': 'vertical',# Tipo de carga: 'vertical', 'inclined'
    'settlement_tolerance': 0.5,  # Tolerancia de convergencia (mm)
}

# =============================
# PARÁMETROS DE ANÁLISIS
# =============================
ANALYSIS = {
    'analysis_type': 'static',  # 'static' o 'transient'
    'max_iterations': 100,       # Máximo número de iteraciones
    'tolerance': 1.0e-6,         # Tolerancia de convergencia
    'algorithm': 'Newton',       # 'Newton', 'ModifiedNewton', 'KrylovNewton'
}

# =============================
# OPCIONES DE VISUALIZACIÓN
# =============================
VISUALIZATION = {
    'plot_mesh': True,
    'plot_deformed': True,
    'plot_stress': True,
    'save_results': True,
    'output_dir': 'results',
    'animation': False,
}

# =============================
# FUNCIÓN AUXILIAR
# =============================
def get_layer_at_depth(z_coord):
    """
    Retorna el índice del estrato correspondiente a una profundidad z

    Parameters:
    -----------
    z_coord : float
        Coordenada z (negativa hacia abajo)

    Returns:
    --------
    int : índice del estrato (0-indexed)
    """
    depth = abs(z_coord)
    for i, layer in enumerate(SOIL_LAYERS):
        if layer['depth_top'] <= depth < layer['depth_bottom']:
            return i
    # Si está más profundo que el último estrato, usar el último
    return len(SOIL_LAYERS) - 1

def print_configuration():
    """Imprime la configuración del modelo"""
    print("="*70)
    print("CONFIGURACIÓN DEL MODELO DE ENSAYO DE CARGA")
    if USE_SYMMETRY:
        print("*** MODELO 1/4 CON SIMETRÍA ***")
    print("="*70)
    print(f"\nZAPATA:")
    print(f"  Dimensiones totales: {FOOTING_WIDTH} m x {FOOTING_LENGTH} m x {FOOTING_THICKNESS} m")
    if USE_SYMMETRY:
        print(f"  Modelo 1/4: {FOOTING_END_X} m x {FOOTING_END_Y} m x {FOOTING_THICKNESS} m")
    print(f"  Profundidad de desplante (Df): {EMBEDMENT_DEPTH} m")
    print(f"  Espacio libre sobre zapata: {FREE_SPACE_HEIGHT} m")
    print(f"\nDOMINIO DE SUELO:")
    if USE_SYMMETRY:
        print(f"  Modelo 1/4: {SOIL_WIDTH_X} m x {SOIL_WIDTH_Y} m x {SOIL_DEPTH} m")
        print(f"  Equivalente a dominio completo: {SOIL_WIDTH_X*2} m x {SOIL_WIDTH_Y*2} m x {SOIL_DEPTH} m")
        print(f"  Planos de simetría: X=0 y Y=0")
    else:
        print(f"  Dimensiones: {SOIL_WIDTH_X} m x {SOIL_WIDTH_Y} m x {SOIL_DEPTH} m")
    print(f"\nESTRATOS DE SUELO:")
    for i, layer in enumerate(SOIL_LAYERS):
        print(f"  Estrato {i+1}: {layer['name']}")
        print(f"    Profundidad: {layer['depth_top']} - {layer['depth_bottom']} m")
        print(f"    E = {layer['E']/1000:.1f} MPa, φ = {layer['friction_angle']}°, c = {layer['cohesion']} kPa")
    print(f"\nENSAYO DE CARGA:")
    if USE_SYMMETRY:
        print(f"  Carga total: {LOAD_TEST['max_load']} kN")
        print(f"  Carga en modelo 1/4: {LOAD_TEST['max_load']/4:.1f} kN")
    else:
        print(f"  Carga máxima: {LOAD_TEST['max_load']} kN")
    print(f"  Incrementos: {LOAD_TEST['num_steps']}")
    print("="*70)

if __name__ == '__main__':
    print_configuration()
