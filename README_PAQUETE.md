# Paquete Integrado de Análisis de Zapatas con OpenSeesPy

## 📋 Descripción

Este paquete proporciona una solución integrada y fácil de usar para el análisis de zapatas superficiales utilizando OpenSeesPy. Incluye:

- **Configuración simple** mediante archivo `config.py`
- **Múltiples tipos de malla**: uniforme, refinada, gradual
- **Modelos optimizados**: modelo completo o 1/4 con simetría
- **Visualizaciones automáticas**: vistas isométricas, mapas de asentamientos
- **Reportes completos**: resultados en CSV y reportes de texto

---

## 🚀 Inicio Rápido

### 1. Requisitos

```bash
pip install openseespy numpy pandas matplotlib
```

### 2. Uso Básico

```bash
# 1. Edita los parámetros en config.py
nano config.py

# 2. Ejecuta el análisis
python run_analysis.py
```

¡Eso es todo! El script hará el resto.

---

## 📁 Estructura de Archivos

```
ZapataU_V1/
├── config.py              # ⭐ ARCHIVO DE CONFIGURACIÓN (editar aquí)
├── run_analysis.py        # ⭐ SCRIPT PRINCIPAL (ejecutar este)
├── utils.py               # Funciones auxiliares (no editar)
├── README_PAQUETE.md      # Este archivo
│
├── # Scripts individuales (versiones anteriores)
├── zapata_analysis_quarter.py
├── zapata_graded_mesh.py
├── zapata_refined_mesh.py
│
└── # Resultados (generados automáticamente)
    ├── settlements_3d.csv
    ├── surface_settlements.csv
    ├── analysis_summary.txt
    ├── modelo_zapata_isometric.png
    └── modelo_zapata_settlements.png
```

---

## ⚙️ Configuración (config.py)

### Parámetros Principales

#### 1. Geometría de la Zapata

```python
ZAPATA = {
    'B': 3.0,      # Ancho (m)
    'L': 3.0,      # Largo (m)
    'h': 0.6,      # Altura (m)
    'Df': 0.0,     # Profundidad de fundación (m)
}
```

#### 2. Dominio de Suelo

```python
DOMINIO = {
    'factor_horizontal': 6,        # Dominio = 6 × B (recomendado: 5-6)
    'profundidad': 20.0,           # Profundidad total (m)
    'usar_cuarto_modelo': True,    # True = modelo 1/4 (más rápido)
}
```

#### 3. Tipo de Malla

```python
MALLA = {
    'tipo': 'graded',  # Opciones: 'uniform', 'refined', 'graded'

    # Configurar solo la sección del tipo elegido:
    'graded': {
        'dx_min': 0.2,           # Tamaño mínimo (cerca de zapata)
        'dx_max': 2.0,           # Tamaño máximo (bordes)
        'ratio': 1.15,           # Ratio de crecimiento
        'dz_surface': 0.3,       # Tamaño vertical superficial
        'dz_deep': 1.0,          # Tamaño vertical profundo
        'depth_transition': 6.0, # Profundidad de transición
    }
}
```

#### 4. Materiales

```python
MATERIAL_SUELO = {
    'E': 20000.0,    # Módulo de Young (kPa)
    'nu': 0.3,       # Coeficiente de Poisson
    'rho': 1800.0,   # Densidad (kg/m³)
}

MATERIAL_ZAPATA = {
    'E': 200000.0,   # Módulo de Young del concreto (kPa)
    'nu': 0.2,       # Coeficiente de Poisson
    'rho': 2400.0,   # Densidad (kg/m³)
}
```

#### 5. Cargas

```python
CARGAS = {
    'P_column': 1000.0,           # Carga de columna (kN)
    'incluir_peso_propio': True,  # Incluir peso de zapata
}
```

#### 6. Opciones de Salida

```python
SALIDA = {
    'guardar_csv': True,
    'generar_graficas': True,
    'generar_reporte': True,
    'formato_imagen': 'png',
    'dpi': 300,
}
```

---

## 📊 Resultados

### Archivos Generados

1. **settlements_3d.csv**: Asentamientos de todos los nodos (X, Y, Z, Settlement_mm)
2. **surface_settlements.csv**: Asentamientos en superficie
3. **analysis_summary.txt**: Reporte completo del análisis
4. **modelo_zapata_isometric.png**: Vista 3D del modelo
5. **modelo_zapata_settlements.png**: Mapa de contornos de asentamientos

### Interpretación de Resultados

El script verifica automáticamente:
- ✓ Asentamiento máximo < 25 mm (configurable)
- ✓ Asentamiento diferencial < 1/500 (configurable)

---

## 🔧 Ejemplos de Uso

### Ejemplo 1: Análisis Rápido con Configuración por Defecto

```bash
python run_analysis.py
```

### Ejemplo 2: Zapata Grande con Malla Refinada

