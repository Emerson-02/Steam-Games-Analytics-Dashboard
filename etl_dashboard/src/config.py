"""
Configurações globais do projeto ETL Dashboard
"""
import os
from pathlib import Path

# Caminhos dos diretórios
BASE_DIR = Path(__file__).parent.parent  # Volta para o diretório principal
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SRC_DIR = BASE_DIR / "src"

# Arquivos de entrada e saída
RAW_STEAM_FILE = RAW_DATA_DIR / "steam.csv"
PROCESSED_STEAM_CSV = PROCESSED_DATA_DIR / "steam_clean.csv"
PROCESSED_STEAM_EXCEL = PROCESSED_DATA_DIR / "steam_clean.xlsx"
DATABASE_FILE = BASE_DIR / "steam.db"

# Configurações de filtro
MIN_YEAR = 2010  # Filtrar jogos a partir de 2010
MIN_PRICE = 0.0  # Preço mínimo para considerar o jogo

# Configurações do dashboard
DASHBOARD_TITLE = "🎮 Steam Games Analytics Dashboard"
DASHBOARD_PORT = 8501

# Configurações de API (caso necessário)
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")
REQUEST_TIMEOUT = 30

# Cores para gráficos
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff6f00',
    'info': '#17a2b8'
}

# Configurações de logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
