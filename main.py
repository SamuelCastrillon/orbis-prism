#!/usr/bin/env python3
# Punto de entrada CLI: delega a src.prism.cli

import sys
from pathlib import Path

# Permitir ejecutar desde raíz sin instalar el paquete (prism está en src/prism)
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root / "src"))

from src.prism.entrypoints import main

if __name__ == "__main__":
    sys.exit(main())
