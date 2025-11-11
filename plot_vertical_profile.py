#!/usr/bin/env python3
"""
Generar perfil vertical de asentamientos en el eje z (x=0, y=0)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Leer datos
df = pd.read_csv('settlements_total.csv')

# Filtrar solo los nodos en x=0, y=0
tolerance = 1e-3
df_eje = df[(abs(df['X']) < tolerance) & (abs(df['Y']) < tolerance)].copy()

# Ordenar por profundidad
df_eje = df_eje.sort_values('Z', ascending=False)

print(f"Nodos encontrados en eje (x=0, y=0): {len(df_eje)}")
print("\nDatos del perfil:")
print(df_eje[['Z', 'Settlement_gravedad_mm', 'Settlement_carga_mm', 'Settlement_total_mm']])

# Crear gráfico
fig, ax = plt.subplots(figsize=(10, 12))

# Graficar las tres curvas
ax.plot(df_eje['Settlement_gravedad_mm'], df_eje['Z'],
        'b-o', linewidth=2, markersize=6, label='Gravedad')
ax.plot(df_eje['Settlement_carga_mm'], df_eje['Z'],
        'r-s', linewidth=2, markersize=6, label='Carga incremental')
ax.plot(df_eje['Settlement_total_mm'], df_eje['Z'],
        'g-^', linewidth=2.5, markersize=7, label='Total', alpha=0.7)

# Marcar interfaces de estratos
# Estrato 1: z=0 a -3.0m
# Estrato 2: z=-3.0 a -13.0m
# Estrato 3: z=-13.0 a -20.0m
ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Superficie')
ax.axhline(y=-1.2, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Df=-1.2m (base zapata)')
ax.axhline(y=-3.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='E1/E2 interface')
ax.axhline(y=-13.0, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='E2/E3 interface')
ax.axhline(y=-20.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Fondo fijo')

# Configuración del gráfico
ax.set_xlabel('Asentamiento (mm)', fontsize=12, fontweight='bold')
ax.set_ylabel('Profundidad Z (m)', fontsize=12, fontweight='bold')
ax.set_title('Perfil Vertical de Asentamientos\nEje Central (X=0, Y=0)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
ax.legend(loc='best', fontsize=10, framealpha=0.9)

# Invertir eje y para que negativo vaya hacia abajo
ax.set_ylim(-20.5, 0.5)

# Agregar texto con información de estratos
ax.text(0.98, 0.95, 'Estratos:', transform=ax.transAxes,
        fontsize=10, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
ax.text(0.98, 0.90, 'E1: 0 a -3m (E=5 MPa)', transform=ax.transAxes,
        fontsize=9, verticalalignment='top', horizontalalignment='right')
ax.text(0.98, 0.86, 'E2: -3 a -13m (E=20 MPa)', transform=ax.transAxes,
        fontsize=9, verticalalignment='top', horizontalalignment='right')
ax.text(0.98, 0.82, 'E3: -13 a -20m (E=50 MPa)', transform=ax.transAxes,
        fontsize=9, verticalalignment='top', horizontalalignment='right')

plt.tight_layout()
plt.savefig('perfil_vertical_asentamientos.png', dpi=300, bbox_inches='tight')
print("\n✓ Gráfico guardado: perfil_vertical_asentamientos.png")

# Guardar datos del perfil en CSV
df_eje.to_csv('perfil_vertical_data.csv', index=False)
print("✓ Datos del perfil guardados: perfil_vertical_data.csv")

plt.show()
