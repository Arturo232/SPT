# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/) y
versionado [SemVer](https://semver.org/lang/es/).

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
