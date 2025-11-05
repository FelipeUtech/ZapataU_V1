# Simulación de Ensayo de Carga de Zapata 🏗️

Programa completo para simular ensayos de carga de zapatas empotradas en suelos estratificados con comportamiento no lineal utilizando OpenSeesPy.

## 📋 Descripción

Este programa realiza análisis tridimensional por elementos finitos de ensayos de carga en zapatas. Permite simular:

- ✅ Zapatas empotradas a profundidad Df
- ✅ Suelo estratificado con n capas
- ✅ Materiales no lineales (modelo Drucker-Prager)
- ✅ Aplicación incremental de carga
- ✅ Curvas carga-asentamiento
- ✅ Visualización de resultados

## 🚀 Instalación

### Requisitos previos

- Python 3.8 o superior
- pip

### Instalar dependencias

```bash
pip install -r requirements.txt
```

## 📁 Estructura del proyecto

```
ZapataU_V1/
│
├── config.py                  # Configuración de parámetros
├── mesh_generator.py          # Generación de malla 3D
├── materials.py               # Definición de materiales no lineales
├── model_builder.py           # Constructor del modelo completo
├── load_test_analyzer.py      # Análisis de ensayo de carga
├── post_processor.py          # Post-procesamiento y visualización
├── main.py                    # Script principal
├── requirements.txt           # Dependencias de Python
└── README.md                  # Este archivo
```

## 🎯 Uso

### Ejecución básica

```bash
python main.py
```

Esto ejecutará la simulación completa con los parámetros por defecto y generará:
- Curvas carga-asentamiento
- Gráficos de presión de contacto
- Módulo de reacción del suelo
- Reportes en texto y CSV

### Opciones de línea de comandos

```bash
# Ver configuración actual sin ejecutar
python main.py --config

# Ejecutar sin mostrar gráficos
python main.py --no-plots

# Ejecutar sin exportar resultados
python main.py --no-export
```

## ⚙️ Configuración

Edita el archivo `config.py` para modificar:

### Geometría de la zapata

```python
FOOTING_WIDTH = 2.0      # Ancho (m)
FOOTING_LENGTH = 2.0     # Largo (m)
FOOTING_THICKNESS = 0.5  # Espesor (m)
EMBEDMENT_DEPTH = 1.5    # Profundidad de desplante Df (m)
```

### Estratos de suelo

```python
SOIL_LAYERS = [
    {
        'name': 'Arcilla blanda',
        'depth_top': 0.0,
        'depth_bottom': 3.0,
        'E': 10000.0,           # Módulo de Young (kPa)
        'nu': 0.35,             # Coeficiente de Poisson
        'rho': 1700.0,          # Densidad (kg/m³)
        'cohesion': 25.0,       # Cohesión (kPa)
        'friction_angle': 15.0, # Ángulo de fricción (°)
    },
    # ... más estratos
]
```

### Parámetros del ensayo

```python
LOAD_TEST = {
    'max_load': 1000.0,     # Carga máxima (kN)
    'num_steps': 20,        # Número de incrementos
    'load_type': 'vertical',
}
```

## 📊 Resultados

Los resultados se guardan en el directorio `results/`:

- `load_settlement.png` - Curva carga-asentamiento
- `pressure_settlement.png` - Presión de contacto vs asentamiento
- `secant_modulus.png` - Módulo de reacción del suelo
- `settlement_profile.png` - Perfil de asentamientos
- `summary_report.txt` - Reporte completo en texto
- `detailed_results.csv` - Datos tabulados
- `model_info.txt` - Información del modelo

## 🧪 Ejemplos de uso

### Ejemplo 1: Zapata en arcilla blanda

```python
# En config.py
FOOTING_WIDTH = 1.5
FOOTING_LENGTH = 1.5
EMBEDMENT_DEPTH = 1.0

SOIL_LAYERS = [
    {
        'name': 'Arcilla blanda',
        'depth_top': 0.0,
        'depth_bottom': 10.0,
        'E': 5000.0,
        'cohesion': 20.0,
        'friction_angle': 0.0,  # φ = 0 para arcilla saturada
    }
]
```

### Ejemplo 2: Zapata en suelo multicapa

```python
SOIL_LAYERS = [
    {'name': 'Arena suelta', 'depth_top': 0.0, 'depth_bottom': 2.0, ...},
    {'name': 'Arcilla', 'depth_top': 2.0, 'depth_bottom': 5.0, ...},
    {'name': 'Arena densa', 'depth_top': 5.0, 'depth_bottom': 15.0, ...},
]
```

## 🔬 Modelos constitutivos

El programa utiliza:

- **Drucker-Prager**: Para suelos friccionantes (arenas, gravas)
- **ElasticIsotropic**: Fallback si Drucker-Prager no está disponible
- **Concreto**: Elástico lineal para la zapata

## 📈 Interpretación de resultados

### Curva carga-asentamiento

- Pendiente inicial: rigidez del sistema
- Curvatura: comportamiento no lineal del suelo
- Asentamiento final: capacidad de servicio

### Módulo de reacción (k)

```
k = q / s
```

Donde:
- q = presión de contacto (kPa)
- s = asentamiento (m)
- k = módulo de reacción (kPa/m)

## ⚠️ Limitaciones

- Modelo elástico-perfectamente plástico (Drucker-Prager)
- No considera efectos dinámicos
- No incluye nivel freático
- Geometría simplificada de la zapata

## 🛠️ Desarrollo futuro

- [ ] Implementar modelos constitutivos avanzados (Cam-Clay, Hardening Soil)
- [ ] Incluir nivel freático y presión de poros
- [ ] Análisis de consolidación
- [ ] Carga cíclica
- [ ] Interfaz gráfica (GUI)
- [ ] Optimización de diseño

## 📚 Referencias

1. Bowles, J.E. (1996). Foundation Analysis and Design. McGraw-Hill.
2. Das, B.M. (2015). Principles of Foundation Engineering. Cengage Learning.
3. OpenSeesPy Documentation: https://openseespydoc.readthedocs.io/

## 👨‍💻 Autor

Desarrollado con Claude AI

## 📄 Licencia

MIT License - Uso libre para fines académicos y profesionales

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en GitHub.

---

**¡Buena suerte con tus simulaciones! 🎉**
