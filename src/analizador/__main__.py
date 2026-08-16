"""Punto de entrada para ``python -m analizador``.

Lanza la consola interactiva (REPL) moderna como experiencia por defecto.
El menu clasico sigue disponible con el comando ``menu``.
"""

from .cli.console import main

if __name__ == "__main__":
    main()
