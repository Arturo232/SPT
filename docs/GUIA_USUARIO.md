# Guía de Usuario — SPT (Sistemas de Potencia en Terminal)

**Versión 1.7.0 | Python 3.10+**

Esta guía explica cómo instalar, abrir y usar el programa en todas sus interfaces: menú CLI, consola de comandos e interfaz gráfica (GUI).

---

## Instalación

### Requisitos previos
- Python 3.10 o superior instalado
- `pip` disponible en la terminal

### Instalar el paquete

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pip install -e .[dev]
```

Esto instala el programa en modo editable junto con todas las dependencias (numpy, scipy, matplotlib, customtkinter, pytest).

---

## ¿Cómo abrir el programa?

El programa tiene **tres formas de uso**:

### 1. 🖥️ Menú CLI (línea de comandos)

```bash
analizador
# o equivalentemente:
python -m analizador
```

Se abre un **menú numerado interactivo** en la terminal con todos los módulos del programa.

### 2. 💻 Consola de comandos (recomendada para ejercicios)

Desde el menú CLI, presiona **`C`** (o escribe `c`) para entrar a la consola.

También puedes ir directo:
```bash
analizador
# → presiona C
```

### 3. 🪟 Interfaz Gráfica (GUI)

```bash
analizador-gui
# o equivalentemente:
python -m analizador.gui.app
```

Se abre una **ventana moderna** con modo oscuro por defecto, sidebar de navegación y formularios visuales.

---

## Menú CLI — Opciones disponibles

Cuando ejecutas `analizador`, verás este menú:

```
══════════════════════════════════════════════
   SPT — Sistemas de Potencia en Terminal
══════════════════════════════════════════════
  C  → Consola de comandos (RECOMENDADO)
  A  → Asistente guiado trifásico
  ─────────────────────────────────────────
  1  → Circuitos monofásicos
  2  → Potencia compleja
  3  → Corrección de factor de potencia
  4  → Flujo de potencia (dos fuentes)
  5  → Sistemas trifásicos balanceados
  6  → Sistema por unidad (p.u.)
  7  → Transformadores
  8  → Flujo de carga N-barras
  9  → Componentes simétricas
  10 → Cortocircuitos
  11 → Máquinas eléctricas (generador)
  12 → Estabilidad transitoria
  ─────────────────────────────────────────
  13 / T → Ejercicios del Taller 2026
  H  → Ayuda / Convenciones de signos
  S  → Salir
```

Escribe el número o letra correspondiente y presiona Enter.

---

## Consola de Comandos — Uso Detallado

La consola es un **REPL interactivo** que permite armar y resolver circuitos eléctricos escribiendo comandos. Soporta circuitos **monofásicos (1φ)** y **trifásicos balanceados (3φ)**.

### Prompt

```
circuito> _
```

### Comandos básicos

| Comando | Descripción |
|---|---|
| `ayuda` | Muestra todos los comandos disponibles |
| `salir` / `exit` | Sale de la consola |
| `ver` | Muestra el estado actual del circuito |
| `limpiar` | Borra todos los datos del circuito |
| `modo mono` | Cambia al modo monofásico (1φ) |
| `modo tri` | Cambia al modo trifásico (3φ) — predeterminado |

### Comandos de circuito

| Comando | Ejemplo | Descripción |
|---|---|---|
| `fuente <V>` | `fuente 207.85` | Tensión de línea de la fuente (V_L) |
| `fuente <V> fase` | `fuente 120 fase` | Tensión de fase de la fuente (V_f) |
| `fuente <fasor>` | `fuente 120@30` | Fasor completo con ángulo |
| `linea <Z>` | `linea 2+4j` | Impedancia de línea en serie |
| `carga <Z>` | `carga 30+40j` | Agrega carga (monofásico) |
| `carga <Y\|Delta> <Z>` | `carga Y 30+40j` | Agrega carga Y o Delta (trifásico) |
| `add <Y\|Delta> <Z>` | `add Delta 60-45j` | Agrega una segunda carga en paralelo |
| `pcarga <S>` | `pcarga 1000+500j` | Carga por potencia compleja (VA) |
| `pcarga <Y\|Delta> <S> [Vnom]` | `pcarga Y 5000 120` | Carga trifásica por potencia |
| `corriente <I>` | `corriente 5@-30` | Corriente de la fuente como dato |
| `vcarga <V>` | `vcarga 200` | Tensión en la carga como dato |
| `resolver` | `resolver` | Resuelve y muestra todos los resultados |
| `resolver mono` | `resolver mono` | Fuerza modo monofásico |
| `resolver tri` | `resolver tri` | Fuerza modo trifásico |

### Comandos de consulta (post-resolver)

| Comando | Descripción |
|---|---|
| `vf` | Tensión de fase en la carga |
| `vl` | Tensión de línea en la carga |
| `if` | Corriente de fase |
| `il` | Corriente de línea |
| `s` / `potencia` | Potencia compleja total |
| `detalle <n>` | Detalle de la carga número n |
| `variables` / `todo` | Reporte completo de todas las variables |

### Comandos de exportación y gráficas

| Comando | Descripción |
|---|---|
| `exportar reporte.txt` | Exporta el reporte en TXT |
| `exportar datos.json` | Exporta en JSON |
| `exportar datos.csv` | Exporta en CSV |
| `exportar datos.xlsx` | Exporta en Excel |
| `grafica fasores` | Muestra diagrama fasorial polar (matplotlib) |
| `grafica potencia` | Muestra triángulo de potencias P-Q-S |

---

## Ejemplo Completo — Circuito Trifásico

**Problema**: Línea trifásica con Z_línea = 2+j4 Ω, conectada a dos cargas en paralelo:
- Carga 1 en Delta: Z = 60-j45 Ω (capacitiva)
- Carga 2 en Y: Z = 30+j40 Ω (inductiva)
- V_L fuente = 207.85 V

```
circuito> fuente 207.85
  ✓ Fuente: V_L = 207.85 V  |  V_f = 120.0 V

