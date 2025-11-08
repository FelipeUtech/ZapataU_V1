#!/usr/bin/env python3
"""
===================================================================================
ARCHIVO DE CONFIGURACIÓN - ANÁLISIS DE ZAPATAS CON OPENSEESPY
===================================================================================
Modifica los parámetros en este archivo para personalizar tu análisis.
Todos los valores están en unidades del Sistema Internacional (SI):
    - Longitud: metros (m)
    - Fuerza: kilonewtons (kN)
    - Presión: kilopascales (kPa)
    - Densidad: kg/m³
===================================================================================
"""

# ===================================================================================
# PARÁMETROS GEOMÉTRICOS DE LA ZAPATA
# ===================================================================================

ZAPATA = {
    'B': 2.0,           # Ancho de la zapata (m) - lado menor
    'L': 3.0,           # Largo de la zapata (m) - lado mayor (puede ser diferente de B)
    'h': 0.4,           # Altura/espesor de la zapata (m)
    'Df': 1.5,          # Profundidad de fundación (m) - Zapata enterrada a 1.5m
}

# ===================================================================================
# PARÁMETROS DEL DOMINIO DE SUELO
# ===================================================================================

# Cálculo automático del dominio basado en dimensiones de zapata
_lado_mayor_zapata = max(ZAPATA['B'], ZAPATA['L'])
_factor_dominio = 8  # Factor multiplicador: dominio = 8 × lado mayor

DOMINIO = {
    'factor_horizontal': _factor_dominio,  # Factor multiplicador del lado mayor
                                           # Se calcula como 8 × max(B, L)

    'ancho_horizontal': _factor_dominio * _lado_mayor_zapata,  # Calculado automáticamente
                                                                # = 8 × max(B, L)

    'profundidad': None,        # Se calcula automáticamente como suma de estratos
                                # Ver función calcular_profundidad_dominio()

    'usar_cuarto_modelo': True, # True = modelo 1/4 con simetría (más eficiente)
                                # False = modelo completo
}

# ===================================================================================
# PARÁMETROS DE MALLA
# ===================================================================================

MALLA = {
    'tipo': 'graded',           # Opciones: 'uniform', 'refined', 'graded'
                                # - uniform: malla uniforme en todo el dominio
                                # - refined: malla refinada en zapata, gruesa afuera
                                # - graded: transición gradual geométrica (RECOMENDADO)

    # Parámetros para malla uniforme
    'uniform': {
        'dx': 1.5,              # Tamaño elemento en X (m)
        'dy': 1.5,              # Tamaño elemento en Y (m)
        'dz': 1.5,              # Tamaño elemento en Z (m)
    },

    # Parámetros para malla refinada
    'refined': {
        'dx_zapata': 0.25,      # Tamaño elemento en zona zapata (m)
        'dx_exterior': 0.5,     # Tamaño elemento en zona exterior (m)
        'dz_shallow': 0.5,      # Tamaño elemento vertical superficial (m)
        'dz_deep': 1.0,         # Tamaño elemento vertical profundo (m)
        'depth_transition': 10.0, # Profundidad de transición fino/grueso (m)
    },

    # Parámetros para malla gradual (transición geométrica)
    'graded': {
        'dx_min': 0.5,          # Tamaño mínimo de elemento (cerca de zapata) - OPTIMIZADO
        'dx_max': 2.0,          # Tamaño máximo de elemento (bordes) - OPTIMIZADO
        'ratio': 1.20,          # Ratio de crecimiento geométrico (1.1-1.2) - OPTIMIZADO
        'dz_surface': 0.6,      # Tamaño elemento vertical superficial - OPTIMIZADO
        'dz_deep': 1.5,         # Tamaño elemento vertical profundo - OPTIMIZADO
        'depth_transition': 7.0, # Profundidad de transición (m) - MODERADO
    }
}

# ===================================================================================
# PROPIEDADES DE MATERIALES - SUELO (ESTRATOS)
# ===================================================================================

