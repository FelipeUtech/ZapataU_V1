# Configuración de Zapatas Rectangulares

## Descripción General

El sistema ahora soporta **zapatas rectangulares (B×L)** con cálculo automático del dominio de análisis.

## Características Principales

### 1. Zapata Rectangular
- **B**: Ancho de la zapata (lado menor, eje X)
- **L**: Largo de la zapata (lado mayor, eje Y)
- Soporta tanto zapatas cuadradas (B=L) como rectangulares (B≠L)

### 2. Cálculo Automático del Dominio

#### Dimensión Horizontal
El ancho del dominio se calcula automáticamente como:

```
Lx = Ly = 8 × max(B, L)
```

Es decir, **8 veces el lado mayor de la zapata**, lo que garantiza que los efectos de borde sean mínimos.

#### Dimensión Vertical
La profundidad del dominio se calcula automáticamente como:

```
Lz = suma de espesores de todos los estratos
```

Esto asegura que el modelo incluya todos los estratos de suelo definidos.

## Configuración en `config.py`

### Definir Dimensiones de la Zapata

```python
ZAPATA = {
    'B': 2.0,    # Ancho (m) - lado menor
    'L': 3.0,    # Largo (m) - lado mayor
    'h': 0.4,    # Espesor (m)
    'Df': 1.5,   # Profundidad de fundación (m)
}
```

### Definir Estratos de Suelo

```python
ESTRATOS_SUELO = [
    {
        'nombre': 'Estrato 1',
        'E': 5000.0,       # kPa
        'nu': 0.3,
        'rho': 1800.0,     # kg/m³
        'espesor': 3.0,    # m
    },
    {
        'nombre': 'Estrato 2',
        'E': 20000.0,      # kPa
        'nu': 0.3,
        'rho': 1800.0,     # kg/m³
        'espesor': 10.0,   # m
    },
    {
        'nombre': 'Estrato 3',
        'E': 50000.0,      # kPa
        'nu': 0.3,
        'rho': 1800.0,     # kg/m³
        'espesor': 7.0,    # m
    },
]
```

## Ejemplo de Cálculo

### Configuración
- Zapata: B=2.0m, L=3.0m
- Estratos: 3.0m + 10.0m + 7.0m = 20.0m

### Dominio Calculado
- **Lado mayor zapata**: max(2.0, 3.0) = 3.0m
- **Lx = Ly**: 8 × 3.0 = **24.0m**
- **Lz**: 3.0 + 10.0 + 7.0 = **20.0m**
- **Dominio total**: 24.0m × 24.0m × 20.0m

### Con Cuarto de Modelo (Simetría)
Si `usar_cuarto_modelo = True`:
- **Dominio efectivo**: 12.0m × 12.0m × 20.0m
- **Zapata en modelo**: 1.0m × 1.5m (mitad de B y mitad de L)

## Flujo de Trabajo

### 1. Modificar Configuración
Edita `config.py` para definir:
- Dimensiones de zapata (B, L, h, Df)
- Estratos de suelo (espesor, propiedades)
- Parámetros de malla y análisis

### 2. Verificar Configuración
```bash
python config.py
```

Verás un resumen como:
```
📐 GEOMETRÍA:
  Zapata: B=2.0m × L=3.0m × h=0.4m
  Tipo: Rectangular
  Profundidad fundación: 1.5m

  Dominio (calculado automáticamente):
    Lado mayor zapata: 3.0m
    Factor horizontal: 8× lado mayor
    Ancho total (Lx=Ly): 24.0m = 8×3.0m
    Profundidad (Lz): 20.0m (suma de estratos)
```

### 3. Sincronizar con JSON
```bash
python sync_config_to_json.py
```

Esto genera automáticamente `mesh_config.json` desde `config.py`.

### 4. Generar Malla
```bash
python generate_mesh_from_config.py
```

Genera la malla tetraédrica 3D con las dimensiones rectangulares.

### 5. Ejecutar Análisis
```bash
python run_analysis.py
```

## Funciones de Utilidad

### `calcular_profundidad_dominio()`
Calcula la profundidad total sumando espesores de estratos.

```python
from config import calcular_profundidad_dominio

profundidad = calcular_profundidad_dominio()
# Retorna: 20.0 (para el ejemplo)
```

### `obtener_dimensiones_dominio()`
Retorna un diccionario con todas las dimensiones calculadas.

```python
from config import obtener_dimensiones_dominio

dim = obtener_dimensiones_dominio()
print(dim)
# {
#   'Lx': 24.0,
#   'Ly': 24.0,
#   'Lz': 20.0,
#   'lado_mayor_zapata': 3.0,
#   'factor': 8
# }
```

## Ventajas del Sistema

1. **Flexibilidad**: Soporta zapatas cuadradas y rectangulares
2. **Automatización**: No hay que calcular manualmente las dimensiones del dominio
3. **Consistencia**: El dominio siempre es proporcional a la zapata
4. **Simplicidad**: Solo define las dimensiones de zapata y estratos
5. **Validación**: Verifica que la configuración sea consistente

## Recomendaciones

### Factor Horizontal
- **Mínimo recomendado**: 5-6 veces el lado mayor
- **Valor por defecto**: 8 veces (muy conservador)
- Si el dominio es muy grande, puedes reducir a 6× para ahorrar elementos

### Profundidad del Dominio
- **Mínimo recomendado**: 6-7 veces el lado mayor de la zapata
- La suma de estratos debe cumplir: Σespesor ≥ 6×max(B,L)
- El sistema te advertirá si es insuficiente

### Refinamiento de Malla
- Usa `dx_min` pequeño cerca de la zapata (0.3-0.5m)
- Usa `dx_max` más grande en los bordes (1.5-2.5m)
- Ratio de crecimiento: 1.1-1.2 (transición suave)

## Compatibilidad

Este sistema es compatible con:
- ✅ `generate_mesh_from_config.py` (generación de mallas)
- ✅ `run_analysis.py` (análisis con OpenSees)
- ✅ Scripts de visualización (PyVista, matplotlib)
- ✅ Modelos de cuarto (simetría) y completos

## Preguntas Frecuentes

### ¿Puedo usar zapatas cuadradas?
Sí, simplemente define B = L en config.py.

### ¿Cómo cambio el factor del dominio?
Modifica `_factor_dominio` en la sección DOMINIO de config.py:
```python
_factor_dominio = 6  # Cambia de 8 a 6, por ejemplo
```

### ¿Qué pasa si agrego más estratos?
La profundidad del dominio se recalculará automáticamente sumando todos los espesores.

### ¿Puedo definir Lz manualmente?
No directamente en la versión actual. El Lz se calcula como suma de estratos para garantizar consistencia.

## Archivo de Ejemplo

Ver `mesh_config.json` para un ejemplo completo de configuración generada automáticamente.
