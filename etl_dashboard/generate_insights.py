"""
Demonstração de Insights dos Dados do Steam
Script para gerar relatórios e insights interessantes
"""
import sys
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuração
DATABASE_FILE = Path("steam.db")
OUTPUT_DIR = Path("insights_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_data():
    """Carrega dados do banco SQLite"""
    if not DATABASE_FILE.exists():
        print("❌ Banco de dados não encontrado! Execute o pipeline primeiro.")
        return None
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM games", conn)
    
    print(f"✅ Dados carregados: {len(df):,} jogos")
    return df

def generate_insights(df):
    """Gera insights interessantes dos dados"""
    print("\n" + "="*60)
    print("📊 INSIGHTS DOS DADOS DO STEAM")
    print("="*60)
    
    # 1. Estatísticas Gerais
    print("\n🎮 ESTATÍSTICAS GERAIS")
    print("-" * 30)
    print(f"Total de jogos: {len(df):,}")
    print(f"Período analisado: {df['release_year'].min()} - {df['release_year'].max()}")
    print(f"Receita total estimada: ${df['estimated_revenue'].sum()/1e9:.1f} bilhões")
    print(f"Preço médio: ${df['price'].mean():.2f}")
    print(f"Avaliação média: {df['positive_percentage'].mean():.1f}%")
    print(f"Jogos gratuitos: {(df['is_free'].sum()/len(df)*100):.1f}%")
    
    # 2. Top Performers
    print("\n🏆 TOP PERFORMERS")
    print("-" * 30)
    
    # Top receita
    top_revenue = df.nlargest(5, 'estimated_revenue')[['name', 'estimated_revenue', 'price']]
    print("\n💰 Top 5 Jogos por Receita:")
    for i, (_, row) in enumerate(top_revenue.iterrows(), 1):
        revenue_millions = row['estimated_revenue'] / 1e6
        print(f"{i}. {row['name'][:40]:<40} - ${revenue_millions:.1f}M")
    
    # Top qualidade
    top_quality = df.nlargest(5, 'quality_score')[['name', 'quality_score', 'positive_percentage']]
    print("\n⭐ Top 5 Jogos por Qualidade:")
    for i, (_, row) in enumerate(top_quality.iterrows(), 1):
        print(f"{i}. {row['name'][:40]:<40} - Score: {row['quality_score']:.1f}")
    
    # 3. Análise por Gênero
    print("\n🎭 ANÁLISE POR GÊNERO")
    print("-" * 30)
    
    genre_stats = df.groupby('primary_genre').agg({
        'appid': 'count',
        'estimated_revenue': 'sum',
        'positive_percentage': 'mean',
        'price': 'mean'
    }).round(2)
    
    genre_stats.columns = ['Jogos', 'Receita_Total', 'Avaliacao_Media', 'Preco_Medio']
    genre_stats['Receita_Milhoes'] = (genre_stats['Receita_Total'] / 1e6).round(1)
    genre_stats = genre_stats.sort_values('Jogos', ascending=False)
    
    print("\nTop 10 Gêneros por Quantidade:")
    for i, (genre, row) in enumerate(genre_stats.head(10).iterrows(), 1):
        print(f"{i:2}. {genre[:20]:<20} - {row['Jogos']:,} jogos, ${row['Receita_Milhoes']}M")
    
    # 4. Evolução Temporal
    print("\n📈 EVOLUÇÃO TEMPORAL")
    print("-" * 30)
    
    yearly_stats = df.groupby('release_year').agg({
        'appid': 'count',
        'estimated_revenue': 'sum',
        'price': 'mean',
        'positive_percentage': 'mean'
    }).round(2)
    
    # Anos com mais lançamentos
    peak_years = yearly_stats.nlargest(5, 'appid')
    print("\nAnos com mais lançamentos:")
    for year, row in peak_years.iterrows():
        print(f"{year}: {row['appid']:,} jogos")
    
    # Anos com maior receita
    revenue_years = yearly_stats.nlargest(5, 'estimated_revenue')
    print("\nAnos com maior receita estimada:")
    for year, row in revenue_years.iterrows():
        revenue_billions = row['estimated_revenue'] / 1e9
        print(f"{year}: ${revenue_billions:.1f}B")
    
    # 5. Análise de Preços
    print("\n💰 ANÁLISE DE PREÇOS")
    print("-" * 30)
    
    price_stats = df.groupby('price_category').size().sort_values(ascending=False)
    print("\nDistribuição por categoria de preço:")
    for category, count in price_stats.items():
        percentage = (count / len(df)) * 100
        print(f"{category:<15}: {count:,} jogos ({percentage:.1f}%)")
    
    # 6. Desenvolvedores
    print("\n👨‍💻 DESENVOLVEDORES")
    print("-" * 30)
    
    dev_stats = df.groupby('developer').agg({
        'appid': 'count',
        'estimated_revenue': 'sum'
    }).sort_values('estimated_revenue', ascending=False)
    
    print("\nTop 10 Desenvolvedores por Receita:")
    for i, (dev, row) in enumerate(dev_stats.head(10).iterrows(), 1):
        revenue_millions = row['estimated_revenue'] / 1e6
        print(f"{i:2}. {dev[:30]:<30} - {row['appid']} jogos, ${revenue_millions:.1f}M")
    
    # 7. Plataformas
    print("\n🖥️ PLATAFORMAS")
    print("-" * 30)
    
    platform_stats = {
        'Windows': df['has_windows'].sum(),
        'Mac': df['has_mac'].sum(),
        'Linux': df['has_linux'].sum(),
        'Multiplataforma': df['is_multiplatform'].sum()
    }
    
    for platform, count in platform_stats.items():
        percentage = (count / len(df)) * 100
        print(f"{platform:<15}: {count:,} jogos ({percentage:.1f}%)")
    
    # 8. Insights Curiosos
    print("\n🤔 INSIGHTS CURIOSOS")
    print("-" * 30)
    
    # Jogo mais caro
    most_expensive = df.loc[df['price'].idxmax()]
    print(f"Jogo mais caro: {most_expensive['name']} - ${most_expensive['price']:.2f}")
    
    # Jogo com mais avaliações
    most_reviewed = df.loc[df['total_ratings'].idxmax()]
    print(f"Jogo com mais avaliações: {most_reviewed['name']} - {most_reviewed['total_ratings']:,} avaliações")
    
    # Jogo mais antigo
    oldest = df.loc[df['release_year'].idxmin()]
    print(f"Jogo mais antigo: {oldest['name']} ({oldest['release_year']})")
    
    # Correlação preço vs qualidade
    price_quality_corr = df['price'].corr(df['positive_percentage'])
    print(f"Correlação Preço x Qualidade: {price_quality_corr:.3f}")
    
    # Média de conquistas por jogo
    avg_achievements = df[df['achievements'] > 0]['achievements'].mean()
    print(f"Média de conquistas por jogo: {avg_achievements:.1f}")
    
    return df

def create_visualizations(df):
    """Cria visualizações dos dados"""
    print(f"\n📊 Gerando visualizações em: {OUTPUT_DIR}/")
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # 1. Evolução de lançamentos por ano
    plt.figure(figsize=(12, 6))
    yearly_releases = df.groupby('release_year').size()
    plt.plot(yearly_releases.index, yearly_releases.values, marker='o', linewidth=2, markersize=4)
    plt.title('Evolução de Lançamentos de Jogos por Ano', fontsize=16, fontweight='bold')
    plt.xlabel('Ano de Lançamento')
    plt.ylabel('Número de Jogos')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'evolucao_lancamentos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Top 10 gêneros
    plt.figure(figsize=(12, 8))
    genre_counts = df['primary_genre'].value_counts().head(10)
    sns.barplot(x=genre_counts.values, y=genre_counts.index)
    plt.title('Top 10 Gêneros de Jogos', fontsize=16, fontweight='bold')
    plt.xlabel('Número de Jogos')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'top_generos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Distribuição de preços
    plt.figure(figsize=(12, 6))
    # Filtrar preços extremos para melhor visualização
    price_filtered = df[df['price'] <= df['price'].quantile(0.95)]['price']
    plt.hist(price_filtered, bins=50, alpha=0.7, edgecolor='black')
    plt.title('Distribuição de Preços dos Jogos', fontsize=16, fontweight='bold')
    plt.xlabel('Preço ($)')
    plt.ylabel('Número de Jogos')
    plt.axvline(price_filtered.mean(), color='red', linestyle='--', 
                label=f'Média: ${price_filtered.mean():.2f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'distribuicao_precos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Receita por categoria de preço
    plt.figure(figsize=(10, 6))
    category_revenue = df.groupby('price_category')['estimated_revenue'].sum() / 1e9
    sns.barplot(x=category_revenue.index, y=category_revenue.values)
    plt.title('Receita Total por Categoria de Preço', fontsize=16, fontweight='bold')
    plt.xlabel('Categoria de Preço')
    plt.ylabel('Receita (Bilhões $)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'receita_categoria.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Visualizações salvas com sucesso!")

def export_insights_to_file(df):
    """Exporta insights para arquivo texto"""
    output_file = OUTPUT_DIR / 'insights_relatorio.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE INSIGHTS - STEAM GAMES DATASET\n")
        f.write("=" * 60 + "\n")
        f.write(f"Gerado em: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Estatísticas básicas
        f.write("ESTATÍSTICAS GERAIS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total de jogos: {len(df):,}\n")
        f.write(f"Período: {df['release_year'].min()} - {df['release_year'].max()}\n")
        f.write(f"Receita total estimada: ${df['estimated_revenue'].sum()/1e9:.2f} bilhões\n")
        f.write(f"Preço médio: ${df['price'].mean():.2f}\n")
        f.write(f"Avaliação média: {df['positive_percentage'].mean():.1f}%\n\n")
        
        # Top jogos por receita
        f.write("TOP 10 JOGOS POR RECEITA\n")
        f.write("-" * 30 + "\n")
        top_revenue = df.nlargest(10, 'estimated_revenue')[['name', 'estimated_revenue']]
        for i, (_, row) in enumerate(top_revenue.iterrows(), 1):
            revenue_millions = row['estimated_revenue'] / 1e6
            f.write(f"{i:2}. {row['name']} - ${revenue_millions:.1f}M\n")
        
        f.write("\n")
        
        # Estatísticas por gênero
        f.write("ESTATÍSTICAS POR GÊNERO\n")
        f.write("-" * 30 + "\n")
        genre_stats = df.groupby('primary_genre').agg({
            'appid': 'count',
            'estimated_revenue': 'sum',
            'price': 'mean'
        }).sort_values('appid', ascending=False)
        
        for genre, row in genre_stats.head(15).iterrows():
            revenue_millions = row['estimated_revenue'] / 1e6
            f.write(f"{genre}: {row['appid']} jogos, ${revenue_millions:.1f}M, Preço médio: ${row['price']:.2f}\n")
    
    print(f"📄 Relatório salvo em: {output_file}")

def main():
    """Função principal"""
    print("🎮 Steam Games Dataset - Análise de Insights")
    print("=" * 60)
    
    # Carregar dados
    df = load_data()
    if df is None:
        return
    
    # Gerar insights
    generate_insights(df)
    
    # Criar visualizações
    create_visualizations(df)
    
    # Exportar relatório
    export_insights_to_file(df)
    
    print(f"\n✅ Análise completa! Confira os arquivos em: {OUTPUT_DIR}/")
    print("📊 Visualizações:")
    print("   • evolucao_lancamentos.png")
    print("   • top_generos.png") 
    print("   • distribuicao_precos.png")
    print("   • receita_categoria.png")
    print("📄 Relatório: insights_relatorio.txt")

if __name__ == "__main__":
    main()
