# AI_CONTEXT.md — Mapa Completo del Proyecto para Agentes de IA

> **Este archivo es la fuente de verdad única para agentes de IA (LLMs, Copilot, Antigravity, etc.) que trabajen en este repositorio.**
> Leer este archivo es el primer paso obligatorio antes de cualquier modificación de código.

---

## 1. Identidad del Proyecto

| Campo | Valor |
|---|---|
| **Nombre** | SPT — Sistemas de Potencia en Terminal |
| **Paquete Python** | `analizador-sep` (importar como `analizador`) |
| **Versión actual** | `1.7.0` |
| **Python mínimo** | 3.10 |
| **Dominio** | Ingeniería Eléctrica — Sistemas Eléctricos de Potencia (SEP) |
| **Origen** | Port académico de MATLAB → Python |
| **Repositorio** | `c:\Users\ARTURO ANDRES\Documents\SEP-PY` |

---

## 2. Arquitectura en Capas (CRÍTICO)

```
┌─────────────────────────────────────────────────────┐
│  Interfaz de Usuario                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  CLI / menús │  │  Consola     │  │  GUI     │  │
│  │  main.py     │  │  asistente.py│  │  gui/    │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
├─────────────────────────────────────────────────────┤
│  Capa de Servicios (services.py)                    │
│  Fachadas que orquestan cálculos + bloque .meta     │
├─────────────────────────────────────────────────────┤
│  Módulos de Dominio (modules/*.py)                  │
│  Un archivo por tema de SEP; funciones puras        │
├─────────────────────────────────────────────────────┤
│  Núcleo Matemático (core.py)                        │
│  Álgebra fasorial, Ohm, potencia; CERO prints       │
└─────────────────────────────────────────────────────┘
```

### Regla de oro: flujo de dependencias
```
gui/* → resolver.py → services.py → modules/* → core.py
main.py / asistente.py → services.py → modules/* → core.py
```

**Nunca** importar en sentido inverso. **Nunca** añadir `print()` o `input()` en `core.py`, `modules/`, `services.py` o `circuito.py`.

---

## 3. Mapa de Archivos

### Raíz del repositorio

| Archivo | Propósito |
|---|---|
| `pyproject.toml` | Configuración del paquete, dependencias, herramientas |
| `AGENTS.md` | Guía de arquitectura para agentes IA (este archivo + reglas breves) |
| `CHANGELOG.md` | Historial de versiones (formato Keep a Changelog) |
| `README.md` | Documentación de usuario (instalación, uso, comandos) |

### `src/analizador/` — Código fuente

| Archivo | Rol en la arquitectura | Lo que hace |
|---|---|---|
| `core.py` | **Capa 1 — Núcleo** | Álgebra fasorial pura: `polar_to_complex`, `complex_to_polar`, `complex_power`, `current_from_voltage_impedance`, `power_factor`, `power_from_vi` |
| `modules/circuitos.py` | **Capa 2 — Módulo** | Circuitos monofásicos serie/paralelo R-X |
| `modules/potencia_compleja.py` | **Capa 2 — Módulo** | Análisis de potencia desde VI, VZ, PF y suma de cargas |
| `modules/correccion_fp.py` | **Capa 2 — Módulo** | Corrección de factor de potencia + cálculo de capacitor |
| `modules/sistemas_trifasicos.py` | **Capa 2 — Módulo** | Carga trifásica balanceada Y/Δ |
| `modules/per_unit.py` | **Capa 2 — Módulo** | Sistema por unidad (bases, conversión) |
| `modules/transformadores.py` | **Capa 2 — Módulo** | Transformadores ideales, equivalente, regulación |
| `modules/flujo_potencia.py` | **Capa 2 — Módulo** | Flujo entre dos fuentes, Newton-Raphson, Gauss-Seidel |
| `modules/componentes_simetricas.py` | **Capa 2 — Módulo** | Transformación Fortescue abc↔012 |
| `modules/cortocircuitos.py` | **Capa 2 — Módulo** | Fallas 3F, SLG, LL, LLG |
| `modules/maquinas.py` | **Capa 2 — Módulo** | Generador síncrono (FEM, curva P-δ) |
| `modules/estabilidad.py` | **Capa 2 — Módulo** | Criterio de áreas iguales, tiempo crítico de despeje |
| `services.py` | **Capa 3 — Servicios** | Fachadas (`service_*`): orquestan módulos, capturan excepciones, retornan `SimpleNamespace` + `.meta` |
| `circuito.py` | **Estado de red** | `CircuitoTrifasico` y `CircuitoMonofasico`: acumulan fuente, línea y cargas; resuelven con `services` |
| `asistente.py` | **UI Consola** | REPL interactivo: parser de comandos, `SesionConsola`, comandos `fuente/linea/carga/resolver/exportar/grafica` |
| `main.py` | **UI CLI** | Menú principal numérico/alfabético; despacha a `menus.py` |
| `menus.py` | **UI CLI** | Submenús por tema (12 módulos + Taller) |
| `resolver.py` | **Backend GUI** | Lógica pura que la GUI invoca para circuitos |
| `gui/app.py` | **UI GUI** | Ventana principal `customtkinter`, sidebar, área dinámica |
| `gui/components.py` | **UI GUI** | Componentes reutilizables: `Card`, `LabeledEntry`, `StatusFeedback` |
| `gui/views/` | **UI GUI** | Vistas por tema (potencia, FP, circuito, per-unit) |
| `utils.py` | **Presentación** | Formateo fasorial/potencia, exportación TXT/JSON/CSV/XLSX |
| `viz.py` | **Gráficas** | Diagramas fasores polar y triángulo P-Q-S con matplotlib |
| `config.py` | **Configuración** | `default_config()` + `mensajes()` catálogo de errores |
| `errors.py` | **Errores** | `AnalizadorError`, `error_analizador()`, `construir_error()` |
| `exercises.py` | **Ejercicios** | Ejercicios 1-5 del Taller 2026 reproducibles |

