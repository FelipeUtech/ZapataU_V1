#!/usr/bin/env python3
"""
===================================================================================
ANÁLISIS PARAMÉTRICO - ESTUDIO DE SENSIBILIDAD
===================================================================================
Este script permite realizar estudios paramétricos variando uno o más parámetros
y comparando los resultados.

CASOS DE USO:
  1. Estudiar efecto del módulo de elasticidad del suelo
  2. Analizar diferentes geometrías de zapata
  3. Evaluar impacto de diferentes cargas
  4. Estudiar convergencia de malla

CONFIGURACIÓN:
  Edita la sección PARÁMETROS DE ESTUDIO más abajo
===================================================================================
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
import sys

# Importar módulos del paquete
import config
import utils

# ===================================================================================
# CONFIGURACIÓN DEL ESTUDIO PARAMÉTRICO
# ===================================================================================

# Selecciona el tipo de estudio paramétrico
ESTUDIO_TIPO = 'modulo_elasticidad'  # Opciones: 'modulo_elasticidad', 'geometria',
                                      # 'carga', 'convergencia_malla', 'custom'

# ===================================================================================
# DEFINICIÓN DE ESTUDIOS PREDEFINIDOS
# ===================================================================================

ESTUDIOS_PREDEFINIDOS = {

    # 1. Variar módulo de elasticidad del suelo
    'modulo_elasticidad': {
        'nombre': 'Variación del Módulo de Elasticidad del Suelo',
        'parametro': 'E_suelo',
        'valores': [5000, 10000, 15000, 20000, 25000, 30000],  # kPa
        'unidad': 'kPa',
        'descripcion': 'Efecto del módulo E en asentamientos'
    },

    # 2. Variar ancho de zapata
    'geometria': {
        'nombre': 'Variación del Ancho de Zapata',
        'parametro': 'B_zapata',
        'valores': [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],  # m
        'unidad': 'm',
        'descripcion': 'Efecto del ancho B en asentamientos'
    },

    # 3. Variar carga aplicada
    'carga': {
        'nombre': 'Variación de Carga Aplicada',
        'parametro': 'P_column',
        'valores': [500, 750, 1000, 1250, 1500, 2000, 2500],  # kN
        'unidad': 'kN',
        'descripcion': 'Efecto de la carga en asentamientos'
    },

    # 4. Convergencia de malla
    'convergencia_malla': {
        'nombre': 'Estudio de Convergencia de Malla',
        'parametro': 'dx_min',
        'valores': [0.5, 0.4, 0.3, 0.25, 0.2, 0.15],  # m
        'unidad': 'm',
        'descripcion': 'Convergencia con refinamiento de malla'
    },

    # 5. Variar coeficiente de Poisson
    'poisson': {
        'nombre': 'Variación del Coeficiente de Poisson',
        'parametro': 'nu_suelo',
        'valores': [0.2, 0.25, 0.3, 0.35, 0.4],
        'unidad': '-',
        'descripcion': 'Efecto del coeficiente de Poisson'
    },

    # 6. Variar profundidad de fundación
    'profundidad_fundacion': {
        'nombre': 'Variación de Profundidad de Fundación',
        'parametro': 'Df',
        'valores': [0.0, 0.5, 1.0, 1.5, 2.0, 2.5],  # m
        'unidad': 'm',
        'descripcion': 'Efecto de la profundidad Df'
    },
}

# ===================================================================================
# FUNCIONES AUXILIARES
# ===================================================================================

def modificar_parametro(parametro, valor):
    """
    Modifica un parámetro específico en la configuración.

    Parameters:
    -----------
    parametro : str
        Nombre del parámetro a modificar
    valor : float
        Nuevo valor del parámetro
    """
    if parametro == 'E_suelo':
        config.MATERIAL_SUELO['E'] = valor
    elif parametro == 'B_zapata':
        config.ZAPATA['B'] = valor
        config.ZAPATA['L'] = valor  # Mantener cuadrada
    elif parametro == 'P_column':
        config.CARGAS['P_column'] = valor
    elif parametro == 'dx_min':
        config.MALLA['tipo'] = 'graded'
        config.MALLA['graded']['dx_min'] = valor
    elif parametro == 'nu_suelo':
        config.MATERIAL_SUELO['nu'] = valor
    elif parametro == 'Df':
        config.ZAPATA['Df'] = valor
    else:
        raise ValueError(f"Parámetro '{parametro}' no reconocido")


def ejecutar_analisis_simple():
    """
    Ejecuta un análisis simple y retorna resultados principales.
    Versión simplificada de run_analysis.py sin visualizaciones.

    Returns:
    --------
    resultados : dict
        Diccionario con resultados principales
    """
    # Preparar parámetros
    zapata = config.ZAPATA
    dominio_cfg = config.DOMINIO
    malla_cfg = config.MALLA
    mat_suelo = config.MATERIAL_SUELO
    mat_zapata = config.MATERIAL_ZAPATA
    cargas = config.CARGAS

    usar_cuarto = dominio_cfg['usar_cuarto_modelo']
    factor = dominio_cfg['factor_horizontal']

    if usar_cuarto:
        Lx = factor * zapata['B'] / 2.0
        Ly = factor * zapata['L'] / 2.0
        B_modelo = zapata['B'] / 2.0
        L_modelo = zapata['L'] / 2.0
    else:
        Lx = factor * zapata['B']
        Ly = factor * zapata['L']
        B_modelo = zapata['B']
        L_modelo = zapata['L']

    Lz = dominio_cfg['profundidad']
    dominio = {'Lx': Lx, 'Ly': Ly, 'Lz': Lz}
    zapata_modelo = {'B': B_modelo, 'L': L_modelo, 'h': zapata['h'],
                     'x_min': 0.0, 'y_min': 0.0}

    # Generar malla
    tipo_malla = malla_cfg['tipo']
    if tipo_malla == 'uniform':
        params = malla_cfg['uniform']
        nx = int(Lx / params['dx'])
        ny = int(Ly / params['dy'])
        nz = int(Lz / params['dz'])
        x_coords, y_coords, z_coords = utils.generar_malla_uniforme(dominio, nx, ny, nz)
    elif tipo_malla == 'refined':
        params = malla_cfg['refined']
        x_coords, y_coords, z_coords = utils.generar_malla_refinada(dominio, zapata_modelo, params)
        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1
    elif tipo_malla == 'graded':
        params = malla_cfg['graded']
        x_coords, y_coords, z_coords = utils.generar_malla_gradual(dominio, zapata_modelo, params)
        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1

    # Crear modelo
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    node_coords, surface_nodes = utils.crear_nodos(x_coords, y_coords, z_coords)
    zapata_nodes = utils.identificar_nodos_zapata(surface_nodes, node_coords, zapata_modelo)

    nodes_per_layer = (nx + 1) * (ny + 1)
    utils.aplicar_condiciones_borde(nz + 1, nodes_per_layer, nx, ny, usar_cuarto)

    ops.nDMaterial('ElasticIsotropic', 1, mat_suelo['E'], mat_suelo['nu'], mat_suelo['rho'])

    n_elements = utils.crear_elementos(nx, ny, nz, nodes_per_layer, mat_tag=1)

    # Aplicar cargas
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    P_column = cargas['P_column']
    if usar_cuarto:
        P_column = P_column / 4.0

    carga_total = utils.aplicar_cargas(zapata_nodes, P_column, zapata, mat_zapata,
                                       cargas['incluir_peso_propio'])

    # Ejecutar análisis
    analisis_cfg = config.ANALISIS
    ops.system(analisis_cfg['solver'])
    ops.numberer(analisis_cfg['numberer'])
    ops.constraints(analisis_cfg['constraints'])
    ops.integrator('LoadControl', 1.0)
    ops.algorithm(analisis_cfg['algorithm'])
    ops.analysis(analisis_cfg['tipo'])

    ok = ops.analyze(1)

    if ok != 0:
        return None  # Análisis falló

    # Extraer resultados
    df_settlements = utils.extraer_asentamientos(node_coords)
    df_surface = df_settlements[df_settlements['Z'] == df_settlements['Z'].max()]

    # Calcular estadísticas
    s_max = df_surface['Settlement_mm'].max()
    s_min = df_surface['Settlement_mm'].min()
    s_mean = df_surface['Settlement_mm'].mean()
    s_std = df_surface['Settlement_mm'].std()
    s_diff = s_max - s_min

    # Asentamiento en centro de zapata
    s_center = df_surface[
        (df_surface['X'] <= zapata_modelo['B'] / 2) &
        (df_surface['Y'] <= zapata_modelo['L'] / 2)
    ]['Settlement_mm'].max()

    # Presión de contacto
    area_zapata = zapata['B'] * zapata['L']
    if usar_cuarto:
        area_zapata = area_zapata / 4.0
    presion = carga_total / area_zapata

    resultados = {
        'asentamiento_maximo': s_max,
        'asentamiento_minimo': s_min,
        'asentamiento_promedio': s_mean,
        'asentamiento_centro': s_center,
        'desviacion_estandar': s_std,
        'diferencial': s_diff,
        'presion_contacto': presion,
        'carga_total': carga_total,
        'n_elementos': n_elements,
        'n_nodos': len(node_coords),
    }

    return resultados


def ejecutar_estudio_parametrico(estudio):
    """
    Ejecuta un estudio paramétrico completo.

    Parameters:
    -----------
    estudio : dict
        Diccionario con configuración del estudio

    Returns:
    --------
    resultados_df : pd.DataFrame
        DataFrame con resultados del estudio
    """
    parametro = estudio['parametro']
    valores = estudio['valores']

    print("\n" + "="*80)
    print(f"ESTUDIO PARAMÉTRICO: {estudio['nombre']}")
    print("="*80)
    print(f"Parámetro: {parametro}")
    print(f"Valores: {valores}")
    print(f"Total de corridas: {len(valores)}")
    print("="*80 + "\n")

    # Desactivar visualizaciones
    config.SALIDA['generar_graficas'] = False
    config.SALIDA['guardar_csv'] = False
    config.SALIDA['generar_reporte'] = False

    # Guardar configuración original
    import copy
    config_original = copy.deepcopy(config.ZAPATA)

    resultados_lista = []

    for i, valor in enumerate(valores, 1):
        print(f"Corrida {i}/{len(valores)}: {parametro} = {valor} {estudio['unidad']}")

        # Modificar parámetro
        modificar_parametro(parametro, valor)

        # Ejecutar análisis
        try:
            resultado = ejecutar_analisis_simple()

            if resultado is not None:
                resultado[parametro] = valor
                resultados_lista.append(resultado)
                print(f"  ✓ Asentamiento máximo: {resultado['asentamiento_maximo']:.4f} mm")
            else:
                print(f"  ✗ Análisis falló")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Restaurar configuración
    config.ZAPATA = config_original

    # Crear DataFrame
    resultados_df = pd.DataFrame(resultados_lista)

    print("\n" + "="*80)
    print("ESTUDIO COMPLETADO")
    print("="*80 + "\n")

    return resultados_df


def generar_graficas_parametricas(resultados_df, estudio, archivo_base='parametric'):
    """
    Genera gráficas del estudio paramétrico.

    Parameters:
    -----------
    resultados_df : pd.DataFrame
        Resultados del estudio
    estudio : dict
        Configuración del estudio
    archivo_base : str
        Nombre base para archivos
    """
    parametro = estudio['parametro']
    unidad = estudio['unidad']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Estudio Paramétrico: {estudio['nombre']}", fontsize=14, fontweight='bold')

    # 1. Asentamiento máximo vs parámetro
    ax = axes[0, 0]
    ax.plot(resultados_df[parametro], resultados_df['asentamiento_maximo'],
            'o-', linewidth=2, markersize=8, color='red', label='Máximo')
    ax.plot(resultados_df[parametro], resultados_df['asentamiento_centro'],
            's-', linewidth=2, markersize=8, color='blue', label='Centro')
    ax.set_xlabel(f'{parametro} ({unidad})', fontsize=11)
    ax.set_ylabel('Asentamiento (mm)', fontsize=11)
    ax.set_title('Asentamientos vs Parámetro', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 2. Presión de contacto vs parámetro
    ax = axes[0, 1]
    ax.plot(resultados_df[parametro], resultados_df['presion_contacto'],
            'o-', linewidth=2, markersize=8, color='green')
    ax.set_xlabel(f'{parametro} ({unidad})', fontsize=11)
    ax.set_ylabel('Presión de Contacto (kPa)', fontsize=11)
    ax.set_title('Presión de Contacto vs Parámetro', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # 3. Diferencial vs parámetro
    ax = axes[1, 0]
    ax.plot(resultados_df[parametro], resultados_df['diferencial'],
            'o-', linewidth=2, markersize=8, color='orange')
    ax.set_xlabel(f'{parametro} ({unidad})', fontsize=11)
    ax.set_ylabel('Asentamiento Diferencial (mm)', fontsize=11)
    ax.set_title('Asentamiento Diferencial vs Parámetro', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # 4. Tabla de resumen
    ax = axes[1, 1]
    ax.axis('off')

    # Crear tabla con estadísticas
    tabla_data = [
        ['Parámetro', 'Mín', 'Máx'],
        [f'{parametro}', f"{resultados_df[parametro].min():.2f}",
         f"{resultados_df[parametro].max():.2f}"],
        ['Asent. máx (mm)', f"{resultados_df['asentamiento_maximo'].min():.2f}",
         f"{resultados_df['asentamiento_maximo'].max():.2f}"],
        ['Asent. centro (mm)', f"{resultados_df['asentamiento_centro'].min():.2f}",
         f"{resultados_df['asentamiento_centro'].max():.2f}"],
        ['Presión (kPa)', f"{resultados_df['presion_contacto'].min():.2f}",
         f"{resultados_df['presion_contacto'].max():.2f}"],
    ]

    tabla = ax.table(cellText=tabla_data, cellLoc='center', loc='center',
                    colWidths=[0.4, 0.3, 0.3])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10)
    tabla.scale(1, 2)

    # Estilo para encabezado
    for i in range(3):
        tabla[(0, i)].set_facecolor('#4CAF50')
        tabla[(0, i)].set_text_props(weight='bold', color='white')

    ax.set_title('Resumen de Resultados', fontweight='bold', pad=20)

    plt.tight_layout()
    archivo = f'{archivo_base}_{parametro}.png'
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo}")
    plt.close()


def guardar_resultados_json(resultados_df, estudio, archivo='parametric_results.json'):
    """Guarda resultados en formato JSON."""
    data = {
        'estudio': estudio,
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'resultados': resultados_df.to_dict('records')
    }

    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Resultados guardados: {archivo}")


# ===================================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================================

def main():
    """Función principal del análisis paramétrico."""

    print("\n" + "="*80)
    print("ANÁLISIS PARAMÉTRICO - ESTUDIO DE SENSIBILIDAD")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Seleccionar estudio
    if ESTUDIO_TIPO not in ESTUDIOS_PREDEFINIDOS:
        print(f"❌ Error: Tipo de estudio '{ESTUDIO_TIPO}' no reconocido")
        print(f"\nEstudios disponibles: {list(ESTUDIOS_PREDEFINIDOS.keys())}")
        sys.exit(1)

    estudio = ESTUDIOS_PREDEFINIDOS[ESTUDIO_TIPO]

    # Ejecutar estudio
    resultados_df = ejecutar_estudio_parametrico(estudio)

    if len(resultados_df) == 0:
        print("❌ No se obtuvieron resultados")
        sys.exit(1)

    # Guardar resultados
    csv_file = f"parametric_{estudio['parametro']}.csv"
    resultados_df.to_csv(csv_file, index=False)
    print(f"✓ Resultados guardados: {csv_file}")

    # Guardar JSON
    guardar_resultados_json(resultados_df, estudio)

    # Generar gráficas
    print("\nGenerando gráficas...")
    generar_graficas_parametricas(resultados_df, estudio)

    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    print(resultados_df.to_string(index=False))
    print("="*80 + "\n")

    print("✅ Análisis paramétrico completado exitosamente\n")


# ===================================================================================
# EJECUTAR
# ===================================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
