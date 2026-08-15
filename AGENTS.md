# Guía de Antigravity y Agentes de IA — SPT (Sistemas de Potencia en Terminal)

Este archivo define las directrices arquitectónicas, estándares de desarrollo, convenciones matemáticas y reglas de contribución para agentes inteligentes y desarrolladores que trabajen en el repositorio **SPT / `analizador-sep`**.

---

## 1. Visión y Propósito del Proyecto

SPT es un analizador y calculador modular de **Sistemas Eléctricos de Potencia (SEP)** en Python (3.10+), portado y modernizado desde MATLAB. Proporciona:
- Núcleo de cálculo numérico puro (fórmulas analíticas, matrices de admitancia, flujos de carga, fallas, estabilidad).
- Capa de servicios desacoplada con contratos de datos y metadatos pedagógicos (`.meta`).
- Interfaces múltiples sobre el mismo backend:
  - **Consola interactiva / REPL** (`analizador.asistente.consola`).
  - **Menús interactivos CLI** (`analizador.menus` / `analizador.main`).
  - **Interfaz gráfica de usuario (GUI)** en CustomTkinter (`analizador.gui`).

---

## 2. Arquitectura y Reglas de Diseño

El proyecto sigue una estricta **arquitectura en capas**:

```
src/analizador/
├── core.py             # Funciones matemáticas elementales (puras, sin prints)
├── modules/            # Módulos de dominio por tema de SEP (puros)
├── services.py         # Fachadas / Servicios que orquestan cálculos y devuelven contratos + .meta
├── errors.py           # Excepciones estructuradas (AnalizadorError)
├── config.py           # Configuración general y catálogo de errores
├── utils.py            # Formateo de fasores/potencias, helpers de entrada y exportadores
├── viz.py              # Gráficos con matplotlib (fasores polares y triángulos P-Q-S)
├── circuito.py         # Estado de red y resolución de circuitos (1f y 3f)
├── asistente.py        # Wizard paso a paso y consola de comandos (REPL)
├── gui/                # Interfaz gráfica moderna con CustomTkinter
└── exercises.py        # Ejercicios verificados del Taller 2026 y ejemplos
```

### Reglas Críticas para Agentes:
1. **Separación de Lógica y Presentación:**
   - NUNCA agregar llamadas a `print()` o `input()` dentro de `core.py`, `modules/*.py`, `services.py` o `circuito.py`.
   - Las funciones de cálculo devuelven números, arreglos de `numpy` o `SimpleNamespace` con los resultados.
2. **Convención de Signos Eléctricos Estándar:**
   - Potencia compleja: $S = V \cdot I^*$
   - Reactiva $Q > 0 \implies$ Inductivo / FP en atraso (*lagging*).
   - Reactiva $Q < 0 \implies$ Capacitivo / FP en adelanto (*leading*).
   - Ángulos en grados para la interacción y radianes para cálculos trigonométricos.
3. **Manejo de Errores Tipados:**
   - Usar `error_analizador(modulo, codigo, formato, *args)` que lanza `AnalizadorError` con identificador `analizador:<modulo>:<codigo>`.
   - Registrar los códigos de error canónicos en `config.py` (`mensajes()`).
4. **Validación de Entradas:**
   - Usar `validate_input(kind, value, name)` en `core.py` para verificar tipos numéricos, factores de potencia válidos ($0 \le \text{FP} \le 1$), valores no nulos y frecuencias positivas.

---

## 3. Entorno de Desarrollo y Comandos Frecuentes

- **Instalación en modo editable con dependencias de desarrollo:**
  ```bash
  pip install -e .[dev]
  ```
- **Ejecutar suite completa de tests:**
  ```bash
  pytest
  # o vía python
  python -m pytest
  ```
- **Lanzar la interfaz CLI interactiva:**
  ```bash
  python -m analizador
  ```
- **Lanzar la interfaz gráfica (GUI):**
  ```bash
  analizador-gui
  # o vía python
  python -m analizador.gui.app
  ```

---

## 4. Estilo de Código y Buenas Prácticas

- Compatible con **Python 3.10+**.
- Seguir PEP 8. Mantener nombres de funciones claros en español/inglés técnico consistente con la base de código.
- En pruebas unitarias con `pytest`, usar tolerancias numéricas para comparaciones de punto flotante (`math.isclose` o `np.isclose`).
