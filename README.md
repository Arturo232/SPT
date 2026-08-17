# ⚡ SPT — Sistemas de Potencia en Terminal

[![CI](https://github.com/tu-usuario/analizador-sep/actions/workflows/ci.yml/badge.svg)](https://github.com/tu-usuario/analizador-sep/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Versi%C3%B3n-1.0.0-brightgreen)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/Tests-257%20pasando-success)](tests/)
[![Typed](https://img.shields.io/badge/Tipado-mypy-blueviolet)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/Licencia-Acad%C3%A9mica-lightgrey)](LICENSE)

> **Analizador académico modular de Sistemas Eléctricos de Potencia (SEP)**:
> port del proyecto MATLAB `SEP` a Python, con consola interactiva (REPL),
> resolución académica inciso por inciso y motor de visualización fasorial
> vectorial.

---

## 🚀 Inicio Rápido (Instalación y Ejecución)

### 🐧 Linux (Arch Linux / Debian / Ubuntu) — Bash

```bash
git clone https://github.com/Arturo232/SPT.git
cd SPT
python -m venv .venv
source .venv/bin/activate
pip install -e .
spt
```

### 🪟 Windows (PowerShell / CMD)

```powershell
git clone https://github.com/Arturo232/SPT.git
cd SPT
python -m venv .venv
.venv\Scripts\activate
pip install -e .
spt
```

> 💡 **¿Qué es `spt`?**
> Al clonar el repositorio e instalar con `pip install -e .`, la aplicación
> queda registrada globalmente bajo el comando `spt` (como ejecutable del
> entorno, en `bin/` de Linux o `Scripts\` de Windows). Por eso, una vez
> instalado, puede abrir la consola interactiva en **cualquier momento**
> escribiendo simplemente `spt` en la terminal. El punto de entrada `main()`
> de `analizador/cli/console.py` es el que inicia la REPL.

---

## 📖 Descripción General

SPT es un **analizador y calculador modular de SEP** escrito en Python 3.10+,
portado y modernizado desde MATLAB. Proporciona:

- 🧮 **Núcleo de cálculo numérico puro** — fórmulas analíticas, matrices de
  admitancia, flujos de carga, fallas, estabilidad (sin `print`, sin `input`).
- 🔌 **Capa de servicios desacoplada** — fachadas `service_*` con contratos de
  datos y metadatos pedagógicos (bloque `.meta`).
- ⌨️ **Consola REPL moderna** — autocompletado, historial, navegación por
  contextos, gramática por niveles y notación polar estándar `M ∠ A°`.
- 🖼️ **Interfaces múltiples sobre el mismo backend**:
  - **Consola interactiva / REPL** (`analizador`) — la experiencia por defecto.
  - **Interfaz gráfica (GUI)** en CustomTkinter (`analizador-gui`).
  - **Menús interactivos CLI** (`analizador.main`, comando `menu`).

### ✨ Características destacadas

| Área | Funcionalidad |
|---|---|
| 🔺 Redes trifásicas | Fuente `L:`/`F:`, `N` cargas en paralelo (Y y Δ), tramos de línea, desglose por fase (3 hilos) |
| 1️⃣ Redes monofásicas | Fuente + línea + cargas en paralelo, desglose completo |
| 🎓 Modo taller | Resolución académica inciso por inciso **(a)–(j)** con `--taller` |
| 📐 Fasores vectoriales | Diagramas polares con flechas, colores por fase y etiquetas `Van: 120.08 V ∠ -30.0°` |
| 🔧 Corrección de FP | kVAR requeridos y capacitancia por fase en µF |
| 📊 Análisis extendido | $Y_{eq}$, pérdidas, eficiencia, regulación, LKC y balance de potencia |
| ✅ Calidad | 257 pruebas unitarias, tipado `mypy`, cobertura con `pytest-cov` |

---

## 🏗️ Arquitectura MVC

El proyecto sigue una estricta **arquitectura en capas**:

```
src/analizador/
├── __init__.py             # Versión del paquete
├── main.py                 # Menú principal clásico (CLI)
├── config.py               # Configuración general y catálogo de errores
├── errors.py               # Excepciones estructuradas (AnalizadorError)
├── utils.py                # Formateo de fasores/potencias, helpers y exportadores
│
├── core/                   # MODELO: lógica matemática y de dominio pura
│   ├── base.py             # Funciones matemáticas elementales (puras, sin prints)
│   ├── circuito.py         # CircuitoTrifasico / CircuitoMonofasico (estado de red)
│   ├── resolver.py         # Resolución de cálculos para la GUI
│   └── exercises.py        # Ejercicios verificados del Taller 2026
│
├── cli/                    # CONSOLA: REPL, parser de redes y gramática
│   ├── console.py          # REPL interactiva (rich + prompt_toolkit)
│   ├── gramatica.py        # Gramática por niveles (sistema → componente → banderas)
│   ├── banner.py           # Banner de bienvenida
│   └── legacy_menu.py      # Menú clásico navegable
│
├── gui/                    # VISTA: componentes visuales y renderizado
│   ├── app.py              # Ventana principal (CustomTkinter)
│   ├── components.py       # Componentes reutilizables
│   ├── views/              # Vistas por tema
│   ├── menus.py            # Menús interactivos CLI
│   └── viz.py              # Gráficos con matplotlib (fasores polares y P-Q-S)
│
├── controllers/            # CONTROLADOR: enlace entre GUI y Core (reservado)
│
├── services/               # SERVICIOS: fachadas y asistentes
│   ├── services.py         # Fachadas service_* (contratos + .meta)
│   └── asistente.py        # Wizard paso a paso y consola de comandos legacy
│
└── modules/                # Módulos de dominio por tema de SEP (puros)
```

| Capa | Responsabilidad | Regla de oro |
|---|---|---|
| `core/` | Matemática y dominio | ❌ Sin `print` ni `input` |
| `cli/` | Consola y presentación terminal | Único lugar con `input` del usuario |
| `gui/` | Ventanas y gráficos | Solo invoca `services`/`core` |
| `services/` | Fachadas y contratos | Devuelve `SimpleNamespace` + `.meta` |
| `modules/` | Un tema del curso por módulo | Funciones puras, sin estado |

> ℹ️ **Convención de signos eléctricos estándar**
> - Potencia compleja: $S = V \cdot I^*$
> - $Q > 0$ → Inductivo / FP en atraso (*lagging*)
> - $Q < 0$ → Capacitivo / FP en adelanto (*leading*)
> - Ángulos en grados para la interacción, radianes para cálculos.

---

## 📐 Marco Teórico de Ingeniería

### 1. Reducción de sistemas trifásicos balanceados

En un sistema **trifásico balanceado**, las tres fases son idénticas en
magnitud y desfasadas $120^\circ$ entre sí. Todo el sistema se reduce al
**circuito equivalente monofásico de la fase 'a'**:

$$V_{LN} = \frac{V_{LL}}{\sqrt{3}}, \qquad I_L = \frac{V_{LN}}{Z_{eq}}$$

| Magnitud | Relación |
|---|---|
| Tensión fase-neutro | $V_{LN} = V_{LL}/\sqrt{3}$ |
| Potencia trifásica | $S_{3\phi} = 3\, V_f \cdot I_f^* = \sqrt{3}\, V_{LL} \cdot I_L^*$ |
| Corriente en Δ | $I_f = \dfrac{I_L}{\sqrt{3}}\, e^{\,j30^\circ}$ |
| Tensión de fase en Δ | $V_f = V_{LL}$ |

### 2. Conversiones Delta–Estrella ($\Delta \to Y$)

Para reducir cargas en paralelo mixtas (Y + Δ) a un único equivalente:

$$Z_Y = \frac{Z_\Delta}{3}, \qquad Z_\Delta = 3\,Z_Y$$

```text
Carga Y (estrella):   V_f = V_LN ,  I_f = I_L
Carga Δ (delta):      V_f = V_LL ,  I_f = I_L·e^(j30°)/√3
```

La impedancia total con la línea en serie es:

$$Z_{total} = Z_{línea} + Z_{cargas,eq}, \qquad Z_{cargas,eq} = \left( \sum_i \frac{1}{Z_{Y,i}} \right)^{-1}$$

### 3. Potencia compleja y factor de potencia

$$S = P + jQ = V \cdot I^*$$

| Cantidad | Fórmula |
|---|---|
| Potencia activa | $P = |S|\cos\varphi$ [W] |
| Potencia reactiva | $Q = |S|\sin\varphi$ [var] |
| Potencia aparente | $\|S\| = \sqrt{P^2+Q^2}$ [VA] |
| Factor de potencia | $fp = \dfrac{P}{|S|} = \cos\varphi$ |

### 4. Corrección del factor de potencia (µF)

Para llevar una carga de $fp_1$ a $fp_2$ se inyecta reactiva capacitiva:

$$Q_c = P \left( \tan\varphi_1 - \tan\varphi_2 \right), \qquad
X_c = \frac{V^2}{|Q_c|}, \qquad
C = \frac{1}{2\pi f X_c} \;[\text{F}]$$

La capacitancia por fase en microfaradios es:

$$C_{\mu F} = \frac{10^6}{2\pi f X_c}$$

> 💡 Un banco de capacitores **no cambia la potencia activa**: reduce la
> corriente de línea y las pérdidas al compensar la reactiva inductiva.

---

## ⌨️ Guía de la Consola REPL / CLI

### Instalación

```bash
pip install -e .[dev]
```

### 🚀 Instalación y Uso Ejecutable (Linux & Windows)

SPT se empaqueta como un **ejecutable de consola** invocable con el comando
`spt` en cualquier terminal, tanto en Linux como en Windows. El `entry point`
`main()` de `analizador/cli/console.py` es el que inicia la REPL.

#### 🐧 Linux (bash)

```bash
cd /ruta/del/proyecto
pip install -e .
```

Luego, simplemente escriba:

```bash
spt
```

#### 🪟 Windows (PowerShell)

```powershell
cd C:\ruta\del\proyecto
pip install -e .
```

Luego, simplemente escriba:

```powershell
spt
```

> 💡 **Nota:** `pip` genera el ejecutable `spt` automáticamente:
> - **Linux/macOS** → en `bin/` del entorno (e.g. `.venv/bin/spt`).
> - **Windows** → en `Scripts\` del entorno (e.g. `.venv\Scripts\spt.exe`).
>
> Si usa un entorno virtual, actívelo primero para que `spt` quede en el
> `PATH`.

### Arranque

```bash
spt                 # consola interactiva REPL (comando ejecutable)
analizador          # alias compatible
analizador-gui      # interfaz gráfica (CustomTkinter, modo oscuro)
python -m analizador
```

Al iniciar se muestra el banner y el prompt `SEP>` con autocompletado,
historial y navegación por contextos. Escriba `help` para ver todos los
comandos.

### Tabla de comandos

| Comando | Acción |
|---|---|
| `trifasico, tri, 3f` | Red trifásica balanceada: `--fuente --cargas --linea`, o asistido |
| `monofasico, mono, 1f` | Red monofásica: `--fuente --cargas --linea`, o asistido |
| `graficar, fasores, plot` | Visualiza los fasores del último circuito resuelto |
| `potencia` | Calcula potencia compleja (asistido) |
| `correccion` | Corrige el factor de potencia (asistido) |
| `flujo` | Flujo de potencia entre dos fuentes (asistido) |
| `per-unit` | Convierte al sistema por unidad (asistido) |
| `taller, ejercicios` | Ejecuta los ejercicios del Taller 2026 |
| `circuito, consola` | Consola de circuitos legacy (mono/tri) |
| `menu, legacy` | Menú clásico navegable |
| `gui` | Abre la interfaz gráfica |
| `modulos` | Lista los módulos temáticos |
| `banner, intro` | Vuelve a mostrar el banner |
| `version` | Muestra la versión |
| `help, ?` | Ayuda con la lista de comandos |
| `clc, cls` | Limpia la pantalla de la terminal |
| `salir, exit, quit, 0` | Sale de la consola |

### 🔺 Ejemplo: red trifásica con dos cargas y línea

```bash
SEP> trifasico --fuente L:216.51[30] --linea 2.95+j6.3 --cargas Y:36+j40 D:63-j51
```

- `L:` → tensión de **línea** ($V_{LL}$); `F:` → tensión de fase ($V_{LN}$).
  Sin prefijo se asume `L`.
- `[30]` → ángulo en grados (notación polar).
- Cargas: `Y:36+j40` (estrella) y `D:63-j51` (delta).
- La salida muestra 6 paneles: datos, reducción Δ→Y, variables de estado,
  balance de potencia, desglose por fase (3 hilos) e interpretación técnica.

```bash
SEP> trifasico --fuente F:120[0] --cargas Y:4+j2 --lineas 8+j4 2+j1
SEP> monofasico --fuente 120 --cargas 4+j2 5-j4 --linea 8+j4
```

### 🎓 Modo taller: resolución inciso por inciso (a)–(j)

```bash
SEP> trifasico --fuente L:216.51[30] --linea 2.95+j6.3 --cargas Y:36+j40 D:63-j51 --taller
```

`--taller` (alias `--resolver-incisos`) agrega la resolución académica
completa:

| Inciso | Contenido |
|---|---|
| (a) | Corriente de la fuente $I_L$ |
| (b) | Potencia compleja total (valores de fase) $S_{3\phi}$ |
| (c) | Potencia compleja total (valores de línea) |
| (d) | Tensión de línea en el nodo de cargas |
| (e) | Fasorial de tensiones Estrella |
| (f) | Corriente por fase de cada carga (Y y Δ) |
| (g) | Corrientes de malla Delta |
| (h) | Coordenadas fasoriales de corrientes Delta |
| (i) | Desglose de potencia $P$ y $Q$ |
| (j) | Corrección de FP (kVAR y µF por fase) |

Cada inciso muestra la variable, su valor polar `M ∠ A°` y la forma
rectangular de apoyo `(a + jb)`:

```text
╭──────────────────── Inciso (a) — Corriente de la fuente ─────────────────────╮
│ I_L = 71.78 ∠ -11.2°  (70.42 - j13.94)                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Control del inciso (j):

```bash
SEP> trifasico --fuente 208 --cargas Y:3+j4 --taller --carga-fp 1 --fp 0.95
```

### 📐 Visualización: `graficar` / `fasores`

Tras resolver, el resultado queda guardado en la sesión; el comando
`graficar` lo dibuja con **fasores vectoriales** (flechas desde el origen,
colores por fase: A rojo, B naranja, C azul):

```bash
SEP> graficar                 # dos paneles: tensiones + corrientes
SEP> graficar --tensiones     # solo fasores de tensión
SEP> graficar --corrientes    # solo fasores de corriente
SEP> graficar --potencia      # triángulo P-Q-S
SEP> graficar --guardar fasores.png   # exporta PNG/PDF sin abrir ventana
```

**Modo monofásico (equivalente 1 hilo):**

```bash
SEP> graficar -m              # V_a e I_a (fase-neutro) — alias --monofasico/--1f/--1p
SEP> graficar --1f --tensiones
```

Si el último circuito resuelto fue monofásico, `graficar` entra
automáticamente en modo 1φ. Todo en una sola línea:

```bash
SEP> trifasico --fuente l:207.85[0] --linea 2+j4 --cargas y:30+j40 d:60-45j --taller --graficar -m
```

### 🧹 Comandos de entorno

```bash
SEP> clc            # limpia la pantalla (alias cls)
SEP> banner         # vuelve a mostrar el banner
SEP> version        # muestra la versión
SEP> help           # ayuda completa
SEP> salir          # sale (exit / quit / 0)
```

### Gramática por niveles (alternativa sin banderas `--`)

```bash
SEP> trifasico fuente --conexion estrella --v-rms 208
SEP> trifasico carga --potencia-activa 1200 --factor-potencia 0.9 --tipo inductivo
SEP> monofasico linea --z 8+j4
```

---

## 🖼️ Galería Visual

> 📸 Capturas de pantalla pendientes de agregar a `docs/images/`.

### Tabla de resultados CLI

![Tabla de Resultados CLI](docs/images/cli_resultados.png)

### Diagrama fasorial vectorial (polo polar)

![Diagrama Fasorial Vectorial](docs/images/fasores_polares.png)

### Resolución de incisos del taller

![Resolución de Incisos de Taller](docs/images/taller_incisos.png)

---

## 🧪 Guía de Instalación y Pruebas

### Dependencias

| Paquete | Uso |
|---|---|
| `numpy` / `scipy` | Núcleo numérico |
| `rich` / `prompt_toolkit` | Consola REPL moderna |
| `matplotlib` | Diagramas fasoriales y triángulo P-Q-S |
| `customtkinter` | Interfaz gráfica |

### Ejecutar las pruebas

```bash
pytest                                          # suite completa (257 tests)
pytest --cov=analizador --cov-report=term       # con cobertura
python -m mypy src/analizador                   # chequeo de tipos
```

> ✅ Las pruebas corren en modo headless (`matplotlib.use("Agg")`) — no
> requieren pantalla activa.

### Uso desde Python (API)

```python
from analizador.core import power_from_vi, polar_to_complex

v = polar_to_complex(200, 0)   # 200∠0° V
i = 4 - 8j                     # A
r = power_from_vi(v, i)
print(r.P, r.Q, r.fp)          # W, var, factor de potencia
```

---

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [`docs/GUIA_USUARIO.md`](docs/GUIA_USUARIO.md) | Manual completo de uso (CLI, consola, GUI, ejemplos) |
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

## 🧾 Convenciones matemáticas

- Potencia compleja: `S = V * conj(I)`.
- `Q > 0` → inductiva / FP en atraso; `Q < 0` → capacitiva / adelanto.
- Capacitor: `Qc < 0` (aporta reactiva negativa).
- Trifásico balanceado: `V_f = V_L/√3`, `S3φ = 3·V_f·conj(I)`, `Z_Y = Z_Δ/3`.
- Flujo de potencia: ángulos en grados; funciones trigonométricas en grados.
- Exportaciones: carpeta configurable `resultados/` (o `SEP_EXPORT_DIR`).

---

<div align="center">

**SPT v1.0.0** — Suite CLI trifásica y motor fasorial completo.

Hecho con 💛 para la enseñanza de Sistemas Eléctricos de Potencia.

</div>
