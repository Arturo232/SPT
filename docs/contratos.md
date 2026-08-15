# Contratos de Datos y Esquemas — SPT

Este documento define la estructura y contratos formales de datos devueltos por las funciones de cálculo y servicios del analizador.

---

## 1. Estructura del Bloque de Metadatos (`.meta`)

Todos los resultados devueltos por la capa de servicios ([`services.py`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/services.py)) incluyen un atributo `meta` (`SimpleNamespace`) con fines pedagógicos y de trazabilidad:

```python
result.meta = SimpleNamespace(
    modulo="potenciaCompleja",
    tema="Potencia compleja desde V e I",
    formulas=[
        "S = V * conj(I)",
        "P = real(S)",
        "Q = imag(S)",
        "FP = cos(phi)"
    ],
    unidades=SimpleNamespace(V="V", I="A", S="VA", P="W", Q="var"),
    advertencias=[]
)
```

---

## 2. Esquemas de Retorno por Módulo

### A. Potencia Compleja (`power_from_vi`, `solve_carga`, `load_power_from_z`)
Retorna una estructura con los siguientes campos obligatorios:

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `S` | `complex` | Potencia compleja total en $\text{VA}$ ($P + jQ$). |
| `P` | `float` | Potencia activa en $\text{W}$. |
| `Q` | `float` | Potencia reactiva en $\text{var}$. |
| `Sabs` | `float` | Magnitud de la potencia aparente ($|S| = \sqrt{P^2 + Q^2}$) en $\text{VA}$. |
| `fp` | `float` | Factor de potencia ($0 \le \text{FP} \le 1$). |
| `phi_deg` | `float` | Ángulo de desfase tensión-corriente en grados sexagesimales. |
| `type` | `str` | Tipo de carga: `'inductiva'`, `'capacitiva'` o `'resistiva'`. |
| `V` *(opcional)* | `complex` | Tensión aplicada en $\text{V}$. |
| `I` *(opcional)* | `complex` | Corriente en $\text{A}$. |

---

### B. Corrección de Factor de Potencia (`service_corregir_fp`)
Retorna los parámetros de dimensionamiento del capacitor de compensación:

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `P` | `float` | Potencia activa constante en $\text{W}$. |
| `Q1` | `float` | Potencia reactiva inicial en $\text{var}$. |
| `Q2` | `float` | Potencia reactiva deseada tras la corrección en $\text{var}$. |
| `Qc` | `float` | Potencia reactiva capacitiva requerida en $\text{var}$ ($Q_c < 0$). |
| `Xc` | `float` | Reactancia capacitiva necesaria en $\Omega$ ($|X_c| = V^2 / |Q_c|$). |
| `C_F` | `float` | Capacitancia necesaria en Faradios ($\text{F}$). |
| `C_uF` | `float` | Capacitancia en microfaradios ($\mu\text{F}$). |
| `fp_corregido` | `float` | Factor de potencia final alcanzado. |
| `type` | `str` | Régimen final: `'inductivo'`, `'capacitivo'` o `'resistivo'`. |

---

### C. Flujo de Potencia entre Dos Fuentes (`service_flujo_dos_fuentes`)

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `V1` | `complex` | Tensión fasorial de la barra 1. |
| `V2` | `complex` | Tensión fasorial de la barra 2. |
| `Zline` | `complex` | Impedancia de la línea de enlace en $\Omega$. |
| `I12` | `complex` | Corriente circulante de la barra 1 a la 2 en $\text{A}$. |
| `S12` | `complex` | Potencia compleja enviada desde la barra 1 en $\text{VA}$. |
| `P12` | `float` | Potencia activa transmitida en $\text{W}$. |
| `Q12` | `float` | Potencia reactiva transmitida en $\text{var}$. |

---

### D. Sistemas Trifásicos Balanceados (`solve_three_phase_load`)

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `VL` | `float` | Tensión de línea en $\text{V}$. |
| `Vf` | `float` | Tensión de fase en $\text{V}$ ($V_f = V_L / \sqrt{3}$ en Y, $V_f = V_L$ en $\Delta$). |
| `If` | `float` | Magnitud de corriente de fase en $\text{A}$. |
| `IL` | `float` | Magnitud de corriente de línea en $\text{A}$. |
| `S` | `complex` | Potencia compleja trifásica total en $\text{VA}$. |
| `P` | `float` | Potencia activa trifásica en $\text{W}$. |
| `Q` | `float` | Potencia reactiva trifásica en $\text{var}$. |
| `fp` | `float` | Factor de potencia trifásico. |
| `type` | `str` | Régimen de la carga. |
