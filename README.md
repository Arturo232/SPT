# SPT — Sistemas de Potencia en Terminal

[![CI](https://github.com/tu-usuario/analizador-sep/actions/workflows/ci.yml/badge.svg)](https://github.com/tu-usuario/analizador-sep/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Versión-1.7.0-brightgreen)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/Tests-150%20pasando-success)](tests/)
[![Typed](https://img.shields.io/badge/Tipado-mypy-blueviolet)](https://mypy-lang.org/)

Consola de comandos eléctricos: port del proyecto MATLAB `SEP` a Python.
Analizador académico modular de sistemas de potencia (circuitos monofásicos,
potencia compleja, corrección del factor de potencia, flujo de potencia,
sistemas trifásicos, p.u., transformadores, flujo de carga N-barras,
componentes simétricas, cortocircuitos, máquinas eléctricas y estabilidad),
con una **consola de comandos** para resolver circuitos monofásicos y
trifásicos balanceados de forma interactiva y una **interfaz gráfica** moderna.

---

## Instalación

```bash
pip install -e .[dev]
```

---

## ¿Cómo abrir el programa?

```bash
analizador          # consola interactiva REPL (experiencia por defecto)
analizador-gui      # interfaz gráfica (customtkinter, modo oscuro)
python -m analizador
```

Al iniciar, se muestra un **banner de bienvenida** en arte ASCII y se entra
en una **consola interactiva (REPL)** con autocompletado, navegación de
historial y comandos asistidos (al estilo Claude Code). Escriba `help` para
ver los comandos:

```
SPT> help
```

| Comando | Acción |
|---|---|
| `menu` / `legacy` | Abre el menú clásico navegable. |
| `gui` | Abre la interfaz gráfica. |
| `circuito` / `consola` | Consola de circuitos (mono/tri). |
| `potencia`, `correccion`, `flujo`, `trifasico`, `per-unit` | Cálculos asistidos paso a paso. |
| `taller` / `ejercicios` | Ejercicios del Taller 2026. |
| `modulos` | Lista los módulos temáticos. |
| `banner`, `version`, `help` | Presentación, versión y ayuda. |
| `salir` / `exit` / `quit` / `0` | Sale de la consola. |

El menú clásico anterior sigue disponible como `python -m analizador.main` o
con el comando `menu` dentro de la REPL.

---

## Interfaz gráfica (GUI)

`analizador-gui` abre una ventana moderna (customtkinter, modo oscuro por
defecto) con:

- **Sidebar** fijo: navegación por temas y selector de tema
  (Dark / Light / System).
- **Área principal dinámica** con tarjetas (cards) de Entradas y
  Resultados por tema:
  - Potencia compleja (desde P/FP o desde V/Z).
  - Corrección de factor de potencia.
  - Circuito monofásico/trifásico (fuente + línea + cargas en paralelo).
  - Sistema por unidad (p.u.).
- **Feedback visual inmediato**: barra de estado con mensajes de éxito
  (verde) o error (rojo) y barra de progreso.
- **Validación de entradas** con placeholders y alertas visuales.
- **Desacoplamiento**: la GUI solo invoca al backend (`analizador.services`,
  `analizador.core.resolver`, `analizador.core.circuito`); los resultados son idénticos a la consola.

---

## Consola de comandos (opción C)

Una terminal propia para armar y resolver circuitos **monofásicos (1φ)** y
**trifásicos balanceados (3φ)**. El modo se elige con `modo` o al resolver
con `resolver mono` / `resolver tri`; cada modo guarda su propio circuito.

### Ejemplo rápido (trifásico con dos cargas)

```
circuito> fuente 207.85           # V_L = 207.85 V (V_f = 120 V)
circuito> linea 2+4j              # Z_línea = 2 + j4 Ω
circuito> carga Delta 60-45j      # carga 1 (Delta, capacitiva)
circuito> add Y 30+40j            # carga 2 (Y, inductiva)
circuito> resolver                # reporte completo
circuito> grafica fasores         # diagrama fasorial
circuito> exportar reporte.txt    # guardar resultados
```

### Ejemplo rápido (monofásico)

```
circuito> modo mono
circuito> fuente 200              # V = 200 V
circuito> carga 0.8+5.6j          # sin conexión Y/Δ en 1φ
circuito> add 8-16j
circuito> resolver
```

### Comandos

| Comando | Qué hace |
|---|---|
| `modo mono` / `modo tri` | Cambia el modo (1φ o 3φ). |
| `resolver mono` / `resolver tri` / `resolver` | Resuelve en el modo indicado o el actual. |
| `fuente <V>` | Tensión de la fuente (con ángulo opcional). |
| `linea <Z>` | Impedancia de línea en serie. |
| `carga <Z>` (mono) / `carga <Y\|Delta> <Z>` (tri) | Agrega una carga en paralelo. |
| `pcarga <S>` / `pcarga <Y\|Delta> <S>` | Carga definida por su potencia. |
| `corriente <I>` | Corriente de la fuente como dato. |
| `vcarga <V>` | Tensión en la carga como dato. |
| `cargas`, `ver`, `limpiar` | Estado, listado y limpieza. |
| `vf`, `vl`, `il`, `if`, `s`, `detalle <n>` | Consulta de variables tras resolver. |
| `variables` / `todo` | Reporte completo. |
| `exportar <archivo>` | Exporta el reporte (TXT/JSON/CSV/XLSX). |
| `grafica fasores` / `grafica potencia` | Diagrama fasorial o triángulo P-Q-S. |
| `ayuda`, `salir` | Ayuda y fin. |

### Formato de impedancias y fasores

**Rectangular** (con `j` o `i`):
```
10+5j   2-8j   4j   j5   10
```

**Polar** (ángulos en grados, con o sin `deg`/`°`):
```
30 angulo 53.13   50/30   30∠53.13   30<53.13   50 exp(30)   50 cis(30)
```
Sin el símbolo de ángulo en el teclado, use `@` (arroba) o la letra `a`:
```
30@53.13   30a53.13   30 a 53.13
```

**R y X por separado**: `linea 10 20` o `carga Y 10 20`.

---

## Uso desde Python (API)

```python
from analizador.core import power_from_vi, polar_to_complex

v = polar_to_complex(200, 0)   # 200∠0° V
i = 4 - 8j                     # A
r = power_from_vi(v, i)
print(r.P, r.Q, r.fp)         # W, var, factor de potencia
```

---

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/GUIA_USUARIO.md`](docs/GUIA_USUARIO.md) | **Manual completo de uso** (CLI, consola, GUI, ejemplos) |
| [`docs/AI_CONTEXT.md`](docs/AI_CONTEXT.md) | Mapa del proyecto para agentes IA y copilots |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Diseño de capas, servicios y catálogo de errores |
| [`docs/contratos.md`](docs/contratos.md) | Esquemas de retorno de `service_*` y bloque `.meta` |
| [`docs/presentacion.md`](docs/presentacion.md) | Formateo fasorial, unidades SI y exportación |
| [`docs/materiales.md`](docs/materiales.md) | Trazabilidad bibliográfica (Stevenson, Saadat, Chapman) |
| [`docs/consola.md`](docs/consola.md) | Guía completa de la consola de comandos |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Historial de fases y estado del proyecto |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de versiones |
| [`AGENTS.md`](AGENTS.md) | Reglas de arquitectura para agentes IA |

---

## Estructura

```text
analizador/
├── main.py                  # Punto de entrada (menú principal, opción C/A/1-13)
├── config.py                # Configuración por defecto + catálogo de mensajes
├── errors.py                # Error analizador (analizador:<modulo>:<codigo>)
├── utils.py                 # Entrada, formateo, presentación, exportación
│
├── core/                    # MODELO: lógica matemática y de dominio puro
│   ├── base.py              # Núcleo matemático (V, I, Z, Y, S, FP, validaciones)
│   ├── circuito.py          # CircuitoTrifasico y CircuitoMonofasico (estado de red)
│   ├── resolver.py          # Lógica pura de la GUI
│   └── exercises.py         # Ejercicios del taller 2026 + ejemplos
│
├── gui/                     # VISTA: interfaz gráfica y presentación
│   ├── app.py               # Ventana principal (customtkinter)
│   ├── components.py        # Componentes reutilizables
│   ├── views/               # Vistas por tema
│   ├── menus.py             # Menús interactivos CLI
│   └── viz.py               # Gráficas (fasores, triángulo de potencias)
│
├── controllers/             # CONTROLADOR: enlace entre GUI y Core
│   └── __init__.py          # Reservado para futuros controladores
│
├── services/                # SERVICIOS: fachadas y asistentes
│   ├── services.py          # Capa de servicios (fachadas, contratos + .meta)
│   └── asistente.py         # Consola de comandos (mono/tri) y asistente guiado
│
└── modules/                 # Un tema del curso por módulo (funciones puras)
```

---

## Pruebas

```bash
pytest                                           # todos los tests
pytest --cov=analizador --cov-report=term       # con cobertura
python -m mypy src/analizador                   # chequeo de tipos
```

---

## Convenciones matemáticas

- Potencia compleja: `S = V * conj(I)`.
- `Q > 0` → inductiva / FP en atraso; `Q < 0` → capacitiva / adelanto.
- Capacitor: `Qc < 0` (aporta reactiva negativa).
- Trifásico balanceado: `V_f = V_L/√3`, `S3φ = 3·V_f·conj(I)`,
  `Z_Y = Z_Δ/3`.
- Flujo de potencia: ángulos en grados; funciones trigonométricas en grados.
