"""
Pipeline ETL Completo para Dados do Steam
Executa todas as etapas: Extract, Transform, Load
"""
import sys
import logging
import logging.config
from pathlib import Path
from datetime import datetime
import argparse

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from src.extract import SteamDataExtractor
from src.transform import SteamDataTransformer
from src.load import SteamDataLoader
from src.config import LOGGING_CONFIG

# Configurar logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class SteamETLPipeline:
    """Pipeline ETL completo para dados do Steam"""
    
    def __init__(self):
        self.extractor = SteamDataExtractor()
        self.transformer = SteamDataTransformer()
        self.loader = SteamDataLoader()
        self.execution_stats = {}
    
    def run_extract(self) -> tuple:
        """
        Executa a etapa de extração
        
        Returns:
            Tuple com (DataFrame, tempo_execução, estatísticas)
        """
        logger.info("🔄 Iniciando etapa de EXTRAÇÃO...")
        start_time = datetime.now()
        
        try:
            # Extrair dados do CSV
            df_raw = self.extractor.extract_csv_data()
            
            # Obter informações dos dados
            data_info = self.extractor.get_data_info(df_raw)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            stats = {
                'records_extracted': len(df_raw),
                'columns': len(df_raw.columns),
                'execution_time': execution_time,
                'memory_usage_mb': data_info['memory_usage'] / 1024 / 1024,
                'missing_values': data_info['missing_values']
            }
            
            logger.info(f"✅ Extração concluída em {execution_time:.2f}s - {len(df_raw):,} registros")
            
            return df_raw, execution_time, stats
            
        except Exception as e:
            logger.error(f"❌ Erro na extração: {str(e)}")
            raise
    
    def run_transform(self, df_raw) -> tuple:
        """
        Executa a etapa de transformação
        
        Args:
            df_raw: DataFrame com dados brutos
            
        Returns:
            Tuple com (DataFrame_transformado, tempo_execução, estatísticas)
        """
        logger.info("🔄 Iniciando etapa de TRANSFORMAÇÃO...")
        start_time = datetime.now()
        
        try:
            # Aplicar transformações sequencialmente
            logger.info("  📝 Limpeza básica dos dados...")
            df_clean = self.transformer.clean_basic_data(df_raw)
            
            logger.info("  📅 Transformação de datas...")
            df_dates = self.transformer.transform_dates(df_clean)
            
            logger.info("  📊 Criação de métricas calculadas...")
            df_metrics = self.transformer.create_calculated_metrics(df_dates)
            
            logger.info("  🏷️ Processamento de dados categóricos...")
            df_categorical = self.transformer.process_categorical_data(df_metrics)
            
            logger.info("  ⚖️ Aplicação de regras de negócio...")
            df_final = self.transformer.apply_business_rules(df_categorical)
            
            # Obter resumo das transformações
            summary = self.transformer.get_transformation_summary(df_raw, df_final)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            stats = {
                'records_input': len(df_raw),
                'records_output': len(df_final),
                'records_removed': summary['records_removed'],
                'removal_percentage': summary['removal_percentage'],
                'new_columns': summary['new_columns_added'],
                'execution_time': execution_time,
                'data_quality_score': summary['data_quality']['avg_quality_score']
            }
            
            logger.info(f"✅ Transformação concluída em {execution_time:.2f}s")
            logger.info(f"   📊 {len(df_raw):,} → {len(df_final):,} registros ({summary['removal_percentage']:.1f}% removidos)")
            logger.info(f"   📈 {summary['new_columns_added']} novas colunas criadas")
            
            return df_final, execution_time, stats
            
        except Exception as e:
            logger.error(f"❌ Erro na transformação: {str(e)}")
            raise
    
    def run_load(self, df_processed) -> tuple:
        """
        Executa a etapa de carga
        
        Args:
            df_processed: DataFrame com dados processados
            
        Returns:
            Tuple com (sucesso, tempo_execução, estatísticas)
        """
        logger.info("🔄 Iniciando etapa de CARGA...")
        start_time = datetime.now()
        
        try:
            success_count = 0
            
            # Salvar em CSV
            logger.info("  💾 Salvando em CSV...")
            if self.loader.save_to_csv(df_processed):
                success_count += 1
            
            # Salvar em Excel
            logger.info("  📊 Salvando em Excel...")
            if self.loader.save_to_excel(df_processed):
                success_count += 1
            
            # Salvar no banco SQLite
            logger.info("  🗄️ Salvando no banco SQLite...")
            if self.loader.save_to_database(df_processed):
                success_count += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Obter informações do banco
            db_info = self.loader.get_database_info()
            
            stats = {
                'formats_saved': success_count,
                'total_formats': 3,
                'execution_time': execution_time,
                'database_size_mb': db_info.get('file_size_mb', 0),
                'database_tables': len(db_info.get('tables', [])),
                'total_db_records': db_info.get('total_records', 0)
            }
            
            logger.info(f"✅ Carga concluída em {execution_time:.2f}s")
            logger.info(f"   💾 {success_count}/3 formatos salvos com sucesso")
            logger.info(f"   🗄️ Banco: {db_info.get('file_size_mb', 0):.2f} MB, {len(db_info.get('tables', []))} tabelas")
            
            return success_count == 3, execution_time, stats
            
        except Exception as e:
            logger.error(f"❌ Erro na carga: {str(e)}")
            raise
    
    def run_pipeline(self, skip_extract=False, skip_transform=False, skip_load=False):
        """
        Executa o pipeline ETL completo
        
        Args:
            skip_extract: Pular etapa de extração
            skip_transform: Pular etapa de transformação
            skip_load: Pular etapa de carga
        """
        pipeline_start = datetime.now()
        logger.info("🚀 INICIANDO PIPELINE ETL COMPLETO")
        logger.info("=" * 60)
        
        try:
            df_current = None
            
            # EXTRACT
            if not skip_extract:
                df_current, extract_time, extract_stats = self.run_extract()
                self.execution_stats['extract'] = extract_stats
            else:
                logger.info("⏭️ Etapa de extração pulada")
            
            # TRANSFORM
            if not skip_transform:
                if df_current is None:
                    logger.warning("⚠️ Sem dados para transformar. Executando extração primeiro...")
                    df_current, _, _ = self.run_extract()
                
                df_current, transform_time, transform_stats = self.run_transform(df_current)
                self.execution_stats['transform'] = transform_stats
            else:
                logger.info("⏭️ Etapa de transformação pulada")
            
            # LOAD
            if not skip_load:
                if df_current is None:
                    raise ValueError("Sem dados para carregar. Execute extração e transformação primeiro.")
                
                success, load_time, load_stats = self.run_load(df_current)
                self.execution_stats['load'] = load_stats
                
                if not success:
                    logger.warning("⚠️ Nem todos os formatos foram salvos com sucesso")
            else:
                logger.info("⏭️ Etapa de carga pulada")
            
            # Resumo final
            total_time = (datetime.now() - pipeline_start).total_seconds()
            self._print_pipeline_summary(total_time)
            
            logger.info("🎉 PIPELINE ETL CONCLUÍDO COM SUCESSO!")
            return True
            
        except Exception as e:
            logger.error(f"💥 ERRO NO PIPELINE: {str(e)}")
            return False
    
    def _print_pipeline_summary(self, total_time):
        """Imprime resumo da execução do pipeline"""
        logger.info("=" * 60)
        logger.info("📋 RESUMO DA EXECUÇÃO")
        logger.info("=" * 60)
        
        logger.info(f"⏱️ Tempo total: {total_time:.2f} segundos")
        
        if 'extract' in self.execution_stats:
            stats = self.execution_stats['extract']
            logger.info(f"📥 EXTRAÇÃO: {stats['records_extracted']:,} registros em {stats['execution_time']:.2f}s")
        
        if 'transform' in self.execution_stats:
            stats = self.execution_stats['transform']
            logger.info(f"🔧 TRANSFORMAÇÃO: {stats['records_input']:,} → {stats['records_output']:,} registros em {stats['execution_time']:.2f}s")
            logger.info(f"   • {stats['new_columns']} novas colunas criadas")
            logger.info(f"   • Score médio de qualidade: {stats['data_quality_score']:.1f}")
        
        if 'load' in self.execution_stats:
            stats = self.execution_stats['load']
            logger.info(f"💾 CARGA: {stats['formats_saved']}/{stats['total_formats']} formatos salvos em {stats['execution_time']:.2f}s")
            logger.info(f"   • Banco: {stats['database_size_mb']:.2f} MB")
            logger.info(f"   • {stats['database_tables']} tabelas criadas")
        
        logger.info("=" * 60)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Pipeline ETL para dados do Steam')
    parser.add_argument('--skip-extract', action='store_true', help='Pular etapa de extração')
    parser.add_argument('--skip-transform', action='store_true', help='Pular etapa de transformação')
    parser.add_argument('--skip-load', action='store_true', help='Pular etapa de carga')
    parser.add_argument('--verbose', '-v', action='store_true', help='Log verboso')
    
    args = parser.parse_args()
    
    # Configurar nível de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Criar e executar pipeline
    pipeline = SteamETLPipeline()
    
    try:
        success = pipeline.run_pipeline(
            skip_extract=args.skip_extract,
            skip_transform=args.skip_transform,
            skip_load=args.skip_load
        )
        
        if success:
            print("\n🎉 Pipeline executado com sucesso!")
            print("📊 Para visualizar o dashboard, execute:")
            print("   streamlit run src/dashboard.py")
        else:
            print("\n❌ Pipeline falhou. Verifique os logs acima.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execução interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n💥 Erro inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
