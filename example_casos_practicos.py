#!/usr/bin/env python3
"""
===================================================================================
EJEMPLOS PRÁCTICOS - CASOS DE USO COMUNES
===================================================================================
Este script muestra cómo usar el paquete para diferentes casos prácticos:

CASOS INCLUIDOS:
  1. Zapata cuadrada pequeña (edificio residencial)
  2. Zapata grande (edificio industrial)
  3. Zapata en suelo blando
  4. Zapata en suelo rígido
  5. Zapata con carga elevada

Selecciona el caso modificando la variable CASO_SELECCIONADO más abajo.
===================================================================================
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

# Importar módulos del paquete
import config

# ===================================================================================
# SELECCIÓN DE CASO
# ===================================================================================

CASO_SELECCIONADO = 1  # Cambiar este número para seleccionar diferentes casos

# ===================================================================================
# DEFINICIÓN DE CASOS PRÁCTICOS
# ===================================================================================

CASOS_PRACTICOS = {

    1: {
        'nombre': 'Zapata Cuadrada Pequeña - Edificio Residencial',
        'descripcion': '''
        Casa de 2 pisos con carga moderada
        - Columna de concreto armado
        - Suelo de consistencia media
        - Zapata superficial
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 2.0,           # Zapata 2m × 2m
                'L': 2.0,
                'h': 0.5,           # Altura 0.5m
                'Df': 0.5,          # Profundidad 0.5m
            },
            'CARGAS': {
                'P_column': 500.0,  # Carga 500 kN (~50 ton)
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 15000.0,       # Suelo medio (15 MPa)
                'nu': 0.3,
                'rho': 1800.0,
            },
            'MALLA': {
                'tipo': 'graded',
            },
            'DOMINIO': {
                'factor_horizontal': 5,
                'profundidad': 15.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 20.0,  # mm
            'presion_contacto_esperada': 130.0,    # kPa
        }
    },

    2: {
        'nombre': 'Zapata Grande - Edificio Industrial',
        'descripcion': '''
        Nave industrial con columna de alta carga
        - Estructura metálica pesada
        - Suelo compacto
        - Zapata grande y profunda
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 5.0,           # Zapata 5m × 5m
                'L': 5.0,
                'h': 1.0,           # Altura 1.0m
                'Df': 1.5,          # Profundidad 1.5m
            },
            'CARGAS': {
                'P_column': 3000.0, # Carga 3000 kN (~300 ton)
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 25000.0,       # Suelo compacto (25 MPa)
                'nu': 0.28,
                'rho': 1900.0,
            },
            'MALLA': {
                'tipo': 'graded',
            },
            'DOMINIO': {
                'factor_horizontal': 6,
                'profundidad': 30.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 30.0,
            'presion_contacto_esperada': 125.0,
        }
    },

    3: {
        'nombre': 'Zapata en Suelo Blando - Zona Costera',
        'descripcion': '''
        Edificio en zona costera con suelo blando
        - Suelo arcilloso blando
        - Asentamientos elevados esperados
        - Requiere análisis cuidadoso
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 3.5,
                'L': 3.5,
                'h': 0.8,
                'Df': 1.0,
            },
            'CARGAS': {
                'P_column': 1200.0,
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 5000.0,        # Suelo blando (5 MPa)
                'nu': 0.35,         # Poisson alto para arcillas
                'rho': 1700.0,
            },
            'MALLA': {
                'tipo': 'graded',
            },
            'DOMINIO': {
                'factor_horizontal': 6,
                'profundidad': 25.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 60.0,  # Asentamientos altos
            'presion_contacto_esperada': 100.0,
        }
    },

    4: {
        'nombre': 'Zapata en Suelo Rígido - Roca Alterada',
        'descripcion': '''
        Edificio sobre roca alterada o suelo muy compacto
        - Material rocoso o grava densa
        - Asentamientos mínimos
        - Alta capacidad portante
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 2.5,
                'L': 2.5,
                'h': 0.6,
                'Df': 0.8,
            },
            'CARGAS': {
                'P_column': 1500.0,
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 50000.0,       # Suelo muy rígido (50 MPa)
                'nu': 0.25,
                'rho': 2100.0,
            },
            'MALLA': {
                'tipo': 'refined',   # Malla refinada suficiente
            },
            'DOMINIO': {
                'factor_horizontal': 4,  # Dominio más pequeño OK
                'profundidad': 15.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 5.0,   # Muy bajo
            'presion_contacto_esperada': 250.0,
        }
    },

    5: {
        'nombre': 'Zapata con Carga Muy Elevada - Puente',
        'descripcion': '''
        Apoyo de puente con carga concentrada muy alta
        - Estructura de puente
        - Requiere zapata masiva
        - Suelo de buena calidad
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 6.0,           # Zapata muy grande
                'L': 6.0,
                'h': 1.5,
                'Df': 2.0,
            },
            'CARGAS': {
                'P_column': 5000.0, # Carga muy alta (500 ton)
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 30000.0,
                'nu': 0.28,
                'rho': 2000.0,
            },
            'MALLA': {
                'tipo': 'graded',
            },
            'DOMINIO': {
                'factor_horizontal': 6,
                'profundidad': 35.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 35.0,
            'presion_contacto_esperada': 145.0,
        }
    },

    6: {
        'nombre': 'Zapata Rápida con Malla Uniforme - Diseño Preliminar',
        'descripcion': '''
        Análisis rápido para diseño preliminar
        - Malla uniforme simple
        - Menor tiempo de cálculo
        - Precisión moderada
        ''',
        'parametros': {
            'ZAPATA': {
                'B': 3.0,
                'L': 3.0,
                'h': 0.6,
                'Df': 0.5,
            },
            'CARGAS': {
                'P_column': 1000.0,
                'incluir_peso_propio': True,
            },
            'MATERIAL_SUELO': {
                'E': 20000.0,
                'nu': 0.3,
                'rho': 1800.0,
            },
            'MALLA': {
                'tipo': 'uniform',
                'uniform': {
                    'dx': 1.0,      # Malla gruesa
                    'dy': 1.0,
                    'dz': 1.0,
                }
            },
            'DOMINIO': {
                'factor_horizontal': 4,  # Dominio pequeño
                'profundidad': 15.0,
                'usar_cuarto_modelo': True,
            }
        },
        'verificacion': {
            'asentamiento_maximo_esperado': 25.0,
            'presion_contacto_esperada': 125.0,
        }
    },

}

# ===================================================================================
# FUNCIONES
# ===================================================================================

def aplicar_caso(caso_num):
    """
    Aplica la configuración de un caso específico.

    Parameters:
    -----------
    caso_num : int
        Número del caso a aplicar
    """
    if caso_num not in CASOS_PRACTICOS:
        print(f"❌ Error: Caso {caso_num} no existe")
        print(f"\nCasos disponibles: {list(CASOS_PRACTICOS.keys())}")
        sys.exit(1)

    caso = CASOS_PRACTICOS[caso_num]

    print("\n" + "="*80)
    print(f"CASO PRÁCTICO {caso_num}: {caso['nombre']}")
    print("="*80)
    print("\nDescripción:")
    print(caso['descripcion'])
    print("="*80 + "\n")

    # Aplicar parámetros al config
    for seccion, parametros in caso['parametros'].items():
        config_seccion = getattr(config, seccion)
        for key, value in parametros.items():
            if isinstance(value, dict):
                config_seccion[key].update(value)
            else:
                config_seccion[key] = value

    return caso


def mostrar_configuracion_caso():
    """Muestra la configuración actual del caso."""
    print("\n" + "-"*80)
    print("CONFIGURACIÓN DEL CASO:")
    print("-"*80)

    print(f"\n📐 ZAPATA:")
    print(f"  Dimensiones: {config.ZAPATA['B']}m × {config.ZAPATA['L']}m × {config.ZAPATA['h']}m")
    print(f"  Profundidad: {config.ZAPATA['Df']}m")

    print(f"\n⚡ CARGAS:")
    print(f"  Carga columna: {config.CARGAS['P_column']} kN")

    # Calcular datos adicionales
    area = config.ZAPATA['B'] * config.ZAPATA['L']
    peso_zapata = area * config.ZAPATA['h'] * config.MATERIAL_ZAPATA['rho'] * 9.81 / 1000
    carga_total = config.CARGAS['P_column'] + peso_zapata
    presion = carga_total / area

    print(f"  Peso zapata: {peso_zapata:.2f} kN")
    print(f"  Carga total: {carga_total:.2f} kN")
    print(f"  Presión contacto: {presion:.2f} kPa")

    print(f"\n🏗️  SUELO:")
    print(f"  Módulo E: {config.MATERIAL_SUELO['E']} kPa")
    print(f"  Coef. Poisson: {config.MATERIAL_SUELO['nu']}")
    print(f"  Densidad: {config.MATERIAL_SUELO['rho']} kg/m³")

    print(f"\n🔬 MALLA:")
    print(f"  Tipo: {config.MALLA['tipo']}")

    print(f"\n📦 DOMINIO:")
    Lx = config.DOMINIO['factor_horizontal'] * config.ZAPATA['B']
    if config.DOMINIO['usar_cuarto_modelo']:
        Lx = Lx / 2.0
        modelo_str = "1/4 con simetría"
    else:
        modelo_str = "completo"
    print(f"  Modelo: {modelo_str}")
    print(f"  Dimensiones: {Lx}m × {Lx}m × {config.DOMINIO['profundidad']}m")

    print("-"*80 + "\n")


def comparar_con_esperado(caso):
    """
    Compara resultados obtenidos con valores esperados.

    Parameters:
    -----------
    caso : dict
        Diccionario del caso con valores de verificación
    """
    # Nota: Esta es una función placeholder
    # En un caso real, ejecutarías el análisis y compararías
    print("\n" + "="*80)
    print("VALORES DE REFERENCIA (APROXIMADOS)")
    print("="*80)

    if 'verificacion' in caso:
        verif = caso['verificacion']
        print(f"\n📊 Resultados esperados:")
        if 'asentamiento_maximo_esperado' in verif:
            print(f"  Asentamiento máximo: ~{verif['asentamiento_maximo_esperado']:.1f} mm")
        if 'presion_contacto_esperada' in verif:
            print(f"  Presión de contacto: ~{verif['presion_contacto_esperada']:.1f} kPa")

    print("\n⚠️  NOTA: Estos son valores aproximados de referencia.")
    print("Los valores reales dependen de las condiciones específicas del suelo.")
    print("="*80 + "\n")


def listar_todos_casos():
    """Lista todos los casos disponibles."""
    print("\n" + "="*80)
    print("CASOS PRÁCTICOS DISPONIBLES")
    print("="*80 + "\n")

    for num, caso in CASOS_PRACTICOS.items():
        print(f"{num}. {caso['nombre']}")
        print(f"   {caso['descripcion'].strip()}\n")

    print("="*80)
    print(f"\nPara seleccionar un caso, modifica CASO_SELECCIONADO en este script.")
    print("Luego ejecuta: python run_analysis.py")
    print("="*80 + "\n")


# ===================================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================================

def main():
    """Función principal."""

    print("\n" + "="*80)
    print("EJEMPLOS PRÁCTICOS - CONFIGURACIÓN DE CASOS")
    print("="*80)

    # Aplicar caso seleccionado
    caso = aplicar_caso(CASO_SELECCIONADO)

    # Mostrar configuración
    mostrar_configuracion_caso()

    # Mostrar valores de referencia
    comparar_con_esperado(caso)

    # Instrucciones
    print("\n" + "="*80)
    print("PRÓXIMOS PASOS")
    print("="*80)
    print("\n1. Revisa la configuración mostrada arriba")
    print("2. Ejecuta el análisis con:")
    print("   python run_analysis.py")
    print("\n3. Para cambiar de caso, modifica CASO_SELECCIONADO en este script")
    print("\n4. Para ver todos los casos disponibles, ejecuta:")
    print("   python example_casos_practicos.py --list")
    print("="*80 + "\n")


# ===================================================================================
# EJECUTAR
# ===================================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        listar_todos_casos()
    else:
        try:
            main()
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
