# Consola de comandos de circuitos

La consola (opción `C` del menú principal) permite armar y resolver
circuitos **monofásicos (1φ)** y **trifásicos balanceados (3φ)** de forma
interactiva, sin anotar valores intermedios: el programa mantiene el estado
de la red (fuente, línea y cargas) y resuelve todo al final.

## Cómo entrar

```bash
python -m analizador.main
```

En el menú principal presione `C` (o elija el número del tema). También se
puede entrar al modo trifásico desde el asistente guiado (`A`).

## Modos de trabajo

La consola trabaja en dos modos:

| Comando | Efecto |
|---|---|
| `modo mono` | Cambia a circuito monofásico (1φ). |
| `modo tri` | Cambia a circuito trifásico balanceado (3φ). |
| `modo` | Muestra el modo actual. |
| `resolver mono` | Resuelve como monofásico (cambia de modo si hace falta). |
| `resolver tri` | Resuelve como trifásico. |
| `resolver` | Resuelve con el modo actual. |

Cada modo guarda su **propio circuito** (fuente, línea y cargas), así puedes
alternar sin perder datos. `limpiar` borra solo el modo activo.

## Diferencia de sintaxis entre modos

| Comando | Modo mono (1φ) | Modo tri (3φ) |
|---|---|---|
| `fuente` | `fuente 200` (una sola V) | `fuente 208` (V_L) o `fuente 120 fase` (V_f) |
| `carga` | `carga 10+20j` (sin conexión) | `carga Y 30+40j` / `carga Delta 45-30j` |
| `pcarga` | `pcarga 1200+1600j` | `pcarga Y 1200+1600j` |
| Potencias | `S = V·conj(I)` (sin ×3) | `S3φ = 3·V_f·conj(I)` |

## Formato de impedancias y fasores

Todos los comandos aceptan las mismas notaciones (ángulos siempre en
**grados**).

**Rectangular** (con `j` o `i`):
```
10+5j   2-8j   4j   j5   10
```

**Polar**:
```
30 angulo 53.13   50/30   30∠53.13   30<53.13   50 exp(30)   50 cis(30)
```

**Sin el símbolo de ángulo en el teclado** (use `@` o la letra `a`):
```
30@53.13   30a53.13   30 a 53.13
```

**R y X por separado**:
```
linea 10 20
carga Y 10 20
```

## Comandos de definición

### `fuente <magnitud> [linea|fase] [angulo]`  |  `fuente <fasor>`

Define la tensión de la fuente.
- En **modo tri**, por defecto es tensión de LÍNEA (`VL`); use `fase` si el
  dato es la tensión de fase (`V_f`). Si se da `V_f`, se deriva `V_L = √3·V_f`.
- En **modo mono**, es la única tensión `V`.

Ejemplos:
```
fuente 208                 # VL = 208 V (tri)
fuente 120 fase            # Vf = 120 V -> VL = 207.8 V (tri)
fuente 200                 # V = 200 V (mono)
fuente 120@30              # fasor polar completo
fuente 96.4+64.3j          # fasor rectangular
```

### `linea <Z>`

Impedancia de línea en serie:
```
linea 2+4j
linea 30 angulo 53.13
linea 1 2                  # R y X por separado
```

### `carga <Z>` (mono) / `carga <Y|Delta> <Z>` (tri)

Agrega una carga en paralelo.
- En **tri**, si es `Delta` el programa convierte solo a Y (`Z_Y = Z_Δ/3`).
- En **mono**, todas las cargas van en paralelo directo.

```
carga Y 30+40j
carga Delta 45-30j
carga 10+20j               # solo mono
```

### `pcarga <S>` (mono) / `pcarga <Y|Delta> <S>` (tri)

Agrega una carga por su **potencia compleja total** `S` (se convierte a
impedancia con la tensión nominal):
```
pcarga Y 1200+1600j
pcarga 5000@36.87          # solo mono
```

### `corriente <I>`  |  `vcarga <V>`

Datos alternativos: si solo conoces la corriente de la fuente o la tensión
en la carga, el programa deriva el resto.
```
corriente 30-40j
vcarga 110-20j
```

## Resolución y consulta

```
resolver            # calcula todo y muestra el reporte completo
variables | todo    # repite el reporte
ver                 # estado actual y qué falta para resolver
cargas              # lista las cargas del modo actual
limpiar             # borra las cargas del modo actual
```

Tras resolver, consultas rápidas:

| Comando | Qué muestra |
|---|---|
| `vf` | Tensiones de fase (fuente y carga). |
| `vl` | Tensiones de línea (solo modo tri). |
| `il` | Corriente de línea / de la fuente. |
| `if` | Corrientes de cada carga. |
| `s` | `S`, `P`, `Q`, `|S|`, `FP` y `phi` totales. |
| `detalle <n>` | Todas las variables de la carga `n`. |

## Mensajes de error

La consola es tolerante: si un comando está mal escrito o le faltan datos,
muestra un mensaje claro con una sugerencia y **no se detiene**.
- Comando con typo sugiere el correcto (ej. `liena` → `linea`).
- `resolver` indica exactamente qué datos faltan.
- `ver` muestra el estado y qué falta.

## Ejemplos resueltos

### Caso trifásico (Universidad del Sinú)

```
circuito> fuente 207.846
circuito> linea 2+4j
circuito> carga Y 30+40j
circuito> add Y 20-15j
circuito> resolver
```

Resultado: `I = 5 A`, `V_L carga = 193.65 V`, `P = 1800 W`, `Q = 0`,
`S1 = 450+j600`, `S2 = 1200-j900`.

### Caso monofásico (dos cargas en paralelo)

```
circuito> modo mono
circuito> fuente 200
circuito> carga 0.8+5.6j
circuito> add 8-16j
circuito> resolver
```

Resultado: `S = 2000+j5000 VA`, `I = 26.93 A`, `FP = 0.371`.
