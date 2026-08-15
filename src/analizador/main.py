"""Analizador de Sistemas de Potencia - punto de entrada (CLI).

Equivalente a ``main.m``: muestra un menú principal agrupado por temas y
delega en cada módulo.
"""

from .menus import (menu_circuito_trifasico, menu_circuitos,
                    menu_componentes, menu_correccion_fp, menu_cortocircuito,
                    menu_estabilidad, menu_flujo_carga, menu_flujo_potencia,
                    menu_maquinas, menu_per_unit, menu_potencia_compleja,
                    menu_transformador, menu_trifasico)
from .asistente import consola

_OPCIONES = [
    # (clave, descripcion, handler)
    ("1", "Circuitos monofasicos", menu_circuitos),
    ("2", "Potencia compleja", menu_potencia_compleja),
    ("3", "Correccion de factor de potencia", menu_correccion_fp),
    ("4", "Flujo de potencia", menu_flujo_potencia),
    ("5", "Sistemas trifasicos", menu_trifasico),
    ("6", "Sistema por unidad (p.u.)", menu_per_unit),
    ("7", "Transformadores", menu_transformador),
    ("8", "Flujo de carga N-barras", menu_flujo_carga),
    ("9", "Componentes simetricas", menu_componentes),
    ("10", "Cortocircuitos", menu_cortocircuito),
    ("11", "Maquinas electricas", menu_maquinas),
    ("12", "Estabilidad", menu_estabilidad),
]

_AYUDA = """
AYUDA DEL ANALIZADOR
--------------------------------------------
Este programa resuelve problemas de sistemas de potencia por temas.

CONVENCIONES DE SIGNO
  - Potencia compleja:  S = V * conj(I).
  - Q > 0  -> carga INDUCTIVA (FP en atraso).
  - Q < 0  -> carga CAPACITIVA (FP en adelanto).
  - Capacitor: Qc < 0 (aporta reactiva negativa).

UNIDADES
  Tension [V], corriente [A], impedancia [ohm], potencia [W/var/VA],
  frecuencia [Hz], angulos en grados.

ENTORNO DE CIRCUITOS (CONSOLA)
  Opcion 'C': consola de comandos para armar y resolver circuitos
  monofasicos (1f) y trifasicos balanceados (3f). Cambie de modo con
  'modo mono' o 'modo tri', o resuelva con 'resolver mono'/'resolver tri'.

TALLER 2026
  Los ejercicios del taller se ejecutan como pruebas (pytest) y estan
  disponibles en el paquete analizador.exercises.
"""


def _mostrar_menu():
    print("\n============================================")
    print(" ANALIZADOR DE SISTEMAS DE POTENCIA")
    print("============================================")
    print(" C. Consola de comandos (monofasico y trifasico)  <-- recomendado")
    print(" A. Asistente guiado de circuito trifasico")
    print("--------------------------------------------")
    print(" CIRCUITOS Y POTENCIA")
    for clave, desc, _ in _OPCIONES[:5]:
        print(" %s. %s" % (clave, desc))
    print("--------------------------------------------")
    print(" REDES Y MAQUINAS")
    for clave, desc, _ in _OPCIONES[5:]:
        print(" %s. %s" % (clave, desc))
    print("--------------------------------------------")
    print(" H. Ayuda / como usar")
    print(" 0. Salir")
    print("--------------------------------------------")


def _dispatch(clave):
    for c, _, handler in _OPCIONES:
        if clave == c:
            handler()
            return True
    return False


def main():
    while True:
        _mostrar_menu()
        clave = input("Seleccione una opcion: ").strip().lower()

        if clave == "0":
            print("\nFin del programa.")
            return
        if clave == "c":
            consola()
            continue
        if clave in ("a", "circuito"):
            menu_circuito_trifasico()
            continue
        if clave in ("h", "ayuda", "help", "?"):
            print(_AYUDA)
            continue
        if not _dispatch(clave):
            print("Opcion no valida. Use 'C' para la consola, 'A' para el asistente, 'H' para ayuda o '0' para salir.")


if __name__ == "__main__":
    main()