### `tests/` — Suite de pruebas

| Archivo | Qué prueba |
|---|---|
| `test_core.py` | Funciones matemáticas del núcleo |
| `test_services.py` | Cada `service_*` de la capa de servicios |
| `test_circuito.py` | `CircuitoTrifasico` y `CircuitoMonofasico` |
| `test_modules_*.py` | Módulos individuales de dominio |
| `test_consola_features.py` | Comandos avanzados de la consola (exportar, grafica, pcarga) |
| `test_exercises.py` | Ejercicios del Taller 2026 contra valores esperados |
| `test_gui_*.py` | Tests de GUI (con skip automático si no hay pantalla) |

### `docs/` — Documentación técnica

| Archivo | Contenido |
|---|---|
| `arquitectura.md` | Diseño de capas, catálogo de servicios, errores |
| `contratos.md` | Esquemas de retorno de `service_*` y bloque `.meta` |
| `presentacion.md` | Formateo fasorial, unidades SI, exportación |
| `materiales.md` | Trazabilidad: Stevenson, Saadat, Chapman, Taller 2026 |
| `consola.md` | Guía completa de la consola de comandos |
| `ROADMAP.md` | Plan de implementación por fases y versiones |
| `AI_CONTEXT.md` | **Este archivo** |
| `GUIA_USUARIO.md` | Manual de uso completo para usuarios finales |

---

## 4. Convenciones Matemáticas (OBLIGATORIO respetarlas)

| Concepto | Convención |
|---|---|
| Potencia compleja | $S = V \cdot I^*$ |
| Reactiva inductiva | $Q > 0$ → inductivo / FP en **atraso** (lagging) |
| Reactiva capacitiva | $Q < 0$ → capacitivo / FP en **adelanto** (leading) |
| Capacitor compensador | $Q_c < 0$ (aporta reactiva negativa) |
| Ángulos — entrada/salida | **Grados** |
| Ángulos — cálculo interno | **Radianes** (usar `np.deg2rad` / `np.rad2deg`) |
| Sistema trifásico | $V_f = V_L / \sqrt{3}$, $S_{3\phi} = 3 V_f I_f^*$, $Z_Y = Z_\Delta / 3$ |
| Flujo de potencia | Tensiones en pu, ángulos en grados |

---

## 5. Contratos de Retorno de `service_*`

Todos los servicios devuelven **`SimpleNamespace`** (nunca dicts normales) con:

```python
result.X      # atributo de resultado (V, I, S, P, Q, fp, etc.)
result.meta   # SimpleNamespace con: modulo, tema, formulas[], unidades, advertencias[]
```

