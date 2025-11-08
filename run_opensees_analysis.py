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

    ops.nDMaterial('ElasticIsotropic', mat_id_zapata, E_zapata, nu_zapata, rho_zapata)

    print(f"   Material {mat_id_zapata}: Zapata (concreto)")
    print(f"      E = {E_zapata:.0f} kPa, ν = {nu_zapata}, ρ = {rho_zapata:.1f} ton/m³")

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
        ops.element('FourNodeTetrahedron',
                   elem['tag'],
                   *elem['nodos'],
                   elem['material'],
                   0.0, 0.0, -9.81)  # Gravedad en -Z (kN/ton = m/s²)

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
    # Aplicar carga en un área central de 1m x 1m para simular carga de columna
    area_carga = 0.5  # Medio metro de radio
    x_centro = 2.0  # Aproximadamente centro de la zapata en el cuarto de modelo
    y_centro = 2.0

    nodos_carga = []
    for tag, x, y, z in nodos_superficie:
        dist = np.sqrt((x - x_centro)**2 + (y - y_centro)**2)
        if dist <= area_carga:
            nodos_carga.append(tag)

    # Si no hay nodos en el área específica, usar nodos cercanos al centro
    if len(nodos_carga) == 0:
        print(f"⚠️  No se encontraron nodos en área de carga central")
        print(f"   Usando nodos más cercanos al centro...")

        # Encontrar nodos más cercanos al centro
        distancias = [(tag, np.sqrt((x-x_centro)**2 + (y-y_centro)**2 + z**2))
                     for tag, x, y, z in nodos_superficie]
        distancias.sort(key=lambda x: x[1])

        # Usar los 5-10 nodos más cercanos
        n_nodos_usar = min(10, len(distancias))
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

    # Crear patrón de carga
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    # Aplicar cargas
    for node_tag in nodos_carga:
        # load nodeTag Fx Fy Fz
        ops.load(node_tag, 0.0, 0.0, carga_por_nodo)

    print(f"✅ Cargas aplicadas en {n_nodos_carga} nodos")


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


def ejecutar_analisis():
    """Ejecuta el análisis estático con algoritmo adaptativo."""
    print("\n🚀 Ejecutando análisis...")

    n_steps = 20  # 20 pasos con LoadControl 0.05
    ok = 0

    for i in range(n_steps):
        ok = ops.analyze(1)

        if ok != 0:
            print(f"   ⚠️  Paso {i+1}/{n_steps} falló, intentando con algoritmo alternativo...")

            # Intentar con algoritmo modificado de Newton
            ops.algorithm('ModifiedNewton', '-initial')
            ok = ops.analyze(1)

            if ok != 0:
                # Intentar con NewtonLineSearch
                ops.algorithm('NewtonLineSearch')
                ok = ops.analyze(1)

            if ok != 0:
                # Intentar con KrylovNewton
                ops.algorithm('KrylovNewton')
                ok = ops.analyze(1)

            # Volver a Newton para siguientes pasos
            if ok == 0:
                ops.algorithm('Newton')
                print(f"   ✅ Paso {i+1}/{n_steps} convergió con algoritmo alternativo")
            else:
                print(f"   ❌ Paso {i+1}/{n_steps} falló incluso con algoritmos alternativos")
                break
        else:
            if (i+1) % 5 == 0:  # Mostrar progreso cada 5 pasos
                print(f"   ✓ Paso {i+1}/{n_steps} completado")

    if ok == 0:
        print(f"✅ Análisis completado exitosamente ({n_steps} pasos)")
        return True
    else:
        print(f"❌ Error en análisis después de {i+1} pasos")
        return False


def extraer_resultados(nodos_dict, output_dir="resultados_opensees"):
    """Extrae resultados de desplazamientos y reacciones."""
    print("\n📊 Extrayendo resultados...")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Archivo de desplazamientos
    disp_file = output_path / "desplazamientos.csv"
    with open(disp_file, 'w') as f:
        f.write("# Desplazamientos de nodos\n")
        f.write("# node,x,y,z,ux,uy,uz,u_total\n")

        for tag, (x, y, z) in nodos_dict.items():
            try:
                # Obtener desplazamientos
                disp = ops.nodeDisp(tag)
                ux, uy, uz = disp[0], disp[1], disp[2]
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

    # Estadísticas de desplazamientos
    desplazamientos = []
    for tag in nodos_dict.keys():
        try:
            disp = ops.nodeDisp(tag)
            uz = disp[2]  # Desplazamiento vertical
            desplazamientos.append(uz)
        except:
            pass

    if desplazamientos:
        desplazamientos = np.array(desplazamientos)
        stats_file = output_path / "estadisticas.txt"

        with open(stats_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("ESTADÍSTICAS DE RESULTADOS\n")
            f.write("="*70 + "\n\n")

            f.write("Desplazamientos verticales (uz):\n")
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
        print("PASO 3: CONDICIONES DE FRONTERA Y CARGAS")
        print("="*80)
        aplicar_condiciones_frontera(nodos)
        aplicar_cargas(nodos)

        # 4. Configurar y ejecutar análisis
        print("\n" + "="*80)
        print("PASO 4: ANÁLISIS")
        print("="*80)
        configurar_analisis()
        exito = ejecutar_analisis()

        if not exito:
            print("\n❌ El análisis falló")
            sys.exit(1)

        # 5. Extraer resultados
        print("\n" + "="*80)
        print("PASO 5: EXTRACCIÓN DE RESULTADOS")
        print("="*80)
        output_dir = extraer_resultados(nodos)

        # Resumen final
        print("\n" + "="*80)
        print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
        print("="*80)
        print(f"\n📂 Resultados guardados en: {output_dir}/")
        print("\nArchivos generados:")
        print("   - desplazamientos.csv  (desplazamientos de todos los nodos)")
        print("   - reacciones.csv       (reacciones en apoyos)")
        print("   - estadisticas.txt     (resumen de resultados)")
        print("\n🎉 ¡Análisis completado!\n")

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
