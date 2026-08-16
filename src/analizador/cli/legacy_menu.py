"""Wrapper del menú navegable clásico.

Permite invocar el menú interactivo antiguo (``gui.menus``) desde la nueva
consola REPL. Al terminar, el control regresa al bucle interactivo.
"""

from rich.console import Console


def lanzar_legacy() -> None:
    """Lanza el menú navegable clásico y espera a que el usuario salga.

    El menú clásico gestiona su propio bucle de entrada/salida. Cuando el
    usuario elige salir, esta función retorna para que la REPL continúe.
    """
    consola = Console()
    consola.print(
        "\n[bold cyan]Entrando al menu clasico.[/] "
        "[dim]Elija una opcion o '0' para volver a la consola.[/]"
    )
    try:
        from analizador.main import main as _legacy_main

        _legacy_main()
    except KeyboardInterrupt:
        consola.print("\n[dim]Menu clasico interrumpido.[/]")
    finally:
        consola.print(
            "\n[bold green]Volviendo a la consola SPT.[/] "
            "Escriba 'help' para ver los comandos."
        )