# Definición de estratos de suelo (de superficie hacia profundidad)
ESTRATOS_SUELO = [
    {
        'nombre': 'Estrato 1',
        'E': 5000.0,            # Módulo de Young (kPa) = 5 MPa
        'nu': 0.3,              # Coeficiente de Poisson
        'rho': 1800.0,          # Densidad (kg/m³)
        'espesor': 3.0,         # Espesor del estrato (m)
    },
    {
        'nombre': 'Estrato 2',
        'E': 20000.0,           # Módulo de Young (kPa) = 20 MPa
        'nu': 0.3,              # Coeficiente de Poisson
        'rho': 1800.0,          # Densidad (kg/m³)
        'espesor': 10.0,        # Espesor del estrato (m)
    },
    {
        'nombre': 'Estrato 3',
        'E': 50000.0,           # Módulo de Young (kPa) = 50 MPa
        'nu': 0.3,              # Coeficiente de Poisson
        'rho': 1800.0,          # Densidad (kg/m³)
        'espesor': 7.0,         # Espesor del estrato (m)
    },
]

# Para compatibilidad con código existente (usa primer estrato como referencia)
MATERIAL_SUELO = ESTRATOS_SUELO[0]

# ===================================================================================
# PROPIEDADES DE MATERIALES - ZAPATA (CONCRETO)
# ===================================================================================

MATERIAL_ZAPATA = {
    'E': 25000000.0,            # Módulo de Young del concreto (kPa) = 25 GPa
                                # Factor: 1250x más rígido que suelo
    'nu': 0.2,                  # Coeficiente de Poisson del concreto
    'rho': 2400.0,              # Densidad del concreto (kg/m³)
}

# ===================================================================================
# CARGAS APLICADAS
# ===================================================================================

CARGAS = {
    'P_column': 1000.0,         # Carga de columna (kN) - carga muerta + viva

    'incluir_peso_propio': True,# True = incluye peso propio de zapata

    # Cargas adicionales (no implementado aún)
    'momento_x': 0.0,           # Momento en X (kN·m)
    'momento_y': 0.0,           # Momento en Y (kN·m)
    'fuerza_horizontal_x': 0.0, # Fuerza horizontal en X (kN)
    'fuerza_horizontal_y': 0.0, # Fuerza horizontal en Y (kN)
}

# ===================================================================================
# PARÁMETROS DE ANÁLISIS
# ===================================================================================

ANALISIS = {
    'tipo': 'Static',           # Tipo de análisis: 'Static', 'Dynamic' (futuro)

    'solver': 'BandGeneral',    # Solver: 'BandGeneral', 'ProfileSPD', 'SparseSYM'

    'numberer': 'RCM',          # Numberer: 'RCM', 'Plain', 'AMD'

    'constraints': 'Plain',     # Constraints: 'Plain', 'Transformation'

    'algorithm': 'Linear',      # Algorithm: 'Linear', 'Newton'
}

# ===================================================================================
# OPCIONES DE SALIDA Y VISUALIZACIÓN
# ===================================================================================

SALIDA = {
    # Archivos de datos
    'guardar_csv': True,                    # Guardar resultados en CSV
    'csv_settlements': 'settlements_3d.csv', # Nombre archivo asentamientos
    'csv_surface': 'surface_settlements.csv', # Nombre archivo superficie

    # Visualizaciones
    'generar_graficas': True,               # Generar gráficas
    'vista_isometrica': True,               # Vista isométrica del modelo
    'mapa_asentamientos': True,             # Mapa de contornos de asentamientos
    'grafica_3d': True,                     # Gráfica 3D de asentamientos

    # Formato de imágenes
    'formato_imagen': 'png',                # Formato: 'png', 'pdf', 'svg'
    'dpi': 300,                             # Resolución de imágenes

    # Nombres de archivos
    'nombre_modelo': 'modelo_zapata',       # Prefijo para archivos de salida

    # Reportes
    'generar_reporte': True,                # Generar reporte de texto
    'nombre_reporte': 'analysis_summary.txt', # Nombre archivo reporte
}

