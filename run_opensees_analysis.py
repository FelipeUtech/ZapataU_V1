#!/usr/bin/env python3
"""
Análisis de zapata con OpenSees usando malla generada por GMSH.

Este script:
1. Lee la malla convertida de opensees_input/
2. Define materiales según config.py
3. Aplica condiciones de frontera (base fija, simetría)
4. Aplica cargas (peso propio + carga de columna)
5. Ejecuta análisis estático
6. Extrae y guarda resultados (desplazamientos, reacciones)

Uso:
    python run_opensees_analysis.py
"""

import openseespy.opensees as ops
import numpy as np
import sys
from pathlib import Path
import config


def leer_nodos_desde_tcl(archivo_tcl):
    """Lee nodos desde archivo TCL generado."""
    nodos = {}
    print(f"📖 Leyendo nodos desde: {archivo_tcl}")

    with open(archivo_tcl, 'r') as f:
        for linea in f:
            linea = linea.strip()
            # Formato: node <tag> <x> <y> <z>
            if linea.startswith('node '):
                partes = linea.split()
                if len(partes) >= 5:
                    tag = int(partes[1])
                    x = float(partes[2])
                    y = float(partes[3])
                    z = float(partes[4])
                    nodos[tag] = (x, y, z)

    print(f"✅ {len(nodos):,} nodos leídos")
    return nodos


def leer_elementos_desde_tcl(archivo_tcl):
    """Lee elementos tetraédricos desde archivo TCL."""
    elementos = []
    print(f"📖 Leyendo elementos desde: {archivo_tcl}")

    with open(archivo_tcl, 'r') as f:
        for linea in f:
            linea = linea.strip()
            # Formato: element FourNodeTetrahedron <tag> <n1> <n2> <n3> <n4> <matTag>
            if linea.startswith('element FourNodeTetrahedron'):
                partes = linea.split()
                if len(partes) >= 8:
                    elem_tag = int(partes[2])
                    n1 = int(partes[3])
                    n2 = int(partes[4])
                    n3 = int(partes[5])
                    n4 = int(partes[6])
                    mat_tag = int(partes[7])
                    elementos.append({
                        'tag': elem_tag,
                        'nodos': [n1, n2, n3, n4],
                        'material': mat_tag
                    })

    print(f"✅ {len(elementos):,} elementos leídos")
    return elementos


def crear_modelo_opensees(nodos, elementos):
    """Crea modelo en OpenSees."""
    print("\n🔨 Creando modelo OpenSees...")

    # Limpiar modelo previo
    ops.wipe()

    # Crear modelo básico
    # -ndm 3: 3 dimensiones
    # -ndf 3: 3 grados de libertad por nodo (ux, uy, uz)
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    print("✅ Modelo básico creado (3D, 3 DOF)")


def definir_materiales():
    """Define materiales según config.py."""
    print("\n🧱 Definiendo materiales...")

    # Definir materiales de estratos de suelo
    for i, estrato in enumerate(config.ESTRATOS_SUELO):
        mat_id = i + 1
        E = estrato['E']  # kPa
        nu = estrato['nu']
        rho = estrato['rho'] / 1000.0  # Convertir kg/m³ a ton/m³

        # nDMaterial ElasticIsotropic tag E nu rho
        ops.nDMaterial('ElasticIsotropic', mat_id, E, nu, rho)

        print(f"   Material {mat_id}: {estrato['nombre']}")
        print(f"      E = {E:.0f} kPa, ν = {nu}, ρ = {rho:.1f} ton/m³")

    # Definir material de zapata
    mat_id_zapata = len(config.ESTRATOS_SUELO) + 1
    E_zapata = config.MATERIAL_ZAPATA['E']
    nu_zapata = config.MATERIAL_ZAPATA['nu']
    rho_zapata = config.MATERIAL_ZAPATA['rho'] / 1000.0

    # TEMPORAL: Reducir rigidez de zapata para prueba
    E_zapata_reducido = 100000.0  # 100 MPa en lugar de 25 GPa

    ops.nDMaterial('ElasticIsotropic', mat_id_zapata, E_zapata_reducido, nu_zapata, rho_zapata)

    print(f"   Material {mat_id_zapata}: Zapata (concreto) - RIGIDEZ REDUCIDA PARA PRUEBA")
    print(f"      E = {E_zapata_reducido:.0f} kPa (original: {E_zapata:.0f}), ν = {nu_zapata}, ρ = {rho_zapata:.1f} ton/m³")

    print("✅ Materiales definidos")