circuito> linea 2+4j
  ✓ Línea: Z = 2.00 + j4.00 Ω  |  |Z| = 4.47 Ω

circuito> carga Delta 60-45j
  ✓ Carga 1 [Delta]: Z_fase = 60.00 - j45.00 Ω

circuito> add Y 30+40j
  ✓ Carga 2 [Y]: Z_fase = 30.00 + j40.00 Ω

circuito> resolver
```

**Resultados mostrados:**
- Corriente de línea total (fuente)
- Caída de tensión en la línea
- Tensión en las cargas (V_L y V_f)
- Corriente de fase por carga
- Corriente de rama en la Delta: I_AB = V_ab / Z_Delta
- Potencia P, Q, |S| y FP en cada carga y en la línea
- Potencia total de la fuente

---

## Ejemplo Completo — Circuito Monofásico

```
circuito> modo mono
  → Modo: Monofásico (1φ)

circuito> fuente 200
  ✓ Fuente: V = 200.0 V

circuito> carga 0.8+5.6j
  ✓ Carga 1: Z = 0.80 + j5.60 Ω

circuito> add 8-16j
  ✓ Carga 2: Z = 8.00 - j16.00 Ω

circuito> resolver
```

---

## Interfaz Gráfica (GUI) — Uso Detallado

### Abrir la GUI

```bash
analizador-gui
```

o desde Python:
```python
python -m analizador.gui.app
```

### Estructura de la ventana

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR (izquierda fija)    │  ÁREA PRINCIPAL       │
│  ───────────────────────     │  ─────────────────    │
│  🔌 Potencia Compleja        │  [Tarjeta Entradas]   │
│  ⚡ Corrección FP            │  • Campo 1: ...       │
│  🔁 Circuito (mono/tri)      │  • Campo 2: ...       │
│  📐 Sistema p.u.             │  [Calcular] (botón)   │
│  ───────────────────────     │                       │
│  Tema: [Dark ▼]             │  [Tarjeta Resultados] │
│                              │  • Resultado 1: ...   │
│                              │  • Resultado 2: ...   │
│  ───────────────────────     │                       │
│  [barra de estado]           │  ✅ Cálculo exitoso   │
└─────────────────────────────────────────────────────┘
```

### Módulos disponibles en la GUI

1. **Potencia Compleja**: Calcula S, P, Q, FP dado V+I o V+Z o P+FP.
2. **Corrección de Factor de Potencia**: Determina el capacitor necesario.
3. **Circuito Monofásico/Trifásico**: Fuente + línea + múltiples cargas.
4. **Sistema por Unidad (p.u.)**: Cálculo de bases y conversión.

### Cambiar el tema visual