# ===================================================================================
# CRITERIOS DE VERIFICACIÓN
# ===================================================================================

CRITERIOS = {
    # Asentamientos admisibles
    'asentamiento_maximo_admisible': 25.0,  # mm - típico: 25-50mm
    'asentamiento_diferencial_admisible': 0.002, # radianes - típico: 1/500 = 0.002

    # Presiones
    'presion_admisible': 200.0,             # kPa - depende del suelo

    # Factor de seguridad
    'factor_seguridad': 3.0,                # Factor de seguridad global
}

# ===================================================================================
# CONFIGURACIÓN AVANZADA (USUARIOS EXPERTOS)
# ===================================================================================

AVANZADO = {
    'tolerancia_convergencia': 1e-6,        # Tolerancia para convergencia
    'max_iteraciones': 100,                 # Máximo número de iteraciones
    'verbose': True,                        # Imprimir información detallada
    'validar_parametros': True,             # Validar parámetros antes de analizar
}

# ===================================================================================
# FUNCIONES DE UTILIDAD PARA CÁLCULOS Y VALIDACIÓN
# ===================================================================================

def calcular_profundidad_dominio():
    """
    Calcula la profundidad total del dominio basada en la suma de espesores de estratos.
    Retorna la profundidad total en metros.
    """
    profundidad_total = sum(estrato['espesor'] for estrato in ESTRATOS_SUELO)
    return profundidad_total


def obtener_dimensiones_dominio():
    """
    Obtiene las dimensiones completas del dominio.
    Retorna un diccionario con Lx, Ly, Lz.
    """
    lado_mayor = max(ZAPATA['B'], ZAPATA['L'])
    ancho_dominio = DOMINIO['factor_horizontal'] * lado_mayor
    profundidad_dominio = calcular_profundidad_dominio()

    return {
        'Lx': ancho_dominio,
        'Ly': ancho_dominio,
        'Lz': profundidad_dominio,
        'lado_mayor_zapata': lado_mayor,
        'factor': DOMINIO['factor_horizontal']
    }


def validar_configuracion():
    """
    Valida que los parámetros de configuración sean consistentes.
    Retorna True si todo es válido, False en caso contrario.
    """
    errores = []

    # Validar geometría
    if ZAPATA['B'] <= 0 or ZAPATA['L'] <= 0 or ZAPATA['h'] <= 0:
        errores.append("❌ Dimensiones de zapata deben ser positivas")

    if ZAPATA['Df'] < 0:
        errores.append("❌ Profundidad de fundación no puede ser negativa")

    # Validar dominio
    if DOMINIO['factor_horizontal'] < 3:
        errores.append("⚠️  ADVERTENCIA: Factor horizontal < 3 puede causar efectos de borde")

    profundidad_calculada = calcular_profundidad_dominio()
    lado_mayor = max(ZAPATA['B'], ZAPATA['L'])
    if profundidad_calculada < 3 * lado_mayor:
        errores.append(f"⚠️  ADVERTENCIA: Profundidad ({profundidad_calculada}m) < 3×lado_mayor ({3*lado_mayor}m) puede ser insuficiente")

    # Validar materiales
    if MATERIAL_SUELO['E'] <= 0 or MATERIAL_ZAPATA['E'] <= 0:
        errores.append("❌ Módulo de Young debe ser positivo")

    if not (0 <= MATERIAL_SUELO['nu'] < 0.5) or not (0 <= MATERIAL_ZAPATA['nu'] < 0.5):
        errores.append("❌ Coeficiente de Poisson debe estar en [0, 0.5)")

    # Validar cargas
    if CARGAS['P_column'] <= 0:
        errores.append("❌ Carga de columna debe ser positiva")

    # Validar tipo de malla
    if MALLA['tipo'] not in ['uniform', 'refined', 'graded']:
        errores.append(f"❌ Tipo de malla '{MALLA['tipo']}' no válido")

    # Imprimir resultados
    if errores:
        print("\n" + "="*80)
        print("ERRORES Y ADVERTENCIAS EN LA CONFIGURACIÓN:")
        print("="*80)
        for error in errores:
            print(error)
        print("="*80 + "\n")
        return False
    else:
        print("\n✓ Configuración validada correctamente\n")
        return True

