# Materiales y Referencias Académicas — SPT

Este documento establece la trazabilidad entre los algoritmos matemáticos implementados en SPT y la literatura clásica de referencia en Ingeniería Eléctrica y Sistemas de Potencia.

---

## 1. Bibliografía de Referencia

1. **Grainger, J. J., & Stevenson, W. D. (1994).** *Power System Analysis*. McGraw-Hill.
   - Capítulos 1 y 2: Conceptos básicos de potencia compleja, circuitos monofásicos y trifásicos.
   - Capítulo 3: Modelado de generadores síncronos y sistema por unidad ($\text{p.u.}$).
   - Capítulo 9: Flujo de potencia con matrices de admitancia ($Y_{\text{bus}}$).
   - Capítulo 11 y 12: Componentes simétricas y análisis de fallas asimétricas.
   - Capítulo 16: Estabilidad transitoria (ecuación de oscilación y áreas iguales).

2. **Saadat, H. (2010).** *Power System Analysis* (3rd ed.). PSA Publishing.
   - Algoritmos numéricos iterativos para flujo de carga: Newton-Raphson y Gauss-Seidel.
   - Trazado de diagramas fasoriales y curvas potencia-ángulo.

3. **Chapman, S. J. (2012).** *Electric Machinery Fundamentals* (5th ed.). McGraw-Hill.
   - Modelado de transformadores monofásicos y trifásicos, regulación de tensión y rendimiento.
   - Máquinas síncronas: cálculo de la fuerza electromotriz interna $E$ y reactancia síncrona $X_s$.

---

## 2. Convenciones de Cálculo y Signos

* **Potencia Compleja:**
  $$S = V \cdot I^* = P + jQ$$
* **Comportamiento Reactivo:**
  * $Q > 0 \implies$ Inductivo (corriente atrasada respecto a la tensión).
  * $Q < 0 \implies$ Capacitivo (corriente adelantada respecto a la tensión).
* **Compensación de Reactivos (Capacitores):**
  $$Q_c = P \cdot (\tan(\phi_2) - \tan(\phi_1)) < 0$$
  $$|X_c| = \frac{V^2}{|Q_c|}, \quad C = \frac{1}{2\pi f |X_c|}$$
* **Transformación de Fortescue ($abc \leftrightarrow 012$):**
  $$a = 1\angle 120^\circ = -\frac{1}{2} + j\frac{\sqrt{3}}{2}$$
  $$V_{012} = \frac{1}{3} \begin{bmatrix} 1 & 1 & 1 \\ 1 & a & a^2 \\ 1 & a^2 & a \end{bmatrix} V_{abc}$$

---

## 3. Mapeo de Ejercicios del Taller 2026

Los ejercicios del taller están implementados como casos de prueba de aceptación y funciones en [`analizador.exercises`](file:///c:/Users/ARTURO%20ANDRES/Documents/SEP-PY/src/analizador/exercises.py):
- **Ejercicio 1:** Carga serie $R\text{-}X$ ($V=480\text{ V}, P=250\text{ kW}, \text{FP}=0.9\text{ atrasado}$).
- **Ejercicio 2:** Carga paralelo $R\text{-}X$ mediante admitancias.
- **Ejercicio 3:** Combinación de dos cargas en paralelo ($35\text{ kW}$ total, carga 1 adelantada $\implies Q_1 < 0$).
- **Ejercicio 4:** Circuito con línea de transmisión serie y carga combinada $R\parallel C$.
- **Ejercicio 5:** Instalación con dos cargas, motor y corrección del factor de potencia a $\text{FP}=1.0$.