En el sidebar inferior, despliega el selector **"Tema"** y elige:
- `Dark` — modo oscuro (por defecto)
- `Light` — modo claro
- `System` — sigue el tema del sistema operativo

### Feedback visual

- ✅ **Verde**: cálculo exitoso, resultados mostrados.
- ❌ **Rojo**: error de entrada o cálculo, mensaje descriptivo.
- La **barra de progreso** anima brevemente durante el cálculo.

---

## Formato de Impedancias y Fasores

Todos los campos de entrada (consola y GUI) aceptan estos formatos:

### Forma rectangular
```
10+5j      →  10 + j5 Ω
2-8j       →  2 - j8 Ω
4j         →  j4 Ω
10         →  10 + j0 Ω (resistencia pura)
```

### Forma polar (ángulos en grados)
```
30∠53.13   →  30 Ω a 53.13°
30@53.13   →  igual (alternativa de teclado)
30a53.13   →  igual
50/30      →  igual
30<53.13   →  igual
50 exp(30) →  igual
```

### R y X por separado
```
linea 2 4      →  Z = 2 + j4 Ω
carga Y 30 40  →  Z_Y = 30 + j40 Ω
```

---

## Convenciones Matemáticas

| Concepto | Convención del programa |
|---|---|
| Potencia compleja | S = V · I* |
| Q > 0 | Carga **inductiva** / FP en **atraso** |
| Q < 0 | Carga **capacitiva** / FP en **adelanto** |
| Ángulos | Entrada/salida en **grados** |
| Sistema trifásico | V_f = V_L / √3 |
| Potencia trifásica | S₃φ = 3 · V_f · I_f* |
| Conversión Delta-Y | Z_Y = Z_Δ / 3 |

---

## Ejercicios del Taller 2026

Desde el menú principal, presiona **`T`** o **`13`** para acceder a 5 ejercicios verificados del curso:

1. Ejercicio 1 — Potencia compleja (P/FP dado)
2. Ejercicio 2 — Corrección de FP con capacitor
3. Ejercicio 3 — Circuito trifásico con línea y dos cargas
4. Ejercicio 4 — Flujo de carga Newton-Raphson
5. Ejercicio 5 — Cortocircuito monofásico (SLG)

Cada ejercicio muestra el enunciado, el procedimiento paso a paso y los resultados numéricos con comparación contra la solución esperada.

---

## Uso desde Python (API)

```python
from analizador.core import power_from_vi, polar_to_complex
from analizador.services import service_trifasico_carga, service_corregir_fp

# Ejemplo 1: Potencia a partir de V e I
V = polar_to_complex(120, 0)      # 120∠0° V
I = polar_to_complex(10, -30)     # 10∠-30° A
r = power_from_vi(V, I)
print(f"P={r.P:.2f} W, Q={r.Q:.2f} var, FP={r.fp:.4f} ({r.type})")

# Ejemplo 2: Carga trifásica en Y
r = service_trifasico_carga(207.85, "Y", 30+40j)
print(f"I_f = {abs(r.If):.4f} A")
print(r.meta.formulas)   # ['Vf = VL/sqrt(3)', 'If = Vf/Zfase', ...]

# Ejemplo 3: Corrección de FP
r = service_corregir_fp(P=10000, fp1=0.75, fp2=0.95, V=220, f=60)
print(f"Capacitor: {r.C_uF:.2f} µF, Xc = {r.Xc:.2f} Ω")
```

---

## Solución de Problemas

| Problema | Solución |
|---|---|
| `analizador-gui` no abre ventana | Verificar que `customtkinter` esté instalado: `pip install customtkinter` |
| Error "No module named 'analizador'" | Ejecutar `pip install -e .` desde la carpeta del proyecto |
| Resultado `Q` tiene signo incorrecto | Verificar convención: Q > 0 = inductivo, Q < 0 = capacitivo |
| Gráfica no aparece en consola | Verificar que `matplotlib` esté instalado y que haya pantalla disponible |
| Tests fallan | Ejecutar `pip install -e .[dev]` para instalar dependencias de desarrollo |

---

## Referencia Rápida de Comandos

```bash
# Instalación
pip install -e .[dev]

# Ejecutar
analizador           # CLI interactivo
analizador-gui       # GUI gráfica
python -m analizador # equivalente a analizador

# Tests
pytest                                          # todos los tests
pytest --cov=analizador --cov-report=term      # con cobertura
python -m mypy src/analizador                  # chequeo de tipos
```
