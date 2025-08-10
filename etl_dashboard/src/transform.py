"""
Módulo de Transformação de Dados (Transform)
Responsável pela limpeza e tratamento dos dados do Steam
"""
import pandas as pd
import numpy as np
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.config import MIN_YEAR, MIN_PRICE

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SteamDataTransformer:
    """Classe responsável pela transformação dos dados do Steam"""
    
    def __init__(self, min_year: int = MIN_YEAR, min_price: float = MIN_PRICE):
        self.min_year = min_year
        self.min_price = min_price
    
    def clean_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpeza básica dos dados
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame limpo
        """
        logger.info("Iniciando limpeza básica dos dados")
        
        # Criar cópia para não modificar o original
        df_clean = df.copy()
        
        # Remover duplicatas baseadas no appid
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['appid'], keep='first')
        duplicates_removed = initial_count - len(df_clean)
        
        if duplicates_removed > 0:
            logger.info(f"Removidas {duplicates_removed} duplicatas")
        
        # Tratar valores nulos
        df_clean = self._handle_missing_values(df_clean)
        
        # Limpar strings
        string_columns = ['name', 'developer', 'publisher', 'categories', 'genres', 'steamspy_tags']
        for col in string_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                df_clean[col] = df_clean[col].replace('nan', np.nan)
        
        logger.info(f"Limpeza básica concluída. Registros: {len(df_clean)}")
        return df_clean
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trata valores faltantes"""
        
        # Preenchimento específico por coluna
        fill_values = {
            'english': 0,
            'required_age': 0,
            'achievements': 0,
            'positive_ratings': 0,
            'negative_ratings': 0,
            'average_playtime': 0,
            'median_playtime': 0,
            'price': 0.0,
            'developer': 'Unknown',
            'publisher': 'Unknown',
            'platforms': 'windows',
            'categories': 'Unknown',
            'genres': 'Unknown',
            'steamspy_tags': 'Unknown'
        }
        
        for col, value in fill_values.items():
            if col in df.columns:
                df[col] = df[col].fillna(value)
        
        return df
    
    def transform_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma e limpa as datas
        
        Args:
            df: DataFrame com dados
            
        Returns:
            DataFrame com datas transformadas
        """
        logger.info("Transformando datas")
        
        df_transformed = df.copy()
        
        # Converter release_date para datetime
        df_transformed['release_date'] = pd.to_datetime(
            df_transformed['release_date'], 
            errors='coerce'
        )
        
        # Extrair componentes da data
        df_transformed['release_year'] = df_transformed['release_date'].dt.year
        df_transformed['release_month'] = df_transformed['release_date'].dt.month
        df_transformed['release_quarter'] = df_transformed['release_date'].dt.quarter
        
        # Filtrar jogos a partir do ano mínimo
        initial_count = len(df_transformed)
        df_transformed = df_transformed[
            df_transformed['release_year'] >= self.min_year
        ]
        filtered_count = initial_count - len(df_transformed)
        
        if filtered_count > 0:
            logger.info(f"Filtrados {filtered_count} jogos anteriores a {self.min_year}")
        
        return df_transformed
    
    def create_calculated_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria métricas calculadas
        
        Args:
            df: DataFrame com dados básicos
            
        Returns:
            DataFrame com métricas adicionais
        """
        logger.info("Criando métricas calculadas")
        
        df_metrics = df.copy()
        
        # Total de avaliações
        df_metrics['total_ratings'] = (
            df_metrics['positive_ratings'] + df_metrics['negative_ratings']
        )
        
        # Porcentagem de avaliações positivas
        df_metrics['positive_percentage'] = np.where(
            df_metrics['total_ratings'] > 0,
            (df_metrics['positive_ratings'] / df_metrics['total_ratings']) * 100,
            0
        )
        
        # Receita estimada (simplificada - assumindo owners como vendas)
        df_metrics['estimated_owners'] = df_metrics['owners'].apply(self._parse_owners_range)
        df_metrics['estimated_revenue'] = df_metrics['estimated_owners'] * df_metrics['price']
        
        # Classificação de preço
        df_metrics['price_category'] = pd.cut(
            df_metrics['price'],
            bins=[0, 5, 15, 30, 60, float('inf')],
            labels=['Free/Cheap', 'Budget', 'Standard', 'Premium', 'AAA'],
            include_lowest=True
        )
        
        # Classificação de popularidade baseada em owners
        df_metrics['popularity_tier'] = pd.cut(
            df_metrics['estimated_owners'],
            bins=[0, 50000, 500000, 2000000, 10000000, float('inf')],
            labels=['Niche', 'Indie', 'Popular', 'Hit', 'Blockbuster'],
            include_lowest=True
        )
        
        # Score de qualidade (combinação de avaliações e playtime)
        df_metrics['quality_score'] = (
            (df_metrics['positive_percentage'] / 100) * 0.7 +
            (np.log1p(df_metrics['average_playtime']) / np.log1p(df_metrics['average_playtime'].max())) * 0.3
        ) * 100
        
        # Tempo desde lançamento
        current_year = datetime.now().year
        df_metrics['years_since_release'] = current_year - df_metrics['release_year']
        
        return df_metrics
    
    def _parse_owners_range(self, owners_str: str) -> int:
        """
        Converte string de range de owners para valor numérico (média do range)
        
        Args:
            owners_str: String no formato "1000000-2000000"
            
        Returns:
            Valor médio do range
        """
        if pd.isna(owners_str) or owners_str == 'Unknown':
            return 0
        
        try:
            # Remover espaços e dividir por hífen
            clean_str = str(owners_str).strip()
            
            if '-' in clean_str:
                min_val, max_val = clean_str.split('-')
                min_val = int(min_val.replace(',', ''))
                max_val = int(max_val.replace(',', ''))
                return (min_val + max_val) // 2
            else:
                return int(clean_str.replace(',', ''))
                
        except (ValueError, AttributeError):
            return 0
    
    def process_categorical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados categóricos (genres, categories, etc.)
        
        Args:
            df: DataFrame com dados
            
        Returns:
            DataFrame com categorias processadas
        """
        logger.info("Processando dados categóricos")
        
        df_processed = df.copy()
        
        # Processar gêneros (pegar o principal)
        df_processed['primary_genre'] = df_processed['genres'].apply(
            lambda x: str(x).split(';')[0] if pd.notna(x) else 'Unknown'
        )
        
        # Processar plataformas
        df_processed['platform_count'] = df_processed['platforms'].apply(
            lambda x: len(str(x).split(';')) if pd.notna(x) else 1
        )
        
        df_processed['has_windows'] = df_processed['platforms'].str.contains('windows', na=False)
        df_processed['has_mac'] = df_processed['platforms'].str.contains('mac', na=False)
        df_processed['has_linux'] = df_processed['platforms'].str.contains('linux', na=False)
        df_processed['is_multiplatform'] = df_processed['platform_count'] > 1
        
        # Processar categorias (verificar multiplayer, single-player, etc.)
        df_processed['is_multiplayer'] = df_processed['categories'].str.contains('Multi-player', na=False)
        df_processed['is_singleplayer'] = df_processed['categories'].str.contains('Single-player', na=False)
        df_processed['has_achievements'] = df_processed['achievements'] > 0
        df_processed['is_free'] = df_processed['price'] == 0
        
        return df_processed
    
    def apply_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica regras de negócio específicas
        
        Args:
            df: DataFrame com dados
            
        Returns:
            DataFrame filtrado pelas regras de negócio
        """
        logger.info("Aplicando regras de negócio")
        
        df_filtered = df.copy()
        initial_count = len(df_filtered)
        
        # Filtrar jogos com dados mínimos necessários
        df_filtered = df_filtered[
            (df_filtered['name'].notna()) &
            (df_filtered['name'] != 'Unknown') &
            (df_filtered['name'] != '') &
            (df_filtered['total_ratings'] >= 10)  # Pelo menos 10 avaliações
        ]
        
        business_filtered = initial_count - len(df_filtered)
        if business_filtered > 0:
            logger.info(f"Removidos {business_filtered} jogos pelas regras de negócio")
        
        return df_filtered
    
    def get_transformation_summary(self, df_original: pd.DataFrame, df_final: pd.DataFrame) -> Dict[str, Any]:
        """
        Gera resumo das transformações aplicadas
        
        Args:
            df_original: DataFrame original
            df_final: DataFrame final após transformações
            
        Returns:
            Dicionário com resumo das transformações
        """
        summary = {
            'original_records': len(df_original),
            'final_records': len(df_final),
            'records_removed': len(df_original) - len(df_final),
            'removal_percentage': ((len(df_original) - len(df_final)) / len(df_original)) * 100,
            'new_columns_added': len(df_final.columns) - len(df_original.columns),
            'original_columns': list(df_original.columns),
            'final_columns': list(df_final.columns),
            'data_quality': {
                'missing_values_original': df_original.isnull().sum().sum(),
                'missing_values_final': df_final.isnull().sum().sum(),
                'avg_quality_score': df_final['quality_score'].mean() if 'quality_score' in df_final.columns else 0
            }
        }
        
        return summary


