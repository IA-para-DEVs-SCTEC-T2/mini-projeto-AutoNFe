"""
Ponto de entrada principal da aplicação AutoNFe
Execute: python main.py
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para permitir imports absolutos
sys.path.insert(0, str(Path(__file__).parent))

from src.web.main import app

if __name__ == "__main__":
    app.run()
