#!/usr/bin/env python3
"""
Generador de malla tetraédrica para OpenSees con configuración flexible.
Lee parámetros desde un archivo JSON para crear mallas con N estratos de suelo.

Uso:
    python generate_mesh_from_config.py [config_file.json]

Si no se especifica archivo, usa mesh_config.json por defecto.
"""

import sys
import json
import gmsh
import numpy as np
import pyvista as pv
import meshio
from pathlib import Path


def load_config(config_file="mesh_config.json"):
    """Carga configuración desde archivo JSON."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config


def validate_config(config):
    """Valida que la configuración tenga todos los campos necesarios."""
    required_keys = ['geometry', 'soil_layers', 'footing_material', 'mesh_refinement', 'output']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Falta campo requerido en configuración: {key}")

    # Validar que hay al menos una capa de suelo
    if len(config['soil_layers']) == 0:
        raise ValueError("Debe haber al menos una capa de suelo")

    # Validar que espesores suman a Lz
    total_thickness = sum(layer['thickness'] for layer in config['soil_layers'])
    Lz = config['geometry']['domain']['Lz']
    if abs(total_thickness - Lz) > 1e-6:
        raise ValueError(f"Espesores de capas ({total_thickness} m) no suman Lz ({Lz} m)")

    print("✅ Configuración validada correctamente")


def print_config_summary(config):
    """Imprime resumen de la configuración."""
    print("\n" + "="*70)
    print("CONFIGURACIÓN DE LA MALLA")
    print("="*70)

    geom = config['geometry']
    print(f"\n📐 Dominio:")
    print(f"   Lx × Ly × Lz: {geom['domain']['Lx']} × {geom['domain']['Ly']} × {geom['domain']['Lz']} m")
    if geom['domain']['quarter_domain']:
        Lx_eff = geom['domain']['Lx'] / 2
        Ly_eff = geom['domain']['Ly'] / 2
        print(f"   Cuarto de dominio: {Lx_eff} × {Ly_eff} × {geom['domain']['Lz']} m")

    print(f"\n🏗️  Zapata:")
    foot = geom['footing']
    print(f"   Ancho (B): {foot['B']} m")
    print(f"   Profundidad (Df): {foot['Df']} m")
    print(f"   Espesor (tz): {foot['tz']} m")

    print(f"\n🪨  Estratos de suelo ({len(config['soil_layers'])} capas):")
    z_top = 0
    for i, layer in enumerate(config['soil_layers']):
        z_bottom = z_top - layer['thickness']
        print(f"   {i+1}. {layer['name']}: {layer['thickness']} m (z: {z_bottom:.1f} a {z_top:.1f} m) - Material {layer['material_id']}")
        z_top = z_bottom

    print(f"\n🧱 Material zapata:")
    print(f"   {config['footing_material']['name']}: Material {config['footing_material']['material_id']}")

    refine = config['mesh_refinement']
    print(f"\n🔍 Refinamiento:")
    print(f"   En zapata: {refine['lc_footing']} m")
    print(f"   Zona cercana: {refine['lc_near']} m")
    print(f"   Fronteras: {refine['lc_far']} m")
    print(f"   Tasa de crecimiento: {refine['growth_rate']}")

    print(f"\n💾 Salida:")
    print(f"   Archivo: {config['output']['filename']}")
    print(f"   Formatos: {', '.join(config['output']['formats'])}")
    print("="*70 + "\n")


def generate_mesh_from_config(config):
    """Genera malla tetraédrica según configuración."""

    # Extraer parámetros
    geom = config['geometry']
    Lx = geom['domain']['Lx']
    Ly = geom['domain']['Ly']
    Lz = geom['domain']['Lz']
    B = geom['footing']['B']
    Df = geom['footing']['Df']
    tz = geom['footing']['tz']

    z_base = -Df - tz
    z_top = -Df
    x0 = Lx - B / 2
    y0 = Ly - B / 2

    # Aplicar cuarto de dominio si está configurado
    if geom['domain']['quarter_domain']:
        Lx /= 2
        Ly /= 2

    # Calcular límites verticales de cada capa
    soil_layers = config['soil_layers']
    layer_boundaries = [0]  # z = 0 en superficie
    z = 0
    for layer in soil_layers:
        z -= layer['thickness']
        layer_boundaries.append(z)

    # Parámetros de refinamiento
    refine = config['mesh_refinement']
    lc_footing = refine['lc_footing']
    lc_near = refine['lc_near']
    lc_far = refine['lc_far']
    growth_rate = refine['growth_rate']

    # ---------------------------------
    # Inicializar Gmsh
    # ---------------------------------
    gmsh.initialize()
    gmsh.model.add("mesh_from_config")

    print("Creando geometría...")

    # Crear cajas para cada capa de suelo
    soil_volumes = []
    for i, layer in enumerate(soil_layers):
        z_top_layer = layer_boundaries[i]
        z_bottom_layer = layer_boundaries[i + 1]
        height = layer['thickness']

        soil_vol = gmsh.model.occ.addBox(0, 0, z_bottom_layer, Lx, Ly, height)
        soil_volumes.append({
            'tag': soil_vol,
            'name': layer['name'],
            'material_id': layer['material_id'],
            'z_top': z_top_layer,
            'z_bottom': z_bottom_layer
        })

    # Crear excavación y zapata
    excav = gmsh.model.occ.addBox(x0 / 2, y0 / 2, z_base, B / 4, B / 4, tz + Df)
    foot = gmsh.model.occ.addBox(x0 / 2, y0 / 2, z_base, B / 4, B / 4, tz)
    gmsh.model.occ.synchronize()

    # Cortar excavación de cada capa de suelo
    print("Cortando excavación en capas de suelo...")
    for i, soil_vol in enumerate(soil_volumes):
        soil_cut, _ = gmsh.model.occ.cut(
            [(3, soil_vol['tag'])],
            [(3, excav)],
            removeObject=True,
            removeTool=(i == len(soil_volumes) - 1)  # Remover herramienta en última capa
        )
        soil_volumes[i]['tag_cut'] = soil_cut[0][1]

    gmsh.model.occ.synchronize()

    # Crear grupos físicos
    print("Definiendo grupos físicos...")
    physical_groups = {}

    for soil_vol in soil_volumes:
        phys_group = gmsh.model.addPhysicalGroup(3, [soil_vol['tag_cut']])
        gmsh.model.setPhysicalName(3, phys_group, soil_vol['name'])
        physical_groups[soil_vol['name']] = {
            'tag': phys_group,
            'material_id': soil_vol['material_id']
        }

    # Grupo físico para zapata
    phys_foot = gmsh.model.addPhysicalGroup(3, [foot])
    foot_name = config['footing_material']['name']
    gmsh.model.setPhysicalName(3, phys_foot, foot_name)
    physical_groups[foot_name] = {
        'tag': phys_foot,
        'material_id': config['footing_material']['material_id']
    }

    gmsh.model.occ.synchronize()

    # ---------------------------------
    # Configurar refinamiento
    # ---------------------------------
    print("Configurando refinamiento gradual...")

    # Centro de la zapata
    x_center = (x0 / 2 + x0 / 2 + B / 4) / 2
    y_center = (y0 / 2 + y0 / 2 + B / 4) / 2
    z_center = (z_base + z_top) / 2

    def size_callback(dim, tag, x, y, z, lc):
        """Calcula tamaño de elemento según distancia a zapata."""
        dx = x - x_center
        dy = y - y_center
        dz = z - z_center
        dist = np.sqrt(dx**2 + dy**2 + dz**2)

        if dist < 0.5:
            return lc_footing
        elif dist < 2.0:
            t = (dist - 0.5) / 1.5
            return lc_footing + (lc_near - lc_footing) * (t ** growth_rate)
        elif dist < 5.0:
            t = (dist - 2.0) / 3.0
            return lc_near + (lc_far - lc_near) * (t ** (growth_rate * 0.8))
        else:
            return lc_far

    gmsh.model.mesh.setSizeCallback(size_callback)

    # Opciones de malla
    gmsh.option.setNumber("Mesh.Algorithm", 5)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Optimize", 1)

    if refine.get('optimize_netgen', True):
        gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)

    # ---------------------------------
    # Generar malla
    # ---------------------------------
    print("\nGenerando malla tetraédrica 3D...")
    print("Esto puede tardar algunos minutos...\n")
    gmsh.model.mesh.generate(3)

    if refine.get('optimize_netgen', True):
        print("Optimizando malla con Netgen...")
        gmsh.model.mesh.optimize("Netgen")

    # Guardar archivo Gmsh
    output_name = config['output']['filename']
    output_dir = Path("mallas")
    output_dir.mkdir(exist_ok=True)

    if 'msh' in config['output']['formats']:
        msh_path = output_dir / f"{output_name}.msh"
        gmsh.write(str(msh_path))
        print(f"✅ Guardado Gmsh: {msh_path}")

    # ---------------------------------
    # Exportar a otros formatos
    # ---------------------------------
    print("\nExtrayendo datos de malla...")
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    points = node_coords.reshape(-1, 3)

    # Obtener elementos tetraédricos
    etags, ntags = gmsh.model.mesh.getElementsByType(4)
    connectivity = ntags - 1
    tet_tags = etags

    # Identificar dominio de cada elemento
    domain_id = np.zeros(len(tet_tags), dtype=int)

    for name, group_info in physical_groups.items():
        pg = group_info['tag']
        mat_id = group_info['material_id']
        ents = gmsh.model.getEntitiesForPhysicalGroup(3, pg)

        for ent in ents:
            etags_local, _ = gmsh.model.mesh.getElementsByType(4, ent)
            for eid in etags_local:
                idx = np.where(tet_tags == eid)[0]
                if len(idx) > 0:
                    domain_id[idx] = mat_id

    # Crear grid PyVista
    if 'vtu' in config['output']['formats']:
        cells = np.insert(connectivity.reshape(-1, 4), 0, 4, axis=1).ravel()
        celltypes = np.full(len(connectivity) // 4, pv.CellType.TETRA, dtype=np.uint8)
        grid = pv.UnstructuredGrid(cells, celltypes, points)
        grid.cell_data["material_id"] = domain_id

        vtu_path = output_dir / f"{output_name}.vtu"
        grid.save(str(vtu_path))
        print(f"✅ Guardado VTK: {vtu_path}")

    # Guardar XDMF
    if 'xdmf' in config['output']['formats']:
        xdmf_path = output_dir / f"{output_name}.xdmf"
        cells_xdmf = connectivity.reshape(-1, 4) + 1
        mesh = meshio.Mesh(
            points,
            [("tetra", cells_xdmf)],
            cell_data={"material_id": [domain_id.astype(np.int32)]}
        )
        meshio.write(str(xdmf_path), mesh)
        print(f"✅ Guardado XDMF: {xdmf_path}")

    gmsh.finalize()

    # ---------------------------------
    # Estadísticas
    # ---------------------------------
    print("\n" + "="*70)
    print("ESTADÍSTICAS DE LA MALLA GENERADA")
    print("="*70)
    print(f"Número de nodos: {len(points):,}")
    print(f"Número de tetraedros: {len(tet_tags):,}")

    print(f"\nDistribución por material:")
    for name, group_info in physical_groups.items():
        mat_id = group_info['material_id']
        count = np.sum(domain_id == mat_id)
        print(f"  {name} (Material {mat_id}): {count:,} elementos")

    # Análisis de calidad
    elem_volumes = []
    for i in range(0, len(connectivity), 4):
        nodes = points[connectivity[i:i+4]]
        v1 = nodes[1] - nodes[0]
        v2 = nodes[2] - nodes[0]
        v3 = nodes[3] - nodes[0]
        vol = abs(np.dot(v1, np.cross(v2, v3))) / 6.0
        elem_volumes.append(vol)

    elem_volumes = np.array(elem_volumes)
    print(f"\nCalidad de elementos:")
    print(f"  Volumen mínimo: {elem_volumes.min():.6f} m³")
    print(f"  Volumen máximo: {elem_volumes.max():.6f} m³")
    print(f"  Volumen promedio: {elem_volumes.mean():.6f} m³")
    print(f"  Ratio max/min: {elem_volumes.max()/elem_volumes.min():.2f}")

    print(f"\n📍 Límites de la malla:")
    print(f"  X: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}]")
    print(f"  Y: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}]")
    print(f"  Z: [{points[:, 2].min():.3f}, {points[:, 2].max():.3f}]")

    print(f"\n✅ Malla tetraédrica generada exitosamente")
    print(f"   Tipo: FourNodeTetrahedron (compatible con OpenSees)")
    print(f"   Archivos guardados en: {output_dir}/")
    print("="*70 + "\n")

    return {
        'num_nodes': len(points),
        'num_elements': len(tet_tags),
        'material_distribution': {name: np.sum(domain_id == info['material_id'])
                                 for name, info in physical_groups.items()},
        'bounds': {
            'x': (points[:, 0].min(), points[:, 0].max()),
            'y': (points[:, 1].min(), points[:, 1].max()),
            'z': (points[:, 2].min(), points[:, 2].max())
        }
    }


def main():
    """Función principal."""
    # Determinar archivo de configuración
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "mesh_config.json"

    print(f"📄 Leyendo configuración desde: {config_file}")

    try:
        # Cargar y validar configuración
        config = load_config(config_file)
        validate_config(config)

        # Mostrar resumen
        print_config_summary(config)

        # Generar malla
        stats = generate_mesh_from_config(config)

        print("\n🎉 Proceso completado exitosamente!")

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{config_file}'")
        print(f"   Crea un archivo de configuración o especifica uno existente:")
        print(f"   python {sys.argv[0]} <archivo_config.json>")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
