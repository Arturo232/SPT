# SPT — Sistemas de Potencia en Terminal (Python)

Consola de comandos eléctricos: port del proyecto MATLAB `SEP` a Python.
Analizador académico modular de sistemas de potencia (circuitos
monofásicos, potencia compleja, corrección del factor de potencia, flujo de
potencia, sistemas trifásicos, p.u., transformadores, flujo de carga
N-barras, componentes simétricas, cortocircuitos, máquinas eléctricas y
estabilidad), con una **consola de comandos** para resolver circuitos
monofásicos y trifásicos balanceados de forma interactiva.

## Instalación

```bash
pip install -e .[dev]
```

## Uso rápido

```bash
analizador          # menú CLI interactivo
python -m analizador
```

En el menú principal:

```
 C. Consola de comandos (monofasico y trifasico)  <-- recomendado
 A. Asistente guiado de circuito trifasico
 1..12. Modulos tematicos
 H. Ayuda / como usar
```

Desde Python:

```python
from analizador.core import power_from_vi, polar_to_complex

v = polar_to_complex(200, 0)
i = 4 - 8j
r = power_from_vi(v, i)
print(r.P, r.Q, r.fp)
```

## Consola de comandos (opción C)

Una terminal propia para armar y resolver circuitos **monofásicos (1φ)** y
**trifásicos balanceados (3φ)**. El modo se elige con `modo` o al resolver
con `resolver mono` / `resolver tri`; cada modo guarda su propio circuito.

### Ejemplo rápido (trifásico)

```
circuito> fuente 207.846          # V_L = 207.8 V (V_f = 120 V)
circuito> linea 2+4j              # Z_línea = 2 + j4 Ω
circuito> carga Y 30+40j          # carga 1 (Y)
circuito> add Y 20-15j            # carga 2 (Y)
circuito> resolver                # reporte completo
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

## Estructura

```text
analizador/
├── main.py          % Punto de entrada (menú principal, opción C/A/1-12)
├── circuito.py      % CircuitoTrifasico y CircuitoMonofasico (estado de red)
├── asistente.py     % Consola de comandos (mono/tri) y asistente guiado
├── core.py          % Núcleo matemático (V, I, Z, Y, S, FP, validaciones)
├── errors.py        % Error analizador (analizador:<modulo>:<codigo>)
├── config.py        % Configuración por defecto + catálogo de mensajes
├── modules/         % Un tema del curso por módulo
├── services.py      % Capa de servicios (fachadas, contratos + .meta)
├── utils.py         % Entrada, formateo, presentación, exportación
├── viz.py           % Gráficas (fasores, triángulo de potencias)
├── exercises.py     % Ejercicios del taller 2026 + ejemplos
└── resolver.py      % Lógica pura de la GUI
```

## Documentación

- `docs/consola.md` — guía completa de la consola de comandos (mono/tri).
- `CHANGELOG.md` — historial de versiones.

## Pruebas

```bash
pytest
```

## Convenciones matemáticas

- Potencia compleja: `S = V * conj(I)`.
- `Q > 0` → inductiva / FP en atraso; `Q < 0` → capacitiva / adelanto.
- Capacitor: `Qc < 0` (aporta reactiva negativa).
- Trifásico balanceado: `V_f = V_L/√3`, `S3φ = 3·V_f·conj(I)`,
  `Z_Y = Z_Δ/3`.
- Flujo de potencia: ángulos en grados; funciones trigonométricas en grados.
