"""Banner ASCII y presentación de bienvenida del analizador.

Renderiza el nombre del proyecto, la versión y un mensaje de bienvenida
con colores usando ``rich``. El arte ASCII es estático y está embebido.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from analizador import __version__

_BANNER = r"""
   ____  ____ _____   _____ ____    _____ ______ _   _ ______ _____ _____
  / ___||  _ \_   _| | ____|  _ \  / ____|  ____| \ | |  ____|_   _|  __ \
  \___ \| |_) || |   |  _| | |_) || (___ | |__  |  \| | |__    | | | |__) |
   ___) |  __/ | |   | |___|  _ <  \___ \|  __| | . ` |  __|   | | |  _  /
  |____/|_|    |_|   |_____|_| \_\ ____) | |____|_|\_\_|     _| |_|_| \_\
                          |_____/|______|  |_____|_____\____|_____/|_____/
"""


def _construir_banner() -> Text:
    """Construye el texto del banner con color en el nombre del proyecto."""
    titulo = Text()
    titulo.append("SPT", style="bold cyan")
    titulo.append("  |  ", style="dim")
    titulo.append("Sistemas de Potencia en Terminal", style="bold white")
    titulo.append("\n\n")
    titulo.append("Version ", style="dim")
    titulo.append(__version__, style="bold yellow")
    titulo.append("  |  Analizador academico de sistemas electricos de potencia",
                  style="dim")
    return titulo


def _construir_panel() -> Panel:
    """Construye el panel de bienvenida con el arte ASCII y la cabecera."""
    arte = Text(_BANNER, style="cyan")
    cabecera = _construir_banner()
    contenido = Text()
    contenido.append_text(arte)
    contenido.append("\n")
    contenido.append_text(cabecera)
    contenido.append("\n\n")
    contenido.append(
        "Escriba 'help' para ver los comandos disponibles o 'menu' para el "
        "menu clasico.",
        style="italic green",
    )
    return Panel(
        contenido,
        title="[bold magenta]Bienvenido[/]",
        subtitle=f"[dim]v{__version__}[/]",
        border_style="cyan",
        padding=(1, 2),
    )


def mostrar_banner(consola: Console | None = None) -> Console:
    """Renderiza el banner de bienvenida.

    Parámetros:
        consola: instancia de ``rich.console.Console`` a reutilizar. Si no se
            proporciona, se crea una nueva.

    Regresa:
        La consola ``rich`` utilizada (para encadenar otras salidas).
    """
    if consola is None:
        consola = Console()
    consola.print(_construir_panel())
    return consola
