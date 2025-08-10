"""
Módulo de Extração de Dados (Extract)
Responsável por coletar os dados brutos do Steam
"""
import pandas as pd
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from src.config import RAW_STEAM_FILE, REQUEST_TIMEOUT, STEAM_API_KEY

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SteamDataExtractor:
    """Classe responsável pela extração de dados do Steam"""
    
    def __init__(self):
        self.steam_api_key = STEAM_API_KEY
        self.timeout = REQUEST_TIMEOUT
    
    def extract_csv_data(self, file_path: Path = RAW_STEAM_FILE) -> pd.DataFrame:
        """
        Extrai dados do arquivo CSV do Steam
        
        Args:
            file_path: Caminho para o arquivo CSV
            
        Returns:
            DataFrame com os dados extraídos
        """
        try:
            logger.info(f"Extraindo dados do arquivo: {file_path}")
            
            # Verificar se o arquivo existe
            if not file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Ler o CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            
            logger.info(f"Dados extraídos com sucesso! Shape: {df.shape}")
            logger.info(f"Colunas: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do CSV: {str(e)}")
            raise
    
    def extract_steam_api_data(self, app_ids: list) -> Dict[str, Any]:
        """
        Extrai dados adicionais da API do Steam (opcional)
        
        Args:
            app_ids: Lista de IDs dos jogos
            
        Returns:
            Dicionário com dados da API
        """
        if not self.steam_api_key:
            logger.warning("API Key do Steam não configurada. Pulando extração da API.")
            return {}
        
        api_data = {}
        
        try:
            logger.info(f"Extraindo dados da API para {len(app_ids)} jogos")
            
            # Exemplo de chamada para API do Steam
            for app_id in app_ids[:10]:  # Limitando para 10 jogos como exemplo
                try:
                    url = f"https://store.steampowered.com/api/appdetails"
                    params = {'appids': app_id, 'filters': 'price_overview,categories'}
                    
                    response = requests.get(url, params=params, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json()
                        api_data[app_id] = data
                    
                except Exception as e:
                    logger.warning(f"Erro ao extrair dados da API para app_id {app_id}: {str(e)}")
                    continue
            
            logger.info(f"Dados da API extraídos para {len(api_data)} jogos")
            
        except Exception as e:
            logger.error(f"Erro geral na extração da API: {str(e)}")
        
        return api_data
    
    def get_data_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Retorna informações básicas sobre os dados extraídos
        
        Args:
            df: DataFrame com os dados
            
        Returns:
            Dicionário com informações dos dados
        """
        info = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'date_range': {
                'min_date': df['release_date'].min() if 'release_date' in df.columns else None,
                'max_date': df['release_date'].max() if 'release_date' in df.columns else None
            }
        }
        
        return info


def main():
    """Função principal para teste do módulo de extração"""
    extractor = SteamDataExtractor()
    
    # Extrair dados do CSV
    df = extractor.extract_csv_data()
    
    # Obter informações dos dados
    info = extractor.get_data_info(df)
    
    print("=== INFORMAÇÕES DOS DADOS EXTRAÍDOS ===")
    print(f"Total de registros: {info['total_records']:,}")
    print(f"Total de colunas: {info['total_columns']}")
    print(f"Período: {info['date_range']['min_date']} até {info['date_range']['max_date']}")
    print(f"Uso de memória: {info['memory_usage'] / 1024 / 1024:.2f} MB")
    
    print("\n=== VALORES FALTANTES ===")
    for col, missing in info['missing_values'].items():
        if missing > 0:
            print(f"{col}: {missing:,} ({missing/info['total_records']*100:.1f}%)")
    
    print("\n=== PRIMEIRAS 5 LINHAS ===")
    print(df.head())
    
    return df


if __name__ == "__main__":
    main()