def main():
    """Função principal para teste do módulo de transformação"""
    from src.extract import SteamDataExtractor
    
    # Extrair dados
    extractor = SteamDataExtractor()
    df_raw = extractor.extract_csv_data()
    
    # Transformar dados
    transformer = SteamDataTransformer()
    
    print("=== INICIANDO TRANSFORMAÇÕES ===")
    
    # Aplicar transformações passo a passo
    df_clean = transformer.clean_basic_data(df_raw)
    df_dates = transformer.transform_dates(df_clean)
    df_metrics = transformer.create_calculated_metrics(df_dates)
    df_categorical = transformer.process_categorical_data(df_metrics)
    df_final = transformer.apply_business_rules(df_categorical)
    
    # Obter resumo
    summary = transformer.get_transformation_summary(df_raw, df_final)
    
    print("=== RESUMO DAS TRANSFORMAÇÕES ===")
    print(f"Registros originais: {summary['original_records']:,}")
    print(f"Registros finais: {summary['final_records']:,}")
    print(f"Registros removidos: {summary['records_removed']:,} ({summary['removal_percentage']:.1f}%)")
    print(f"Novas colunas adicionadas: {summary['new_columns_added']}")
    print(f"Score médio de qualidade: {summary['data_quality']['avg_quality_score']:.1f}")
    
    print("\n=== NOVAS MÉTRICAS CRIADAS ===")
    new_columns = set(df_final.columns) - set(df_raw.columns)
    for col in sorted(new_columns):
        print(f"- {col}")
    
    print("\n=== TOP 10 JOGOS POR SCORE DE QUALIDADE ===")
    top_games = df_final.nlargest(10, 'quality_score')[['name', 'quality_score', 'positive_percentage', 'estimated_revenue']]
    print(top_games.to_string(index=False))
    
    return df_final


if __name__ == "__main__":
    main()
