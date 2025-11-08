#!/usr/bin/env python3
"""
Script para sincronizar config.py con mesh_config.json automáticamente.
Genera mesh_config.json basándose en los parámetros de config.py.

Uso:
    python sync_config_to_json.py
"""

import json
import config


def generar_mesh_config_desde_config_py():
    """
    Genera un diccionario de configuración de malla desde config.py.
    """
    # Obtener dimensiones del dominio calculadas automáticamente
    dimensiones = config.obtener_dimensiones_dominio()

    # Calcular profundidad total de estratos
    profundidad_total = config.calcular_profundidad_dominio()

    # Crear configuración
    mesh_config = {
        "geometry": {
            "domain": {
                "Lx": dimensiones['Lx'],
                "Ly": dimensiones['Ly'],
                "Lz": dimensiones['Lz'],
                "quarter_domain": config.DOMINIO['usar_cuarto_modelo'],
                "_comment": f"Lx=Ly calculado como {config.DOMINIO['factor_horizontal']}×max(B,L)={config.DOMINIO['factor_horizontal']}×{dimensiones['lado_mayor_zapata']}={dimensiones['Lx']}m, Lz=suma de estratos={dimensiones['Lz']}m"
            },
            "footing": {
                "B": config.ZAPATA['B'],
                "L": config.ZAPATA['L'],
                "Df": config.ZAPATA['Df'],
                "tz": config.ZAPATA['h'],
                "_comment": "Zapata rectangular B×L (ancho×largo)"
            }
        },
        "soil_layers": [],
        "footing_material": {
            "name": "FOOTING",
            "material_id": len(config.ESTRATOS_SUELO) + 1,  # ID después de los estratos
            "description": "Zapata de concreto"
        },
        "mesh_refinement": {
            "lc_footing": config.MALLA['graded']['dx_min'],
            "lc_near": config.MALLA['graded']['dx_min'] * 1.5,
            "lc_far": config.MALLA['graded']['dx_max'],
            "growth_rate": config.MALLA['graded']['ratio'],
            "optimize_netgen": True
        },
        "output": {
            "filename": "zapata_3D_cuarto_refined",
            "formats": ["msh", "vtu", "xdmf"]
        }
    }

    # Agregar estratos de suelo
    for i, estrato in enumerate(config.ESTRATOS_SUELO):
        layer = {
            "name": f"SOIL_{i+1}",
            "thickness": estrato['espesor'],
            "material_id": i + 1,
            "description": estrato['nombre']
        }
        mesh_config['soil_layers'].append(layer)

    # Validar que espesores suman correctamente
    total_thickness = sum(layer['thickness'] for layer in mesh_config['soil_layers'])
    if abs(total_thickness - dimensiones['Lz']) > 1e-6:
        print(f"⚠️  ADVERTENCIA: Suma de estratos ({total_thickness}m) no coincide con Lz ({dimensiones['Lz']}m)")

    return mesh_config


def guardar_mesh_config(mesh_config, filename='mesh_config.json'):
    """Guarda la configuración en archivo JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(mesh_config, f, indent=2, ensure_ascii=False)
    print(f"✅ Archivo guardado: {filename}")


def main():
    """Función principal."""
    print("\n" + "="*70)
    print("SINCRONIZACIÓN DE CONFIGURACIÓN")
    print("="*70)
    print("\n📖 Leyendo config.py...")

    # Mostrar resumen de config.py
    config.imprimir_resumen()

    # Generar configuración JSON
    print("🔄 Generando mesh_config.json desde config.py...")
    mesh_config = generar_mesh_config_desde_config_py()

    # Guardar archivo
    guardar_mesh_config(mesh_config)

    # Mostrar resumen
    print("\n" + "="*70)
    print("CONFIGURACIÓN GENERADA")
    print("="*70)
    print(f"\n📐 Dominio:")
    print(f"   Lx × Ly × Lz: {mesh_config['geometry']['domain']['Lx']} × {mesh_config['geometry']['domain']['Ly']} × {mesh_config['geometry']['domain']['Lz']} m")

    print(f"\n🏗️  Zapata:")
    foot = mesh_config['geometry']['footing']
    print(f"   B × L × h: {foot['B']} × {foot['L']} × {foot['tz']} m")
    print(f"   Df: {foot['Df']} m")

    print(f"\n🪨  Estratos ({len(mesh_config['soil_layers'])} capas):")
    for layer in mesh_config['soil_layers']:
        print(f"   - {layer['name']}: {layer['thickness']} m")

    print(f"\n💡 Ahora puedes generar la malla con:")
    print(f"   python generate_mesh_from_config.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