def crear_nodos(nodos_dict):
    """Crea nodos en OpenSees."""
    print(f"\n📍 Creando {len(nodos_dict):,} nodos...")

    for tag, (x, y, z) in nodos_dict.items():
        # node tag x y z
        ops.node(tag, x, y, z)

    print("✅ Nodos creados")


def crear_elementos(elementos_list):
    """Crea elementos tetraédricos en OpenSees."""
    print(f"\n🔷 Creando {len(elementos_list):,} elementos tetraédricos...")

    for elem in elementos_list:
        # element FourNodeTetrahedron eleTag iNode jNode kNode lNode matTag <b1 b2 b3>
        # Sin fuerzas de cuerpo (body forces) - usaremos fuerzas nodales equivalentes
        ops.element('FourNodeTetrahedron',
                   elem['tag'],
                   *elem['nodos'],
                   elem['material'],
                   0.0, 0.0, 0.0)

    # Estadísticas por material
    materiales_count = {}
    for elem in elementos_list:
        mat_id = elem['material']
        materiales_count[mat_id] = materiales_count.get(mat_id, 0) + 1

    print("✅ Elementos creados")
    print("   Distribución por material:")
    for mat_id, count in sorted(materiales_count.items()):
        print(f"      Material {mat_id}: {count:,} elementos")


def aplicar_condiciones_frontera(nodos_dict):
    """Aplica condiciones de frontera al modelo."""
    print("\n🔒 Aplicando condiciones de frontera...")

    # Tolerancia para comparación de coordenadas
    tol = 1e-3

    # Encontrar límites del dominio
    coords = np.array(list(nodos_dict.values()))
    z_min = coords[:, 2].min()
    z_max = coords[:, 2].max()
    x_min = coords[:, 0].min()
    y_min = coords[:, 1].min()

    print(f"   Límites del dominio:")
    print(f"      X: {x_min:.3f} a {coords[:, 0].max():.3f} m")
    print(f"      Y: {y_min:.3f} a {coords[:, 1].max():.3f} m")
    print(f"      Z: {z_min:.3f} a {z_max:.3f} m")

    count_base = 0
    count_sym_x = 0
    count_sym_y = 0

    for tag, (x, y, z) in nodos_dict.items():
        # Base fija (z = z_min)
        if abs(z - z_min) < tol:
            # fix nodeTag ux uy uz (1=fijo, 0=libre)
            ops.fix(tag, 1, 1, 1)
            count_base += 1

        # Simetría en X = 0 (restringir desplazamiento en X)
        elif abs(x - x_min) < tol:
            ops.fix(tag, 1, 0, 0)
            count_sym_x += 1

        # Simetría en Y = 0 (restringir desplazamiento en Y)
        elif abs(y - y_min) < tol:
            ops.fix(tag, 0, 1, 0)
            count_sym_y += 1

    print(f"✅ Condiciones de frontera aplicadas:")
    print(f"      Base fija (z={z_min:.1f}m): {count_base} nodos")
    print(f"      Simetría X (x={x_min:.1f}m): {count_sym_x} nodos")
    print(f"      Simetría Y (y={y_min:.1f}m): {count_sym_y} nodos")


