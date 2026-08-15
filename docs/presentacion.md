# Presentación, Formateo y Exportación — SPT

Este documento detalla las normas de formateo visual de magnitudes eléctricas, representación de números complejos/fasores y exportación de datos en el sistema.

---

## 1. Representación de Fasores y Números Complejos

Las magnitudes complejas (tensiones, corrientes, impedancias, admitancias) se representan de forma dual:

1. **Forma Rectangular:**
   $$Z = R + jX \quad (\text{ej: } 10 + j5\ \Omega,\ 4 - j8\ \text{A})$$
2. **Forma Polar (Magnitud y Ángulo en Grados):**
   $$Z = |Z|\angle \theta^\circ \quad (\text{ej: } 11.1803\angle 26.57^\circ\ \Omega)$$

El módulo [`analizador.utils`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/utils.py) ofrece la función pura `format_complex(z)` que genera ambas representaciones simultáneamente.

---

## 2. Unidades Canónicas del Sistema Internacional (SI)

| Magnitud | Símbolo | Unidad SI |
| :--- | :--- | :--- |
| Tensión eléctrica | $V, E$ | Voltio ($\text{V}$) / Kilovoltio ($\text{kV}$) |
| Corriente eléctrica | $I$ | Amperio ($\text{A}$) / Kiloamperio ($\text{kA}$) |
| Impedancia / Reactancia / Resistencia | $Z, X, R$ | Ohmio ($\Omega$) |
| Admitancia / Susceptancia / Conductancia | $Y, B, G$ | Siemens ($\text{S}$) |
| Potencia Activa | $P$ | Vatio ($\text{W}$) / Kilovatio ($\text{kW}$) / Megavatio ($\text{MW}$) |
| Potencia Reactiva | $Q$ | Voltiamperio reactivo ($\text{var}$) / $\text{kvar}$ / $\text{Mvar}$ |
| Potencia Aparente | $S, \|S\|$ | Voltiamperio ($\text{VA}$) / $\text{kVA}$ / $\text{MVA}$ |
| Capacitancia | $C$ | Faradio ($\text{F}$) / Microfaradio ($\mu\text{F}$) |
| Frecuencia | $f$ | Hercio ($\text{Hz}$) |
| Ángulos de desfase | $\phi, \delta, \theta$ | Grados sexagesimales ($^\circ$) |

---

## 3. Exportación de Resultados

La función `export_results(result, archivo, formato)` de [`analizador.utils`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/utils.py) permite persistir cualquier cálculo o reporte de circuito en los siguientes formatos:

1. **Texto Plano (`.txt`):**
   Reporte formateado idéntico a la salida de consola, con procedimiento y fórmulas.
2. **JSON Estructurado (`.json`):**
   Serialización completa con separación de partes reales e imaginarias para complejos, apta para consumo por APIs o procesamiento automatizado.
3. **Valores Separados por Comas (`.csv`) / Excel (`.xlsx`):**
   Tabla tabular de dos columnas `[campo, valor]` para análisis en hojas de cálculo.
