"""
Módulo de Carga de Dados (Load)
Responsável por salvar os dados processados em diferentes formatos
"""
import pandas as pd
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import PROCESSED_STEAM_CSV, PROCESSED_STEAM_EXCEL, DATABASE_FILE

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SteamDataLoader:
    """Classe responsável pela carga dos dados processados"""
    
    def __init__(self):
        self.database_file = DATABASE_FILE
        self.csv_file = PROCESSED_STEAM_CSV
        self.excel_file = PROCESSED_STEAM_EXCEL
    
    def save_to_csv(self, df: pd.DataFrame, file_path: Optional[Path] = None) -> bool:
        """
        Salva DataFrame em arquivo CSV
        
        Args:
            df: DataFrame para salvar
            file_path: Caminho do arquivo (opcional)
            
        Returns:
            True se salvou com sucesso
        """
        try:
            output_path = file_path or self.csv_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Salvando dados em CSV: {output_path}")
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            file_size = output_path.stat().st_size / 1024 / 1024  # MB
            logger.info(f"CSV salvo com sucesso! Tamanho: {file_size:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {str(e)}")
            return False
    
    def save_to_excel(self, df: pd.DataFrame, file_path: Optional[Path] = None) -> bool:
        """
        Salva DataFrame em arquivo Excel com múltiplas abas
        
        Args:
            df: DataFrame para salvar
            file_path: Caminho do arquivo (opcional)
            
        Returns:
            True se salvou com sucesso
        """
        try:
            output_path = file_path or self.excel_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Salvando dados em Excel: {output_path}")
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Aba principal com todos os dados
                df.to_excel(writer, sheet_name='All_Games', index=False)
                
                # Aba com top jogos por receita
                top_revenue = df.nlargest(100, 'estimated_revenue')
                top_revenue.to_excel(writer, sheet_name='Top_Revenue', index=False)
                
                # Aba com top jogos por qualidade
                top_quality = df.nlargest(100, 'quality_score')
                top_quality.to_excel(writer, sheet_name='Top_Quality', index=False)
                
                # Aba com estatísticas por gênero
                genre_stats = self._create_genre_statistics(df)
                genre_stats.to_excel(writer, sheet_name='Genre_Stats', index=True)
                
                # Aba com estatísticas por ano
                year_stats = self._create_year_statistics(df)
                year_stats.to_excel(writer, sheet_name='Year_Stats', index=True)
            
            file_size = output_path.stat().st_size / 1024 / 1024  # MB
            logger.info(f"Excel salvo com sucesso! Tamanho: {file_size:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar Excel: {str(e)}")
            return False
    
    def save_to_database(self, df: pd.DataFrame, table_name: str = 'games') -> bool:
        """
        Salva DataFrame no banco SQLite
        
        Args:
            df: DataFrame para salvar
            table_name: Nome da tabela
            
        Returns:
            True se salvou com sucesso
        """
        try:
            logger.info(f"Salvando dados no banco SQLite: {self.database_file}")
            
            # Criar diretório se não existir
            self.database_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Conectar ao banco
            with sqlite3.connect(self.database_file) as conn:
                # Salvar dados na tabela principal
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                
                # Criar tabelas auxiliares para análise
                self._create_summary_tables(df, conn)
                
                # Criar índices para melhor performance
                self._create_indexes(conn, table_name)
                
                # Obter estatísticas do banco
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
            
            logger.info(f"Banco SQLite salvo com sucesso! Registros: {record_count:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {str(e)}")
            return False
    
    def _create_summary_tables(self, df: pd.DataFrame, conn: sqlite3.Connection):
        """Cria tabelas de resumo para análise rápida"""
        
        # Estatísticas por gênero
        genre_stats = self._create_genre_statistics(df)
        genre_stats.to_sql('genre_statistics', conn, if_exists='replace', index=True)
        
        # Estatísticas por ano
        year_stats = self._create_year_statistics(df)
        year_stats.to_sql('year_statistics', conn, if_exists='replace', index=True)
        
        # Top jogos por diferentes métricas
        top_games = {
            'top_revenue': df.nlargest(50, 'estimated_revenue')[
                ['appid', 'name', 'estimated_revenue', 'price', 'estimated_owners']
            ],
            'top_quality': df.nlargest(50, 'quality_score')[
                ['appid', 'name', 'quality_score', 'positive_percentage', 'total_ratings']
            ],
            'top_popular': df.nlargest(50, 'estimated_owners')[
                ['appid', 'name', 'estimated_owners', 'total_ratings', 'average_playtime']
            ]
        }
        
        for table_name, data in top_games.items():
            data.to_sql(table_name, conn, if_exists='replace', index=False)
    
    def _create_indexes(self, conn: sqlite3.Connection, table_name: str):
        """Cria índices para melhor performance"""
        
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_appid ON {table_name}(appid)",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_release_year ON {table_name}(release_year)",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_primary_genre ON {table_name}(primary_genre)",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_price_category ON {table_name}(price_category)",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_estimated_revenue ON {table_name}(estimated_revenue)",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_quality_score ON {table_name}(quality_score)"
        ]
        
        cursor = conn.cursor()
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Erro ao criar índice: {str(e)}")
    
    def _create_genre_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria estatísticas agregadas por gênero"""
        
        stats = df.groupby('primary_genre').agg({
            'appid': 'count',
            'price': ['mean', 'median'],
            'estimated_revenue': ['sum', 'mean'],
            'positive_percentage': 'mean',
            'quality_score': 'mean',
            'estimated_owners': ['sum', 'mean'],
            'average_playtime': 'mean'
        }).round(2)
        
        # Achatar nomes das colunas
        stats.columns = [f'{col[0]}_{col[1]}' if col[1] else col[0] for col in stats.columns]
        stats = stats.rename(columns={'appid_count': 'total_games'})
        
        # Adicionar percentual do total
        stats['percentage_of_total'] = (stats['total_games'] / len(df) * 100).round(1)
        
        return stats.sort_values('total_games', ascending=False)
    
    def _create_year_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria estatísticas agregadas por ano"""
        
        stats = df.groupby('release_year').agg({
            'appid': 'count',
            'price': ['mean', 'median'],
            'estimated_revenue': ['sum', 'mean'],
            'positive_percentage': 'mean',
            'quality_score': 'mean',
            'estimated_owners': ['sum', 'mean'],
            'is_free': lambda x: (x == True).sum(),
            'has_achievements': lambda x: (x == True).sum()
        }).round(2)
        
        # Achatar nomes das colunas
        stats.columns = [f'{col[0]}_{col[1]}' if col[1] else col[0] for col in stats.columns]
        stats = stats.rename(columns={
            'appid_count': 'total_games',
            'is_free_<lambda>': 'free_games',
            'has_achievements_<lambda>': 'games_with_achievements'
        })
        
        # Calcular percentuais
        stats['free_games_percentage'] = (stats['free_games'] / stats['total_games'] * 100).round(1)
        stats['achievements_percentage'] = (stats['games_with_achievements'] / stats['total_games'] * 100).round(1)
        
        return stats.sort_values('release_year', ascending=True)
    
    def load_from_database(self, query: str = "SELECT * FROM games LIMIT 1000") -> pd.DataFrame:
        """
        Carrega dados do banco SQLite
        
        Args:
            query: Consulta SQL
            
        Returns:
            DataFrame com os dados consultados
        """
        try:
            logger.info(f"Carregando dados do banco: {self.database_file}")
            
            with sqlite3.connect(self.database_file) as conn:
                df = pd.read_sql_query(query, conn)
            
            logger.info(f"Dados carregados com sucesso! Shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do banco: {str(e)}")
            return pd.DataFrame()
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o banco de dados
        
        Returns:
            Dicionário com informações do banco
        """
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                
                # Listar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Obter contagem de registros por tabela
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                
                # Tamanho do arquivo
                file_size = self.database_file.stat().st_size / 1024 / 1024  # MB
                
                return {
                    'database_file': str(self.database_file),
                    'file_size_mb': round(file_size, 2),
                    'tables': tables,
                    'table_counts': table_counts,
                    'total_records': sum(table_counts.values())
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do banco: {str(e)}")
            return {}


def main():
    """Função principal para teste do módulo de carga"""
    from src.extract import SteamDataExtractor
    from src.transform import SteamDataTransformer
    
    # Pipeline completo para teste
    print("=== EXECUTANDO PIPELINE ETL COMPLETO ===")
    
    # Extract
    extractor = SteamDataExtractor()
    df_raw = extractor.extract_csv_data()
    print(f"✓ Extração concluída: {len(df_raw):,} registros")
    
    # Transform
    transformer = SteamDataTransformer()
    df_clean = transformer.clean_basic_data(df_raw)
    df_dates = transformer.transform_dates(df_clean)
    df_metrics = transformer.create_calculated_metrics(df_dates)
    df_categorical = transformer.process_categorical_data(df_metrics)
    df_final = transformer.apply_business_rules(df_categorical)
    print(f"✓ Transformação concluída: {len(df_final):,} registros")
    
    # Load
    loader = SteamDataLoader()
    
    print("\n=== SALVANDO DADOS ===")
    
    # Salvar em CSV
    if loader.save_to_csv(df_final):
        print("✓ CSV salvo com sucesso")
    
    # Salvar em Excel
    if loader.save_to_excel(df_final):
        print("✓ Excel salvo com sucesso")
    
    # Salvar em banco SQLite
    if loader.save_to_database(df_final):
        print("✓ Banco SQLite salvo com sucesso")
    
    # Informações do banco
    db_info = loader.get_database_info()
    print(f"\n=== INFORMAÇÕES DO BANCO ===")
    print(f"Arquivo: {db_info.get('database_file')}")
    print(f"Tamanho: {db_info.get('file_size_mb')} MB")
    print(f"Tabelas: {', '.join(db_info.get('tables', []))}")
    print(f"Total de registros: {db_info.get('total_records'):,}")
    
    return df_final


if __name__ == "__main__":
    main()