def calcular_fuerzas_gravedad(nodos_dict, elementos_list):
    """
    Calcula fuerzas nodales equivalentes por peso propio de suelo y zapata.

    Para cada elemento tetraédrico, calcula su volumen y masa, y distribuye
    la fuerza gravitacional entre sus 4 nodos (1/4 del peso a cada nodo).
    """
    print("\n⚖️  Calculando fuerzas nodales por peso propio...")

    # Gravedad (hacia abajo en Z)
    g = 9.81  # m/s²

    # Diccionario para acumular fuerzas por nodo
    fuerzas_nodos = {}  # {node_tag: fuerza_z}

    # Obtener densidades por material desde config
    densidades = {
        1: config.ESTRATOS_SUELO[0]['rho'] / 1000.0,  # ton/m³
        2: config.ESTRATOS_SUELO[1]['rho'] / 1000.0,
        3: config.ESTRATOS_SUELO[2]['rho'] / 1000.0,
        4: config.MATERIAL_ZAPATA['rho'] / 1000.0
    }

    masa_total = 0.0

    for elem in elementos_list:
        # Obtener coordenadas de los 4 nodos del tetraedro
        nodos_elem = elem['nodos']
        coords = np.array([nodos_dict[n] for n in nodos_elem])

        # Calcular volumen del tetraedro
        # V = |det(v1, v2, v3)| / 6, donde v1,v2,v3 son vectores desde nodo 0
        v1 = coords[1] - coords[0]
        v2 = coords[2] - coords[0]
        v3 = coords[3] - coords[0]
        volumen = abs(np.dot(v1, np.cross(v2, v3))) / 6.0

        # Obtener densidad del material
        mat_id = elem['material']
        rho = densidades.get(mat_id, 1.8)  # ton/m³

        # Masa del elemento
        masa_elem = volumen * rho  # ton
        masa_total += masa_elem

        # Peso del elemento (fuerza hacia abajo)
        peso_elem = masa_elem * g  # kN (porque ton * m/s² = kN)

        # Distribuir 1/4 del peso a cada nodo del tetraedro
        fuerza_por_nodo = -peso_elem / 4.0  # Negativo = hacia abajo

        for nodo in nodos_elem:
            if nodo not in fuerzas_nodos:
                fuerzas_nodos[nodo] = 0.0
            fuerzas_nodos[nodo] += fuerza_por_nodo

    peso_total = masa_total * g

    print(f"   Masa total del sistema: {masa_total:.2f} ton")
    print(f"   Peso total: {peso_total:.2f} kN")
    print(f"   Nodos con fuerza de gravedad: {len(fuerzas_nodos)}")

    return fuerzas_nodos


def aplicar_cargas(nodos_dict):
    """Aplica cargas en la superficie de la zapata."""
    print("\n⚡ Aplicando cargas...")

    # Encontrar nodos en superficie del terreno (z ≈ 0)
    coords = np.array(list(nodos_dict.values()))
    z_max = coords[:, 2].max()
    tol = 0.15  # Tolerancia para superficie (aumentada)

    # La carga se aplica en la superficie del terreno (z ≈ 0)
    # ya que la zapata está enterrada
    z_superficie = 0.0

    # Encontrar nodos en superficie
    nodos_superficie = []
    for tag, (x, y, z) in nodos_dict.items():
        # Buscar nodos en superficie del terreno
        if abs(z - z_superficie) < tol:
            nodos_superficie.append((tag, x, y, z))

    if len(nodos_superficie) == 0:
        print("❌ No se encontraron nodos en superficie!")
        return

    # Filtrar nodos que están dentro del área de carga
    # Aplicar carga en un área más amplia para evitar singularidades
    area_carga = 1.5  # 1.5 metros de radio para distribuir mejor la carga
    x_centro = 1.5  # Centro aproximado del cuarto de modelo
    y_centro = 1.5

    nodos_carga = []
    for tag, x, y, z in nodos_superficie:
        dist = np.sqrt((x - x_centro)**2 + (y - y_centro)**2)
        if dist <= area_carga:
            nodos_carga.append(tag)

    # Si no hay nodos en el área específica, usar MÁS nodos cercanos al centro
    if len(nodos_carga) < 5:
        print(f"⚠️  Pocos nodos en área de carga ({len(nodos_carga)})")
        print(f"   Usando más nodos cercanos para distribuir la carga...")

        # Encontrar nodos más cercanos al centro
        distancias = [(tag, np.sqrt((x-x_centro)**2 + (y-y_centro)**2))
                     for tag, x, y, z in nodos_superficie]
        distancias.sort(key=lambda x: x[1])

        # Usar al menos 20 nodos para distribuir bien la carga
        n_nodos_usar = min(20, len(distancias))
        nodos_carga = [tag for tag, dist in distancias[:n_nodos_usar]]

    n_nodos_carga = len(nodos_carga)

    # Calcular carga total
    P_column = config.CARGAS['P_column']

    # Debido a cuarto de modelo, solo aplicar 1/4 de la carga
    P_total_cuarto = P_column / 4.0

    # Distribuir carga entre nodos
    carga_por_nodo = -P_total_cuarto / n_nodos_carga  # Negativo = hacia abajo

    print(f"   Carga de columna total: {P_column:.1f} kN")
    print(f"   Carga en cuarto de modelo: {P_total_cuarto:.1f} kN")
    print(f"   Nodos en superficie: {len(nodos_superficie)}")
    print(f"   Nodos con carga aplicada: {n_nodos_carga}")
    print(f"   Carga por nodo: {carga_por_nodo:.3f} kN")

    # Crear patrón de carga para cargas de columna (usar ID 2)
    # Pattern ID 1 está reservado para gravedad
    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)

    # Aplicar cargas
    for node_tag in nodos_carga:
        # load nodeTag Fx Fy Fz
        ops.load(node_tag, 0.0, 0.0, carga_por_nodo)

    print(f"✅ Cargas de columna aplicadas en {n_nodos_carga} nodos (Pattern ID 2)")


