"""Terminal CLI tipo REPL del analizador (banner + consola interactiva).

Paquete que agrupa los componentes de la interfaz de terminal moderna:
banner ASCII, bucle REPL con autocompletado y el menú navegable legado.
"""

from .console import main

__all__ = ["main"]
