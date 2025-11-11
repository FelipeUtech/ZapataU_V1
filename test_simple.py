#!/usr/bin/env python3
"""
Test muy simple para verificar FourNodeTetrahedron
"""
import openseespy.opensees as ops
import numpy as np

print("TEST: FourNodeTetrahedron con nDMaterial")
print("="*60)

# Crear modelo simple
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)

# 4 nodos formando un tetraedro simple de 1m de lado
print("\n1. Crear nodos...")
ops.node(1, 0.0, 0.0, 0.0)
ops.node(2, 1.0, 0.0, 0.0)
ops.node(3, 0.0, 1.0, 0.0)
ops.node(4, 0.0, 0.0, 1.0)
print("✓ 4 nodos creados")

# Fijar nodo 1 completamente
print("\n2. Aplicar condiciones de borde...")
ops.fix(1, 1, 1, 1)
ops.fix(2, 1, 1, 0)
ops.fix(3, 0, 1, 0)
print("✓ Nodo 1 fijado")

# Crear material elástico
print("\n3. Crear material...")
E = 20000.0  # kPa
nu = 0.3
ops.nDMaterial('ElasticIsotropic', 1, E, nu)
print(f"✓ Material: E={E} kPa, nu={nu}")

# Crear elemento
print("\n4. Crear elemento tetraédrico...")
try:
    ops.element('FourNodeTetrahedron', 1, 1, 2, 3, 4, 1)
    print("✓ Elemento tetraédrico creado")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Aplicar carga en nodo 4
print("\n5. Aplicar carga...")
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)
ops.load(4, 0.0, 0.0, -10.0)  # 10 kN hacia abajo
print("✓ Carga -10 kN en nodo 4 (dirección Z)")

# Análisis
print("\n6. Ejecutar análisis...")
ops.system('BandGeneral')
ops.numberer('Plain')
ops.constraints('Plain')
ops.integrator('LoadControl', 1.0)
ops.algorithm('Linear')
ops.analysis('Static')

ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado")
else:
    print(f"❌ Análisis falló: código {ok}")
    exit(1)

# Leer desplazamientos
print("\n7. Desplazamientos:")
print(f"{'Nodo':<6} {'ux (mm)':>12} {'uy (mm)':>12} {'uz (mm)':>12}")
print("-"*48)
for nid in [1, 2, 3, 4]:
    disp = ops.nodeDisp(nid)
    ux, uy, uz = disp[0]*1000, disp[1]*1000, disp[2]*1000
    print(f"{nid:<6} {ux:>12.6f} {uy:>12.6f} {uz:>12.6f}")

print("\n✓ Test completado")
print("="*60)
