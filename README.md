# Analizador de Sistemas de Potencia (Python)

Port del proyecto MATLAB `SEP` a Python: analizador académico modular de
sistemas de potencia (circuitos monofásicos, potencia compleja, corrección
del factor de potencia, flujo de potencia, sistemas trifásicos, p.u.,
transformadores, flujo de carga N-barras, componentes simétricas,
cortocircuitos, máquinas eléctricas y estabilidad).

## Instalación

```bash
pip install -e .[dev]
```

## Uso rápido

```bash
analizador          # menú CLI interactivo
python -m analizador
```

Desde Python:

```python
from analizador.core import power_from_vi, polar_to_complex

v = polar_to_complex(200, 0)
i = 4 - 8j
r = power_from_vi(v, i)
print(r.P, r.Q, r.fp)
```

## Estructura

```text
analizador/
├── core.py          % Núcleo matemático (V, I, Z, Y, S, FP, validaciones)
├── errors.py        % Error analizador (analizador:<modulo>:<codigo>)
├── config.py        % Configuración por defecto + catálogo de mensajes
├── modules/         % Un tema del curso por módulo
├── services.py      % Capa de servicios (fachadas, contratos + .meta)
├── utils.py         % Entrada, formateo, presentación, exportación
├── viz.py           % Gráficas (fasores, triángulo de potencias)
├── exercises.py     % Ejercicios del taller 2026 + ejemplos
└── main.py          % Punto de entrada (menú)
```

## Pruebas

```bash
pytest
```

## Convenciones matemáticas

- Potencia compleja: `S = V * conj(I)`.
- `Q > 0` → inductiva / FP en atraso; `Q < 0` → capacitiva / adelanto.
- Capacitor: `Qc < 0` (aporta reactiva negativa).
- Flujo de potencia: ángulos en grados; funciones trigonométricas en grados.
