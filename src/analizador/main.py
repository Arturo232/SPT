"""Analizador de Sistemas de Potencia - punto de entrada (CLI).

Equivalente a ``main.m``: muestra un menú principal y delega en cada módulo.
"""

from .menus import (menu_circuitos, menu_componentes, menu_correccion_fp,
                    menu_cortocircuito, menu_estabilidad, menu_flujo_carga,
                    menu_flujo_potencia, menu_maquinas, menu_per_unit,
                    menu_potencia_compleja, menu_transformador, menu_trifasico)
from .utils import input_helpers


def main():
    while True:
        print("\n============================================")
        print(" ANALIZADOR DE SISTEMAS DE POTENCIA")
        print("============================================")
        print(" 1. Circuitos monofasicos")
        print(" 2. Potencia compleja")
        print(" 3. Correccion de factor de potencia")
        print(" 4. Flujo de potencia")
        print(" 5. Sistemas trifasicos")
        print(" 6. Sistema por unidad (p.u.)")
        print(" 7. Transformadores")
        print(" 8. Flujo de carga N-barras")
        print(" 9. Componentes simetricas")
        print("10. Cortocircuitos")
        print("11. Maquinas electricas")
        print("12. Estabilidad")
        print(" 0. Salir")
        print("--------------------------------------------")

        opcion = input_helpers("choice", "Seleccione una opcion:", [
            "Circuitos monofasicos",
            "Potencia compleja",
            "Correccion de factor de potencia",
            "Flujo de potencia",
            "Sistemas trifasicos",
            "Sistema por unidad (p.u.)",
            "Transformadores",
            "Flujo de carga N-barras",
            "Componentes simetricas",
            "Cortocircuitos",
            "Maquinas electricas",
            "Estabilidad",
            "Salir",
        ])

        if opcion == 1:
            menu_circuitos()
        elif opcion == 2:
            menu_potencia_compleja()
        elif opcion == 3:
            menu_correccion_fp()
        elif opcion == 4:
            menu_flujo_potencia()
        elif opcion == 5:
            menu_trifasico()
        elif opcion == 6:
            menu_per_unit()
        elif opcion == 7:
            menu_transformador()
        elif opcion == 8:
            menu_flujo_carga()
        elif opcion == 9:
            menu_componentes()
        elif opcion == 10:
            menu_cortocircuito()
        elif opcion == 11:
            menu_maquinas()
        elif opcion == 12:
            menu_estabilidad()
        elif opcion == 13:
            print("\nFin del programa.")
            return


if __name__ == "__main__":
    main()
