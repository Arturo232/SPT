# Arquitectura del Sistema — SPT (Analizador de Sistemas de Potencia)

Este documento describe la arquitectura modular y el flujo de datos del analizador de sistemas de potencia en Python.

---

## 1. Visión General por Capas

El proyecto está diseñado bajo una **arquitectura por capas desacopladas**:

```
+-------------------------------------------------------------+
|                     CAPA DE PRESENTACIÓN                    |
|  - CLI (main.py, menus.py)                                  |
|  - Consola / REPL (asistente.py)                            |
|  - GUI CustomTkinter (gui/app.py, views/*.py)               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      CAPA DE SERVICIOS                      |
|  - Fachadas unificadas (services.py)                        |
|  - Gestor de red (circuito.py: CircuitoTrifasico/Mono)      |
|  - Despachador de GUI (resolver.py)                         |
|  - Metadatos y procedimientos (.meta)                       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      DOMINIO / MÓDULOS                      |
|  - modules/circuitos.py                                     |
|  - modules/potencia_compleja.py                             |
|  - modules/correccion_fp.py                                 |
|  - modules/flujo_potencia.py                                |
|  - modules/sistemas_trifasicos.py                           |
|  - modules/per_unit.py                                      |
|  - modules/transformadores.py                               |
|  - modules/componentes_simetricas.py                        |
|  - modules/cortocircuitos.py                                |
|  - modules/maquinas.py                                      |
|  - modules/estabilidad.py                                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                       NÚCLEO (CORE)                         |
|  - core.py: álgebra fasorial, Ohm, potencias, validaciones  |
|  - errors.py: excepciones tipadas (AnalizadorError)         |
|  - config.py: catálogo canónico de mensajes y config.json   |
|  - utils.py: formateo puro, exportación CSV/JSON/TXT        |
|  - viz.py: gráficos fasoriales y triángulos de potencia     |
+-------------------------------------------------------------+
```

---

## 2. Responsabilidades por Capa

### A. Núcleo Matemático (`core.py`)
- Define las funciones matemáticas puras elementales:
  - Conversión polar $\leftrightarrow$ rectangular.
  - Ley de Ohm fasorial ($V = I \cdot Z$, $I = V / Z$).
  - Potencia compleja $S = V \cdot I^*$, factor de potencia $\text{FP} = \cos(\phi)$.
  - Cálculo de impedancias y admitancias equivalentes ($Z = 1/Y$).
- Funciones estrictamente deterministas sin efectos secundarios.
- Realiza validaciones previas de tipo y rango con `validate_input()`.

### B. Módulos de Especialidad (`modules/*.py`)
- Implementan los algoritmos específicos de cada área de Sistemas Eléctricos de Potencia:
  - Flujo de carga no lineal ($N$-barras con Newton-Raphson y Gauss-Seidel).
  - Transformación de componentes simétricas de Fortescue ($abc \leftrightarrow 012$).
  - Cálculo de fallas simétricas y asimétricas ($\text{SLG}$, $\text{L-L}$, $\text{D-L-G}$).
  - Ecuación de oscilación y criterio de áreas iguales para estabilidad transitoria.
  - Reducción de transformadores y análisis en sistema por unidad ($\text{p.u.}$).

### C. Capa de Servicios y Estado de Red (`services.py`, `circuito.py`, `resolver.py`)
- **Fachadas Seguras (`services.py`):**
  - Orquestan llamadas a múltiples funciones de dominio.
  - Atrapan excepciones internas y retornan estructuras de error consistentes.
  - Añaden el bloque `.meta` con las fórmulas empleadas y unidades del resultado.
- **Entorno de Red (`circuito.py`):**
  - Mantiene el estado del circuito (fuente, línea y cargas en paralelo).
  - Admite modo monofásico (`CircuitoMonofasico`) y trifásico balanceado (`CircuitoTrifasico`).
- **Resolvedor UI (`resolver.py`):**
  - Interfaz común consumida por las vistas gráficas o APIs.

### D. Capa de Presentación e Interfaces (`main.py`, `asistente.py`, `gui/`)
- **Consola de Comandos / REPL (`asistente.py`):**
  - Intérprete de lenguaje natural con diagnóstico de datos faltantes y sugerencias de comandos.
- **Menú Interactivo (`main.py`, `menus.py`):**
  - Navegación clásica por consola guiada por teclado.
- **GUI Moderna (`gui/app.py`):**
  - Aplicación de escritorio con CustomTkinter, soporte Dark/Light mode y vistas dinámicas en cards.

---

## 3. Manejo Unificado de Errores

Todos los errores del sistema están catalogados de forma unívoca con identificadores jerárquicos:

```text
analizador:<módulo>:<código>
```

Ejemplos:
- `analizador:core:fpInvalido`: El factor de potencia debe estar entre 0 y 1.
- `analizador:circuito:sinTension`: No se ha definido la tensión del sistema.
- `analizador:flujoCarga:sinSlack`: Se requiere exactamente una barra Slack.

Las excepciones se gestionan a través de la clase [`AnalizadorError`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/errors.py) y el catálogo canónico reside en [`config.py`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/config.py).