def imprimir_resumen():
    """Imprime un resumen de la configuración actual."""
    dimensiones = obtener_dimensiones_dominio()

    print("\n" + "="*80)
    print("RESUMEN DE CONFIGURACIÓN")
    print("="*80)
    print(f"\n📐 GEOMETRÍA:")
    print(f"  Zapata: B={ZAPATA['B']}m × L={ZAPATA['L']}m × h={ZAPATA['h']}m")
    es_cuadrada = ZAPATA['B'] == ZAPATA['L']
    print(f"  Tipo: {'Cuadrada' if es_cuadrada else 'Rectangular'}")
    print(f"  Profundidad fundación: {ZAPATA['Df']}m")
    print(f"\n  Dominio (calculado automáticamente):")
    print(f"    Lado mayor zapata: {dimensiones['lado_mayor_zapata']}m")
    print(f"    Factor horizontal: {dimensiones['factor']}× lado mayor")
    print(f"    Ancho total (Lx=Ly): {dimensiones['Lx']}m = {dimensiones['factor']}×{dimensiones['lado_mayor_zapata']}m")
    print(f"    Profundidad (Lz): {dimensiones['Lz']}m (suma de estratos)")

    print(f"\n🔬 MALLA:")
    print(f"  Tipo: {MALLA['tipo']}")
    print(f"  Modelo: {'1/4 con simetría' if DOMINIO['usar_cuarto_modelo'] else 'Completo'}")

    print(f"\n🏗️  MATERIALES:")
    print(f"  Suelo - {len(ESTRATOS_SUELO)} estratos:")
    z_actual = 0
    for i, estrato in enumerate(ESTRATOS_SUELO, 1):
        z_sup = z_actual
        z_inf = z_actual - estrato['espesor']
        print(f"    {estrato['nombre']}: z={z_sup}m a {z_inf}m, E={estrato['E']/1000:.0f} MPa")
        z_actual = z_inf
    print(f"  Zapata - E: {MATERIAL_ZAPATA['E']} kPa, ν: {MATERIAL_ZAPATA['nu']}")

    print(f"\n⚡ CARGAS:")
    print(f"  Carga columna: {CARGAS['P_column']} kN")
    print(f"  Incluir peso propio: {'Sí' if CARGAS['incluir_peso_propio'] else 'No'}")

    # Calcular presión de contacto aproximada
    area_zapata = ZAPATA['B'] * ZAPATA['L']
    peso_zapata = ZAPATA['B'] * ZAPATA['L'] * ZAPATA['h'] * MATERIAL_ZAPATA['rho'] * 9.81 / 1000
    carga_total = CARGAS['P_column'] + (peso_zapata if CARGAS['incluir_peso_propio'] else 0)
    presion = carga_total / area_zapata

    print(f"  Carga total: {carga_total:.2f} kN")
    print(f"  Presión contacto: {presion:.2f} kPa")

    print(f"\n📊 SALIDA:")
    print(f"  Guardar CSV: {'Sí' if SALIDA['guardar_csv'] else 'No'}")
    print(f"  Generar gráficas: {'Sí' if SALIDA['generar_graficas'] else 'No'}")
    print(f"  Generar reporte: {'Sí' if SALIDA['generar_reporte'] else 'No'}")

    print("\n" + "="*80 + "\n")

# ===================================================================================
# EJECUTAR AL IMPORTAR
# ===================================================================================

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar resumen y validar
    imprimir_resumen()
    validar_configuracion()
    print("\n💡 Tip: Modifica los valores en este archivo y ejecuta 'python run_analysis.py'")