def configurar_analisis():
    """Configura parámetros del análisis."""
    print("\n⚙️  Configurando análisis...")

    # Sistema de ecuaciones
    ops.constraints('Plain')
    ops.numberer('RCM')
    ops.system('BandGeneral')

    # Criterio de convergencia más permisivo
    ops.test('NormDispIncr', 1.0e-4, 100, 0)  # Tolerancia relajada

    # Algoritmo de solución
    ops.algorithm('Newton')

    # Integrador con paso más pequeño
    ops.integrator('LoadControl', 0.05)  # Pasos más pequeños = 20 pasos

    # Tipo de análisis
    ops.analysis('Static')

    print("✅ Análisis configurado (20 pasos de carga)")


def ejecutar_fase_gravedad(fuerzas_gravedad):
    """
    Ejecuta fase de peso propio (gravedad).

    Args:
        fuerzas_gravedad: dict con {node_tag: fuerza_z} calculado previamente
    """
    print("\n🌍 FASE 1: PESO PROPIO (GRAVEDAD)")
    print("="*80)

    # Crear patrón de carga para gravedad (Pattern ID = 1)
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    # Aplicar fuerzas nodales de gravedad
    count_cargas = 0
    for node_tag, fuerza_z in fuerzas_gravedad.items():
        # load nodeTag Fx Fy Fz
        ops.load(node_tag, 0.0, 0.0, fuerza_z)
        count_cargas += 1

    print(f"   ✅ {count_cargas} fuerzas nodales de gravedad aplicadas")

    # Configurar análisis de gravedad
    ops.wipeAnalysis()
    ops.constraints('Plain')
    ops.numberer('RCM')
    ops.system('UmfPack')  # Mejor para problemas con gran rango de rigidez
    ops.test('NormDispIncr', 1.0e-3, 200, 0)  # Tolerancia permisiva
    ops.algorithm('Newton')
    ops.integrator('LoadControl', 0.1)  # 10 pasos
    ops.analysis('Static')

    print("⚙️  Análisis de gravedad configurado")
    print("   Ejecutando análisis de peso propio en 10 pasos...")

    n_steps_gravity = 10
    ok = 0

    for i in range(n_steps_gravity):
        ok = ops.analyze(1)

        if ok != 0:
            print(f"   ⚠️  Paso {i+1}/{n_steps_gravity} falló, intentando algoritmo alternativo...")

            ops.algorithm('ModifiedNewton', '-initial')
            ok = ops.analyze(1)

            if ok != 0:
                ops.algorithm('NewtonLineSearch')
                ok = ops.analyze(1)

            if ok != 0:
                ops.algorithm('KrylovNewton')
                ok = ops.analyze(1)

            if ok == 0:
                ops.algorithm('Newton')
                print(f"   ✅ Paso {i+1}/{n_steps_gravity} convergió con algoritmo alternativo")
            else:
                print(f"   ❌ Paso {i+1}/{n_steps_gravity} falló incluso con algoritmos alternativos")
                return False
        else:
            if (i+1) % 2 == 0:
                print(f"   ✓ Paso {i+1}/{n_steps_gravity} completado")

    if ok == 0:
        print(f"✅ Fase de gravedad completada exitosamente")
        print(f"   Estado de peso propio establecido")

        # Fijar el estado actual de gravedad como constante
        # Esto mantiene las cargas de gravedad y el campo de tensiones
        print(f"   🔒 Fijando estado de gravedad con loadConst()")
        ops.loadConst('-time', 0.0)

        # Guardar desplazamientos de la fase de gravedad
        # Los restaremos en post-procesamiento para obtener solo desplazamientos incrementales
        print(f"   💾 Guardando desplazamientos de gravedad para post-procesamiento")

        # Obtener todos los nodos del modelo
        node_tags = ops.getNodeTags()

        # Guardar desplazamientos de gravedad en diccionario
        desplazamientos_gravedad = {}
        for node_tag in node_tags:
            disp = ops.nodeDisp(node_tag)
            desplazamientos_gravedad[node_tag] = {
                'ux': disp[0],
                'uy': disp[1],
                'uz': disp[2]
            }

        print(f"   ✅ Desplazamientos de gravedad guardados ({len(node_tags)} nodos)")
        print(f"   📊 Estado listo para fase 2: tensiones iniciales establecidas")

        return True, desplazamientos_gravedad
    else:
        print(f"❌ Fase de gravedad falló")
        return False, {}


