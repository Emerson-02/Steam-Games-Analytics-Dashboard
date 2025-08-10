"""
Pacote ETL Dashboard Steam
Pipeline completo de Extract, Transform, Load para dados do Steam
"""

__version__ = "1.0.0"
__author__ = "ETL Dashboard Team"
__description__ = "Pipeline ETL completo para análise de dados do Steam com dashboard interativo"

# Imports principais para facilitar uso do pacote
from .extract import SteamDataExtractor
from .transform import SteamDataTransformer  
from .load import SteamDataLoader
from .config import *

__all__ = [
    'SteamDataExtractor',
    'SteamDataTransformer', 
    'SteamDataLoader'
]