En caso de **error capturado**, devuelven `dict` con `{"codigo": str, "mensaje": str, "causa": Exception}`.
Detectar error: `isinstance(result, dict) and "codigo" in result`.

---

## 6. Sistema de Errores

```python
# Lanzar error tipado:
error_analizador("modulo", "codigoError", "Mensaje con {0} interpolado", valor)
# → Lanza AnalizadorError("analizador:modulo:codigoError", mensaje)

# En servicios (capturar y retornar):
except Exception as err:
    result = construir_error(err)
```

Todos los códigos canónicos están en `config.py → mensajes()`.

---

## 7. Formato de Impedancias (Parser de la Consola)

El parser en `asistente.py` acepta múltiples formatos:

| Formato | Ejemplo |
|---|---|
| Rectangular `R+jX` | `10+5j`, `2-8j`, `4j`, `10` |
| Polar ángulo | `30 angulo 53.13`, `50/30`, `30∠53.13`, `30<53.13` |
| Polar teclado | `30@53.13`, `30a53.13`, `30 a 53.13` |
| Exponencial | `50 exp(30)`, `50 cis(30)` |
| R y X por separado | `linea 10 20` (R=10, X=20) |

---

## 8. Puntos de Entrada

```bash
# CLI interactivo (menú principal)
python -m analizador
analizador

# GUI (ventana customtkinter)
python -m analizador.gui.app
analizador-gui

# Desde Python
from analizador.core import power_from_vi, polar_to_complex
from analizador.services import service_trifasico_carga
```

---

## 9. Dependencias

| Paquete | Uso |
|---|---|
| `numpy>=1.24` | Álgebra lineal, números complejos, arrays |
| `scipy>=1.10` | Resolución de sistemas en flujo de carga |
| `matplotlib>=3.7` | Gráficas de fasores y triángulo de potencias |
| `customtkinter>=5.2` | GUI moderna (modo oscuro/claro) |
| `pytest>=7.0` | Suite de pruebas (dev) |
| `pytest-cov>=4.0` | Reporte de cobertura de código (dev) |
| `mypy>=1.0` | Chequeo estático de tipos (dev) |

---

## 10. Comandos de Desarrollo

```bash
# Instalar en modo editable con dependencias de desarrollo
pip install -e .[dev]

# Ejecutar todos los tests
python -m pytest

# Tests con cobertura
python -m pytest --cov=analizador --cov-report=term-missing

# Chequeo de tipos
python -m mypy src/analizador --ignore-missing-imports

# Lanzar CLI
python -m analizador

# Lanzar GUI
python -m analizador.gui.app
```

---

## 11. Reglas para Agentes IA

1. **NO agregar `print()` o `input()`** en `core.py`, `modules/`, `services.py` o `circuito.py`.
2. **Respetar la arquitectura en capas**: nunca importar desde capas superiores hacia inferiores en sentido inverso.
3. **Usar `error_analizador()`** para errores; registrar nuevos códigos en `config.py → mensajes()`.
4. **Usar `validate_input()`** en `core.py` para validar parámetros de entrada.
5. **Los servicios SIEMPRE capturan excepciones** con `try/except` y retornan `construir_error(err)`.
6. **Tests numéricos** deben usar `math.isclose` o `np.isclose` con tolerancias explícitas.
7. **Tipos de retorno**: funciones de `core.py` → escalares o `np.ndarray`; servicios → `SimpleNamespace`.
8. **Formato de fasores**: siempre mostrar en formato polar `M∠θ°` en la salida al usuario.
9. **Convención de signos**: SIEMPRE $Q > 0$ inductivo, $Q < 0$ capacitivo. Nunca invertir.
10. **Versión**: al incrementar versión, actualizar `pyproject.toml`, `CHANGELOG.md` y `docs/ROADMAP.md`.

---

## 12. Estado del Proyecto (v1.7.0)

| Fase | Contenido | Estado |
|---|---|---|
| Fase 0 | AGENTS.md + CI GitHub Actions | ✅ Completada |
| Fase 1 | Documentación técnica (4 docs) | ✅ Completada |
| Fase 2 | Exportar, gráficas, consola mejorada | ✅ Completada |
| Fase 3 | GUI con customtkinter | ✅ Completada |
| Fase 4 | Type hints + pytest-cov + badges | ✅ Completada |

**Tests**: 150+ pasando al 100%. **Cobertura**: medida con `pytest-cov`.