Editar `config.py`:
```python
ZAPATA = {'B': 5.0, 'L': 5.0, 'h': 0.8, 'Df': 1.0}
DOMINIO = {'factor_horizontal': 5, 'profundidad': 30.0, 'usar_cuarto_modelo': True}
MALLA = {'tipo': 'refined'}
CARGAS = {'P_column': 2500.0, 'incluir_peso_propio': True}
```

Ejecutar:
```bash
python run_analysis.py
```

### Ejemplo 3: Suelo Blando

Editar `config.py`:
```python
MATERIAL_SUELO = {
    'E': 5000.0,     # Suelo blando (5 MPa)
    'nu': 0.35,
    'rho': 1600.0,
}
```

### Ejemplo 4: Modelo Completo (sin simetría)

Editar `config.py`:
```python
DOMINIO = {
    'factor_horizontal': 4,
    'profundidad': 20.0,
    'usar_cuarto_modelo': False,  # Modelo completo
}
```

**Nota**: El modelo completo requiere ~4× más tiempo de cálculo.

---

## 📈 Comparación de Tipos de Malla

| Tipo | Ventajas | Desventajas | Uso Recomendado |
|------|----------|-------------|-----------------|
| **uniform** | Simple, predecible | Muchos elementos, lento | Modelos pequeños, pruebas |
| **refined** | Balance precisión/velocidad | Transición abrupta | Análisis estándar |
| **graded** | Óptimo, transición suave | Configuración compleja | Análisis profesional, publicación |

---

## 🎯 Mejores Prácticas

### 1. Selección del Dominio

- **Factor horizontal**: 5-6× el ancho B (mínimo 3×)
- **Profundidad**: 6-7× el ancho B (mínimo 3×)
- Usar `usar_cuarto_modelo=True` siempre que sea posible (75% más rápido)

### 2. Selección de Malla

- **Pruebas rápidas**: `uniform` con dx=1.0m
- **Análisis estándar**: `refined` con dx_zapata=0.25m
- **Publicación/tesis**: `graded` con dx_min=0.2m, ratio=1.15

### 3. Convergencia

Para verificar convergencia, ejecuta con mallas progresivamente más finas:
```python
# Corrida 1: dx_min=0.4
# Corrida 2: dx_min=0.3
# Corrida 3: dx_min=0.2
# Comparar resultados - diferencia < 5% = convergido
```

### 4. Validación

Valora tu análisis verificando:
- ✓ Asentamientos en bordes lejanos ≈ 0 (efectos de borde minimizados)
- ✓ Distribución de asentamientos suave (sin discontinuidades)
- ✓ Comparar con soluciones analíticas simples (si aplica)

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'openseespy'"

**Solución**:
```bash
pip install openseespy
```

### Error: "Análisis no converge"

**Solución**:
1. Verificar que cargas son razonables
2. Verificar propiedades de materiales (E > 0, 0 ≤ ν < 0.5)
3. Usar malla más fina
4. Revisar condiciones de borde

### Advertencia: "Factor horizontal < 3"

**Solución**: Aumentar `factor_horizontal` en config.py (mínimo 3, recomendado 5-6)

### Resultados inesperados

**Verificar**:
1. Unidades correctas (m, kN, kPa)
2. Geometría correcta (B, L, h positivos)
3. Material suelo realista (E típico: 5000-50000 kPa)
4. Dominio suficientemente grande

---

## 📚 Referencias

### Libros
- Bowles, J.E. (1996). "Foundation Analysis and Design"
- Das, B.M. (2015). "Principles of Foundation Engineering"

### Software
- OpenSeesPy: https://openseespydoc.readthedocs.io/
- OpenSees: https://opensees.berkeley.edu/

### Normas
- ACI 318: Building Code Requirements for Structural Concrete
- ASCE 7: Minimum Design Loads for Buildings

---

## 🤝 Contribuciones

Para reportar bugs o sugerir mejoras, contacta al desarrollador o modifica directamente el código.

---

## 📝 Notas de Versión

### v1.0 (2025-11-06)
- ✓ Versión inicial integrada
- ✓ Soporte para 3 tipos de malla
- ✓ Modelo completo y 1/4
- ✓ Visualizaciones automáticas
- ✓ Validación de parámetros

### Próximas características (planificadas)
- [ ] Modelos de material no lineal
- [ ] Análisis de cargas combinadas (momento, horizontal)
- [ ] Análisis de grupo de zapatas
- [ ] Interfaz gráfica (GUI)
- [ ] Exportación a formatos CAD

---

## 📧 Soporte

Para preguntas o asistencia:
- Revisa este README completo
- Consulta la documentación de OpenSeesPy
- Verifica la configuración en config.py

---

## ⚖️ Licencia

Este código es proporcionado "tal cual" para propósitos educativos y de investigación.

**IMPORTANTE**: Los resultados de este software deben ser verificados por un ingeniero profesional antes de su uso en diseño estructural real.

---

**Última actualización**: 2025-11-06
