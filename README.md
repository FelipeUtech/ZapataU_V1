# Análisis de Zapata con OpenSeesPy

Proyecto de análisis estructural de zapatas sobre suelo utilizando el método de elementos finitos 3D con OpenSeesPy.

## Descripción

Este proyecto implementa un modelo 3D de elementos finitos para analizar el comportamiento de una zapata de concreto sobre un dominio de suelo, calculando asentamientos y distribución de esfuerzos bajo cargas aplicadas.

## Archivos del Proyecto

### Scripts de Análisis

1. **`soil_mesh_3d.py`** - Script base para generación de malla 3D de suelo
   - Crea un dominio de suelo de 20m × 20m × 20m
   - Malla de elementos brick (hexaédricos)
   - Condiciones de borde: base fija y bordes laterales con rodillos

2. **`zapata_analysis.py`** - Análisis básico de zapata
   - Malla: 10 × 10 × 10 elementos
   - Zapata de 3m × 3m × 0.6m centrada
   - Carga total: 1127 kN (1000 kN columna + 127 kN peso propio)

3. **`zapata_analysis_refined.py`** - Análisis refinado (RECOMENDADO)
   - Malla mejorada: 20 × 20 × 15 elementos
   - Mejor captura del comportamiento de la zapata
   - 9 nodos bajo la zapata para distribución de carga más precisa

## Resultados del Análisis Refinado

### Parámetros del Modelo

**Geometría:**
- Zapata: 3.0m × 3.0m × 0.6m
- Dominio de suelo: 20.0m × 20.0m × 20.0m
- Malla: 20 × 20 × 15 elementos (7,056 nodos)
- Tamaño de elemento: 1.0m × 1.0m × 1.33m

**Propiedades del Suelo:**
- Módulo de Young: 30 MPa (arena densa / arcilla firme)
- Coeficiente de Poisson: 0.3
- Densidad: 1,800 kg/m³

**Propiedades del Concreto:**
- Módulo de Young: 25,000 MPa
- Coeficiente de Poisson: 0.2
- Densidad: 2,400 kg/m³

**Cargas:**
- Carga de columna: 1,000 kN
- Peso propio zapata: 127.14 kN
- Carga total: 1,127.14 kN
- Presión de contacto: 125.24 kPa

### Resultados Principales

| Parámetro | Valor |
|-----------|-------|
| Asentamiento máximo | 12.22 mm |
| Asentamiento mínimo | 10.49 mm |
| Asentamiento promedio | 10.97 mm |
| Desviación estándar | 0.53 mm |
| Asentamiento diferencial | 1.73 mm |
| Relación diferencial | 14.13% |

### Verificaciones

✓ **Asentamiento total < 25mm** - ACEPTABLE
- El asentamiento máximo de 12.22 mm está dentro del límite típico de 25 mm para estructuras

⚠ **Asentamiento diferencial ≥ 10%** - REVISAR
- La relación diferencial de 14.13% supera el límite recomendado del 10%
- Podría requerir ajustes en el diseño o mejora del suelo

## Archivos de Resultados

- `zapata_analysis_refined.png` - Visualización completa con 6 gráficas:
  - Mapa de contorno de asentamientos en superficie
  - Perfiles de asentamiento en cortes X e Y
  - Vista 3D de asentamientos
  - Distribución bajo la zapata
  - Resumen de datos y verificaciones

- `analysis_summary_refined.txt` - Resumen textual del análisis
- `surface_settlements_refined.csv` - Asentamientos en todos los nodos de superficie
- `zapata_settlements_refined.csv` - Asentamientos bajo la zapata

## Instalación

### Dependencias del Sistema (Linux)
```bash
sudo apt-get install libblas3 liblapack3 libgfortran5
```

### Paquetes de Python
```bash
pip install openseespy matplotlib scipy numpy
```

## Uso

### Ejecutar el Análisis Refinado
```bash
python zapata_analysis_refined.py
```

Esto generará:
- Gráficas de resultados (PNG)
- Archivos de datos (CSV)
- Resumen del análisis (TXT)

### Modificar Parámetros

Para cambiar las propiedades del análisis, edita las siguientes secciones en `zapata_analysis_refined.py`:

**Dimensiones del suelo:**
```python
Lx_soil = 20.0    # Longitud en x (m)
Ly_soil = 20.0    # Longitud en y (m)
Lz_soil = 20.0    # Profundidad en z (m)
```

**Discretización de la malla:**
```python
nx = 20      # Número de elementos en x
ny = 20      # Número de elementos en y
nz = 15      # Número de elementos en z
```

**Dimensiones de la zapata:**
```python
B_zapata = 3.0    # Ancho de la zapata (m)
L_zapata = 3.0    # Largo de la zapata (m)
h_zapata = 0.6    # Espesor de la zapata (m)
```

**Propiedades del suelo:**
```python
E_soil = 30000.0      # Módulo de Young (kPa)
nu_soil = 0.3         # Coeficiente de Poisson
rho_soil = 1800.0     # Densidad (kg/m³)
```

**Cargas:**
```python
P_column = 1000.0      # Carga de columna (kN)
```

## Características del Modelo

### Condiciones de Borde
- **Base (z = -20m):** Completamente fija (restricción en x, y, z)
- **Bordes laterales:** Rodillos (permiten movimiento vertical)
  - Bordes x = 0 y x = 20m: restricción en x
  - Bordes y = 0 y y = 20m: restricción en y

### Tipo de Elementos
- Elementos brick estándar (`stdBrick`) de 8 nodos
- Material elástico isótropo (`ElasticIsotropic`)

### Análisis
- Análisis estático lineal
- Sistema de ecuaciones: Band General
- Numerador: RCM (Reverse Cuthill-McKee)
- Integrador: Control de carga

## Visualizaciones

El script genera automáticamente:

1. **Mapa de contorno** - Distribución de asentamientos en superficie
2. **Perfiles de corte** - Asentamientos a lo largo de ejes X e Y
3. **Vista 3D** - Representación tridimensional de asentamientos
4. **Distribución bajo zapata** - Asentamientos en nodos cargados
5. **Panel de información** - Resumen completo del análisis

## Notas Técnicas

- El modelo utiliza unidades: metros (m), kilonewtons (kN), kilopascales (kPa)
- La carga se distribuye uniformemente entre los nodos bajo la zapata
- El asentamiento diferencial se calcula como la diferencia entre máximo y mínimo
- Los resultados son válidos para comportamiento elástico lineal del suelo

## Mejoras Futuras

- [ ] Implementar modelos de suelo no lineales (Mohr-Coulomb, Drucker-Prager)
- [ ] Agregar capas de suelo con diferentes propiedades
- [ ] Análisis de consolidación (tiempo-dependiente)
- [ ] Cálculo de esfuerzos en el suelo y en la zapata
- [ ] Verificación de capacidad portante
- [ ] Análisis paramétrico automatizado

## Referencias

- OpenSeesPy Documentation: https://openseespydoc.readthedocs.io/
- Fundamentos de Mecánica de Suelos (Bowles, 1996)
- Foundation Engineering Handbook (Fang, 1991)

## Autor

Proyecto desarrollado para análisis de zapatas con elementos finitos 3D.

## Licencia

Este proyecto está disponible para uso educativo e investigación.