def ejecutar_fase_carga():
    """Ejecuta análisis de carga de la zapata (Fase 2)."""
    print("\n📦 FASE 2: CARGA DE COLUMNA")
    print("="*80)

    # Configurar análisis para carga de zapata
    ops.wipeAnalysis()
    ops.constraints('Plain')
    ops.numberer('RCM')
    ops.system('UmfPack')  # Igual que en inicialización
    ops.test('NormDispIncr', 1.0e-3, 200, 0)  # Tolerancia más permisiva
    ops.algorithm('Newton')
    ops.integrator('LoadControl', 0.05)  # 20 pasos para carga
    ops.analysis('Static')

    print("⚙️  Análisis de carga configurado")
    print("   Aplicando carga de zapata en 20 pasos...")

    n_steps = 20
    ok = 0

    for i in range(n_steps):
        ok = ops.analyze(1)

        if ok != 0:
            print(f"   ⚠️  Paso {i+1}/{n_steps} falló, intentando con algoritmo alternativo...")

            ops.algorithm('ModifiedNewton', '-initial')
            ok = ops.analyze(1)

            if ok != 0:
                ops.algorithm('NewtonLineSearch')
                ok = ops.analyze(1)

            if ok != 0:
                ops.algorithm('KrylovNewton')
                ok = ops.analyze(1)

            if ok == 0:
                ops.algorithm('Newton')
                print(f"   ✅ Paso {i+1}/{n_steps} convergió con algoritmo alternativo")
            else:
                print(f"   ❌ Paso {i+1}/{n_steps} falló incluso con algoritmos alternativos")
                break
        else:
            if (i+1) % 5 == 0:
                print(f"   ✓ Paso {i+1}/{n_steps} completado")

    if ok == 0:
        print(f"✅ Fase de carga completada exitosamente ({n_steps} pasos)")
        return True
    else:
        print(f"❌ Error en fase de carga después de {i+1} pasos")
        return False


