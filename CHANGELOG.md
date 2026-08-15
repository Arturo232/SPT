# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/) y
versionado [SemVer](https://semver.org/lang/es/).

## [1.7.0] - 2026-08-15

### Añadido

- **Tipado estático** (`type hints`) formal en `core.py`, `errors.py` y `config.py`: anotaciones de tipo completas con `Union`, `dict[str, str]`, `dict[str, Any]`, alias `Scalar` y `NumericLike`. Compatible con `mypy --ignore-missing-imports`.
- **Cobertura de código** (`pytest-cov>=4.0`) integrada como dependencia de desarrollo; paso de CI genera reporte `coverage.xml` y muestra líneas faltantes en terminal.
- **Chequeo de tipos** con `mypy>=1.0` como paso adicional en `.github/workflows/ci.yml` (`continue-on-error: true` para no bloquear el pipeline en módulos con tipos parciales).
- **Badges** en `README.md`: CI, Python 3.10+, Versión 1.7.0, Tests 150+, Mypy.
- **`docs/AI_CONTEXT.md`**: mapa completo del proyecto para agentes IA y copilots (arquitectura, mapa de archivos, contratos de retorno, convenciones matemáticas, reglas para agentes).
- **`docs/GUIA_USUARIO.md`**: manual completo de uso para usuarios finales (instalación, CLI, consola de comandos con ejemplos, GUI paso a paso, API Python, solución de problemas).
- Tabla de navegación completa a todos los documentos en `docs/` en el `README.md`.

### Cambiado

- `pyproject.toml`: versión actualizada a `1.7.0`; sección `[project.optional-dependencies] dev` ahora incluye `pytest-cov>=4.0` y `mypy>=1.0`; secciones `[tool.mypy]` y `[tool.coverage]` agregadas.
- `AGENTS.md`: actualizado para referenciar `docs/AI_CONTEXT.md` como fuente de verdad extendida.

## [1.6.0] - 2026-08-15

### Añadido

- Comando **`exportar`** en la consola interactiva: guarda el reporte completo del circuito en formatos TXT, JSON, CSV o XLSX.
- Comando **`grafica`** en la consola interactiva: visualiza el diagrama fasorial polar (`grafica fasores`) o el triángulo de potencias $P\text{-}Q\text{-}S$ (`grafica potencia`) usando `matplotlib`.
- Soporte para **`V_nominal` opcional** en el comando `pcarga` de la consola tanto en modo trifásico como monofásico (`pcarga <Y|Delta> <S> [Vnom]`).
- Acceso directo al menú de **Ejercicios del Taller 2026 y ejemplos** como opción `13` o atajo `T` en el menú principal CLI (`analizador.main`).
- Suite de pruebas unitarias para comandos avanzados de consola (`tests/test_consola_features.py`).

## [1.5.0] - 2026-08-15

### Añadido

- Guía de arquitectura y estándares para agentes y desarrolladores ([`AGENTS.md`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/AGENTS.md)).
- Pipeline de Integración Continua (CI) en GitHub Actions (`.github/workflows/ci.yml`) con matriz de pruebas en Python 3.10, 3.11, 3.12 y 3.13.
- Documentación técnica exhaustiva adaptada desde MATLAB:
  - [`docs/arquitectura.md`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/docs/arquitectura.md): Diseño de capas, servicios y catálogo de errores.
  - [`docs/contratos.md`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/docs/contratos.md): Especificación de contratos de retorno y bloque `.meta`.
  - [`docs/presentacion.md`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/docs/presentacion.md): Formateo fasorial, unidades SI y exportación.
  - [`docs/materiales.md`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/docs/materiales.md): Trazabilidad bibliográfica y ejercicios.

## [1.4.0] - 2026-08-15

### Añadido

- **Interfaz gráfica (GUI)** con `customtkinter` (`analizador-gui`):
  - Sidebar fijo con navegación por temas, botones con hover y selector
    de tema (Dark / Light / System).
  - Área principal dinámica con vistas en cards: Potencia compleja,
    Corrección de FP, Circuito (mono/tri con lista de cargas) y Sistema
    p.u.
  - Feedback visual inmediato: barra de estado con mensajes de
    éxito/error y barra de progreso.
  - Entradas con placeholders, unidades visibles y validación previa al
    cálculo con alertas visuales.
  - Desacoplamiento total: las vistas solo invocan al backend
    (`resolver`, `services`, `circuito`); sin lógica de negocio en la GUI.
- Componentes reutilizables (`gui/components.py`): `Card`,
  `LabeledEntry`, `StatusFeedback`, `leer_float`.
- Dependencia `customtkinter` y punto de entrada `analizador-gui`.
- Tests de la GUI (componentes, registro de vistas y smoke de ventana,
  con skip automático si no hay pantalla).

## [1.3.0] - 2026-08-15

### Añadido

- Consola de comandos como **opción `C` del menú principal** (primera
  opción recomendada); el asistente guiado queda como opción `A`.
- **Circuito monofásico (1φ)** en la consola (`CircuitoMonofasico`):
  fuente, línea y cargas en paralelo, sin conversión Y/Δ ni potencias ×3.
- **Modos de trabajo** en la consola:
  - `modo mono` / `modo tri` cambian el circuito activo.
  - `resolver mono` / `resolver tri` / `resolver` resuelven en el modo
    indicado o el actual.
  - Cada modo guarda su propio circuito (fuente, línea y cargas).
- Guía completa de la consola en `docs/consola.md`.

### Cambiado

- El comando `fuente` acepta el **fasor completo con ángulo**
  (`fuente 120@30`, `fuente 120 angulo 30`, `fuente 96.4+64.3j`), además
  del formato magnitud + ángulo por separado.
- El parser de impedancias y fasores reconoce notación **polar en todas sus
  formas**: `M angulo A`, `M/A`, `M∠A`, `M<A`, `M exp(A)`, `M e^(A)`,
  `M cis(A)` y los separadores de teclado `M@A` y `M a A` (sin símbolo de
  ángulo). Ángulos en grados, con o sin `deg`/`°`.

### Corregido

- La consola es tolerante a errores: captura comandos mal escritos o datos
  faltantes, muestra un mensaje informativo y **no se detiene**.
- Comando desconocido con typo sugiere el comando correcto.
- `resolver` y `ver` indican qué datos faltan para poder resolver.

## [1.2.0] - 2026-08-15

### Añadido

- Reporte completo con todas las variables del circuito trifásico: `Vf`/`VL`
  de la fuente, caída en la línea, y por cada carga `Vf`, `VL`, `If`, `IL`,
  `S`, `P`, `Q`, `|S|`, `FP` y `phi` según su conexión (Y o Delta).
- Comandos de consulta individual: `vl`, `vf`, `il`, `if`, `s|potencia`,
  `detalle <n>` y `variables|todo`.
- Entradas flexibles: fuente por voltaje de fase (`fuente 120 fase`),
  corriente como dato (`corriente <I>`), tensión en la carga como dato
  (`vcarga <V>`) y carga por potencia (`pcarga <S>`).
- Impedancias en forma polar (`M angulo A`, `M/A`) y por R y X separados.

## [1.1.0] - 2026-08-15

### Añadido

- Entorno de resolución de circuitos trifásicos balanceados con estado de
  red (`analizador.circuito`): fuente (VL), impedancia de línea y N cargas
  en paralelo (Y o Delta) con conversión Delta→Y automática.
- Asistente guiado (`analizador.asistente.asistente`): Fuente → Línea →
  Cargas → Resultados.
- Consola de comandos (`analizador.asistente.consola`): parser natural
  (`fuente 208`, `linea 0.1+0.05j`, `carga Delta 30+40j`, `resolver`).
- Menú principal rediseñado: agrupado por temas, opción destacada 'A' y
  sección de ayuda (convenciones de signo y unidades).
- Tests del entorno de circuito (caso del material, conversión Δ→Y,
  estado acumulativo y comandos).

## [1.0.0] - 2026-08-15

Port completo del Analizador de Sistemas de Potencia de MATLAB a Python.

### Añadido

- Núcleo matemático (`analizador/core`): V, I, Z, Y, S, FP, validaciones.
- Módulos de dominio (`analizador/modules`):
  - Circuitos monofásicos (serie/paralelo R-X y circuitos).
  - Potencia compleja (flujos VI/VZ/PF, suma de cargas, corriente de fuente).
  - Corrección de factor de potencia.
  - Flujo de potencia entre dos fuentes.
  - Sistemas trifásicos balanceados (Y/Δ).
  - Sistema por unidad (bases, conversión, cambio de base).
  - Transformadores (ideal, equivalente, regulación, eficiencia, trifásico).
  - Flujo de carga N-barras (Newton-Raphson y Gauss-Seidel).
  - Componentes simétricas (Fortescue abc↔012).
  - Cortocircuitos (3F, SLG, LL, LLG).
  - Máquinas eléctricas (generador síncrono).
  - Estabilidad (áreas iguales, tcr).
- Capa de servicios (`analizador/services`): fachadas con contratos de datos
  y bloque `.meta`.
- CLI interactivo (`analizador/main`) y menús por módulo.
- Presentación: formateo puro, salida por consola, exportación TXT/JSON/CSV
  y gráficas con matplotlib.
- Ejercicios del taller 2026 como pruebas de aceptación.
- Suites de pruebas portadas a pytest (102 tests).