def extraer_resultados(nodos_dict, desplazamientos_gravedad=None, output_dir="resultados_opensees"):
    """
    Extrae resultados de desplazamientos y reacciones.

    Args:
        nodos_dict: Diccionario de nodos {tag: (x, y, z)}
        desplazamientos_gravedad: Desplazamientos de fase de gravedad para restar
        output_dir: Directorio de salida
    """
    print("\n📊 Extrayendo resultados...")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Archivo de desplazamientos
    disp_file = output_path / "desplazamientos.csv"
    with open(disp_file, 'w') as f:
        f.write("# Desplazamientos de nodos (INCREMENTALES - solo por carga de columna)\n")
        f.write("# node,x,y,z,ux,uy,uz,u_total\n")

        for tag, (x, y, z) in nodos_dict.items():
            try:
                # Obtener desplazamientos totales
                disp = ops.nodeDisp(tag)
                ux_total, uy_total, uz_total = disp[0], disp[1], disp[2]

                # Restar desplazamientos de gravedad para obtener incrementales
                if desplazamientos_gravedad and tag in desplazamientos_gravedad:
                    ux = ux_total - desplazamientos_gravedad[tag]['ux']
                    uy = uy_total - desplazamientos_gravedad[tag]['uy']
                    uz = uz_total - desplazamientos_gravedad[tag]['uz']
                else:
                    # Si no hay datos de gravedad, usar valores totales
                    ux, uy, uz = ux_total, uy_total, uz_total

                u_total = np.sqrt(ux**2 + uy**2 + uz**2)

                f.write(f"{tag},{x:.6f},{y:.6f},{z:.6f},{ux:.6e},{uy:.6e},{uz:.6e},{u_total:.6e}\n")

            except:
                pass  # Nodo sin resultados

    print(f"   ✅ Desplazamientos guardados: {disp_file}")

    # Archivo de reacciones (solo nodos fijos)
    react_file = output_path / "reacciones.csv"
    with open(react_file, 'w') as f:
        f.write("# Reacciones en nodos fijos\n")
        f.write("# node,x,y,z,Rx,Ry,Rz,R_total\n")

        for tag, (x, y, z) in nodos_dict.items():
            try:
                # Obtener reacciones
                react = ops.nodeReaction(tag)
                Rx, Ry, Rz = react[0], react[1], react[2]
                R_total = np.sqrt(Rx**2 + Ry**2 + Rz**2)

                # Solo guardar si hay reacción significativa
                if R_total > 1e-6:
                    f.write(f"{tag},{x:.6f},{y:.6f},{z:.6f},{Rx:.6e},{Ry:.6e},{Rz:.6e},{R_total:.6e}\n")

            except:
                pass  # Nodo sin reacciones

    print(f"   ✅ Reacciones guardadas: {react_file}")

    # Estadísticas de desplazamientos (incrementales)
    desplazamientos = []
    for tag in nodos_dict.keys():
        try:
            disp = ops.nodeDisp(tag)
            uz_total = disp[2]  # Desplazamiento vertical total

            # Restar desplazamiento de gravedad
            if desplazamientos_gravedad and tag in desplazamientos_gravedad:
                uz = uz_total - desplazamientos_gravedad[tag]['uz']
            else:
                uz = uz_total

            desplazamientos.append(uz)
        except:
            pass

    if desplazamientos:
        desplazamientos = np.array(desplazamientos)
        stats_file = output_path / "estadisticas.txt"

        with open(stats_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("ESTADÍSTICAS DE RESULTADOS - DESPLAZAMIENTOS INCREMENTALES\n")
            f.write("="*70 + "\n\n")

            f.write("IMPORTANTE: Estos son desplazamientos INCREMENTALES (solo carga de columna)\n")
            f.write("El campo de tensiones inicial por gravedad está considerado.\n\n")

            f.write("Desplazamientos verticales (uz) - INCREMENTALES:\n")
            f.write(f"   Máximo (asentamiento): {abs(desplazamientos.min()):.6f} m = {abs(desplazamientos.min())*1000:.3f} mm\n")
            f.write(f"   Mínimo: {desplazamientos.max():.6e} m\n")
            f.write(f"   Promedio: {desplazamientos.mean():.6e} m\n")
            f.write(f"   Desv. estándar: {desplazamientos.std():.6e} m\n")

            f.write(f"\nArchivos generados:\n")
            f.write(f"   - {disp_file.name}\n")
            f.write(f"   - {react_file.name}\n")
            f.write(f"   - {stats_file.name}\n")

        print(f"   ✅ Estadísticas guardadas: {stats_file}")

        print(f"\n📈 Resultados principales:")
        print(f"   Asentamiento máximo: {abs(desplazamientos.min())*1000:.3f} mm")
        print(f"   Número de nodos analizados: {len(desplazamientos):,}")

    return output_path


def main():
    """Función principal."""
    print("="*80)
    print("  ANÁLISIS DE ZAPATA CON OPENSEES")
    print("="*80)

    # Directorios
    input_dir = Path("opensees_input")

    if not input_dir.exists():
        print(f"❌ Error: Directorio {input_dir} no encontrado")
        print("   Ejecuta primero: python run_pipeline.py")
        sys.exit(1)

    # Archivos de entrada
    nodos_file = input_dir / "nodes.tcl"
    elementos_file = input_dir / "elements.tcl"

    if not nodos_file.exists() or not elementos_file.exists():
        print(f"❌ Error: Archivos de malla no encontrados en {input_dir}")
        sys.exit(1)

    try:
        # 1. Leer malla
        print("\n" + "="*80)
        print("PASO 1: LECTURA DE MALLA")
        print("="*80)
        nodos = leer_nodos_desde_tcl(nodos_file)
        elementos = leer_elementos_desde_tcl(elementos_file)

        # 2. Crear modelo
        print("\n" + "="*80)
        print("PASO 2: CREACIÓN DE MODELO")
        print("="*80)
        crear_modelo_opensees(nodos, elementos)
        definir_materiales()
        crear_nodos(nodos)
        crear_elementos(elementos)

        # 3. Aplicar condiciones de frontera
        print("\n" + "="*80)
        print("PASO 3: CONDICIONES DE FRONTERA")
        print("="*80)
        aplicar_condiciones_frontera(nodos)

        # 4. Calcular fuerzas de gravedad
        print("\n" + "="*80)
        print("PASO 4: CÁLCULO DE FUERZAS DE GRAVEDAD")
        print("="*80)
        fuerzas_gravedad = calcular_fuerzas_gravedad(nodos, elementos)

        # 5. Ejecutar análisis en dos fases
        print("\n" + "="*80)
        print("PASO 5: EJECUCIÓN DEL ANÁLISIS EN DOS FASES")
        print("="*80)
        print("📋 Análisis estructurado:")
        print("   1. Fase de gravedad (peso propio)")
        print("   2. Fase de carga (carga de columna)")
        print()

        # Fase 1: Gravedad
        exito_gravedad, desplazamientos_gravedad = ejecutar_fase_gravedad(fuerzas_gravedad)

        if not exito_gravedad:
            print("\n❌ Fase de gravedad falló")
            sys.exit(1)

        # Fase 2: Aplicar y analizar carga de columna
        aplicar_cargas(nodos)
        exito_carga = ejecutar_fase_carga()

        if not exito_carga:
            print("\n❌ Fase de carga falló")
            sys.exit(1)

        # 6. Extraer resultados
        print("\n" + "="*80)
        print("PASO 6: EXTRACCIÓN DE RESULTADOS")
        print("="*80)
        output_dir = extraer_resultados(nodos, desplazamientos_gravedad=desplazamientos_gravedad)

        # Resumen final
        print("\n" + "="*80)
        print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
        print("="*80)
        print(f"\n📂 Resultados guardados en: {output_dir}/")
        print("\nArchivos generados:")
        print("   - desplazamientos.csv  (desplazamientos de todos los nodos)")
        print("   - reacciones.csv       (reacciones en apoyos)")
        print("   - estadisticas.txt     (resumen de resultados)")

        print("\n" + "="*80)
        print("⚠️  IMPORTANTE: INTERPRETACIÓN DE RESULTADOS")
        print("="*80)
        print("Los desplazamientos mostrados son SOLO los debidos a la carga de columna.")
        print("Procedimiento usado:")
        print("  1. Fase 1: Aplicar gravedad → establecer campo de tensiones inicial")
        print("  2. Resetear desplazamientos a cero (mantiene tensiones)")
        print("  3. Fase 2: Aplicar carga de columna → medir desplazamientos ADICIONALES")
        print("\nPor lo tanto:")
        print("  • Los resultados muestran asentamiento INCREMENTAL por carga de columna")
        print("  • El campo de tensiones incluye el efecto de gravedad")
        print("  • Este es el procedimiento estándar en análisis geotécnico")
        print("="*80)
        print("\n🎉 ¡Análisis completado!\n")

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
