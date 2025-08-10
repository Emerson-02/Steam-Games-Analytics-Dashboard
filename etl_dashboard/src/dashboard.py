"""
Dashboard Interativo para Análise de Dados do Steam
Usando Streamlit para criar visualizações interativas
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import sys

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent))

# Imports locais simplificados
DATABASE_FILE = Path(__file__).parent.parent / "steam.db"
DASHBOARD_TITLE = "🎮 Steam Games Analytics Dashboard"
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff6f00',
    'info': '#17a2b8'
}

# Configuração da página
st.set_page_config(
    page_title="Steam Analytics Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Carrega dados do banco SQLite com cache"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            df = pd.read_sql_query("SELECT * FROM games", conn)
        
        if df.empty:
            st.error("❌ Não foi possível carregar os dados. Execute o pipeline ETL primeiro.")
            st.stop()
            
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.stop()

@st.cache_data
def load_summary_data():
    """Carrega dados de resumo das tabelas auxiliares"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            genre_stats = pd.read_sql_query("SELECT * FROM genre_statistics", conn)
            year_stats = pd.read_sql_query("SELECT * FROM year_statistics", conn)
            top_revenue = pd.read_sql_query("SELECT * FROM top_revenue LIMIT 10", conn)
            top_quality = pd.read_sql_query("SELECT * FROM top_quality LIMIT 10", conn)
            
        return genre_stats, year_stats, top_revenue, top_quality
    except Exception as e:
        st.warning(f"⚠️ Tabelas de resumo não encontradas: {str(e)}")
        return None, None, None, None

def create_sidebar_filters(df):
    """Cria filtros na sidebar"""
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de ano
    min_year = int(df['release_year'].min())
    max_year = int(df['release_year'].max())
    
    year_range = st.sidebar.slider(
        "Ano de Lançamento",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )
    
    # Filtro de gênero
    genres = ['Todos'] + sorted(df['primary_genre'].unique().tolist())
    selected_genre = st.sidebar.selectbox("Gênero Principal", genres)
    
    # Filtro de preço
    price_categories = ['Todas'] + sorted(df['price_category'].dropna().unique().tolist())
    selected_price_category = st.sidebar.selectbox("Categoria de Preço", price_categories)
    
    # Filtro de plataforma
    platform_options = st.sidebar.multiselect(
        "Plataformas",
        options=['Windows', 'Mac', 'Linux'],
        default=['Windows', 'Mac', 'Linux']
    )
    
    # Filtro de avaliação mínima
    min_rating = st.sidebar.slider(
        "Avaliação Positiva Mínima (%)",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )
    
    return {
        'year_range': year_range,
        'genre': selected_genre,
        'price_category': selected_price_category,
        'platforms': platform_options,
        'min_rating': min_rating
    }

def apply_filters(df, filters):
    """Aplica filtros aos dados"""
    filtered_df = df.copy()
    
    # Filtro de ano
    filtered_df = filtered_df[
        (filtered_df['release_year'] >= filters['year_range'][0]) &
        (filtered_df['release_year'] <= filters['year_range'][1])
    ]
    
    # Filtro de gênero
    if filters['genre'] != 'Todos':
        filtered_df = filtered_df[filtered_df['primary_genre'] == filters['genre']]
    
    # Filtro de categoria de preço
    if filters['price_category'] != 'Todas':
        filtered_df = filtered_df[filtered_df['price_category'] == filters['price_category']]
    
    # Filtro de plataformas
    platform_filters = []
    if 'Windows' in filters['platforms']:
        platform_filters.append(filtered_df['has_windows'] == True)
    if 'Mac' in filters['platforms']:
        platform_filters.append(filtered_df['has_mac'] == True)
    if 'Linux' in filters['platforms']:
        platform_filters.append(filtered_df['has_linux'] == True)
    
    if platform_filters:
        platform_filter = platform_filters[0]
        for pf in platform_filters[1:]:
            platform_filter = platform_filter | pf
        filtered_df = filtered_df[platform_filter]
    
    # Filtro de avaliação
    filtered_df = filtered_df[filtered_df['positive_percentage'] >= filters['min_rating']]
    
    return filtered_df

def create_kpi_metrics(df):
    """Cria métricas KPI no topo do dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_games = len(df)
        st.metric(
            label="🎮 Total de Jogos",
            value=f"{total_games:,}",
            delta=None
        )
    
    with col2:
        total_revenue = df['estimated_revenue'].sum()
        st.metric(
            label="💰 Receita Estimada",
            value=f"${total_revenue/1e9:.1f}B",
            delta=None
        )
    
    with col3:
        avg_price = df['price'].mean()
        st.metric(
            label="💲 Preço Médio",
            value=f"${avg_price:.2f}",
            delta=None
        )
    
    with col4:
        avg_rating = df['positive_percentage'].mean()
        st.metric(
            label="⭐ Avaliação Média",
            value=f"{avg_rating:.1f}%",
            delta=None
        )

def create_top_games_charts(df):
    """Cria gráficos dos top jogos"""
    st.subheader("🏆 Top Jogos")
    
    tab1, tab2, tab3 = st.tabs(["💰 Mais Rentáveis", "⭐ Melhor Avaliados", "👥 Mais Populares"])
    
    with tab1:
        top_revenue = df.nlargest(10, 'estimated_revenue')
        fig = px.bar(
            top_revenue,
            x='estimated_revenue',
            y='name',
            orientation='h',
            title="Top 10 Jogos por Receita Estimada",
            labels={'estimated_revenue': 'Receita Estimada ($)', 'name': 'Jogo'},
            color='estimated_revenue',
            color_continuous_scale='viridis'
        )
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        top_quality = df.nlargest(10, 'quality_score')
        fig = px.bar(
            top_quality,
            x='quality_score',
            y='name',
            orientation='h',
            title="Top 10 Jogos por Score de Qualidade",
            labels={'quality_score': 'Score de Qualidade', 'name': 'Jogo'},
            color='quality_score',
            color_continuous_scale='plasma'
        )
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        top_popular = df.nlargest(10, 'estimated_owners')
        fig = px.bar(
            top_popular,
            x='estimated_owners',
            y='name',
            orientation='h',
            title="Top 10 Jogos por Popularidade (Owners)",
            labels={'estimated_owners': 'Número Estimado de Owners', 'name': 'Jogo'},
            color='estimated_owners',
            color_continuous_scale='cividis'
        )
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

def create_time_analysis(df):
    """Cria análises temporais"""
    st.subheader("📈 Análise Temporal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Lançamentos por ano
        yearly_releases = df.groupby('release_year').size().reset_index(name='count')
        fig = px.line(
            yearly_releases,
            x='release_year',
            y='count',
            title="Evolução de Lançamentos por Ano",
            labels={'release_year': 'Ano', 'count': 'Número de Lançamentos'},
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Receita por ano
        yearly_revenue = df.groupby('release_year')['estimated_revenue'].sum().reset_index()
        fig = px.bar(
            yearly_revenue,
            x='release_year',
            y='estimated_revenue',
            title="Receita Estimada por Ano de Lançamento",
            labels={'release_year': 'Ano', 'estimated_revenue': 'Receita Estimada ($)'},
            color='estimated_revenue',
            color_continuous_scale='blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def create_genre_analysis(df):
    """Cria análise por gêneros"""
    st.subheader("🎭 Análise por Gêneros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição de jogos por gênero
        genre_counts = df['primary_genre'].value_counts().head(10)
        fig = px.pie(
            values=genre_counts.values,
            names=genre_counts.index,
            title="Distribuição dos Top 10 Gêneros",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Receita média por gênero
        genre_revenue = df.groupby('primary_genre')['estimated_revenue'].mean().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=genre_revenue.values,
            y=genre_revenue.index,
            orientation='h',
            title="Receita Média por Gênero (Top 10)",
            labels={'x': 'Receita Média ($)', 'y': 'Gênero'},
            color=genre_revenue.values,
            color_continuous_scale='oranges'
        )
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

def create_price_analysis(df):
    """Cria análise de preços"""
    st.subheader("💰 Análise de Preços")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição por categoria de preço
        price_dist = df['price_category'].value_counts()
        fig = px.bar(
            x=price_dist.index,
            y=price_dist.values,
            title="Distribuição por Categoria de Preço",
            labels={'x': 'Categoria de Preço', 'y': 'Número de Jogos'},
            color=price_dist.values,
            color_continuous_scale='greens'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Relação preço vs avaliação
        fig = px.scatter(
            df.sample(1000) if len(df) > 1000 else df,  # Amostra para performance
            x='price',
            y='positive_percentage',
            size='estimated_owners',
            color='primary_genre',
            title="Preço vs Avaliação Positiva",
            labels={'price': 'Preço ($)', 'positive_percentage': 'Avaliação Positiva (%)'},
            hover_data=['name']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def create_detailed_stats(df):
    """Cria estatísticas detalhadas"""
    st.subheader("📊 Estatísticas Detalhadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Estatísticas Gerais**")
        stats_df = pd.DataFrame({
            'Métrica': [
                'Total de Jogos',
                'Jogos Gratuitos',
                'Jogos Multiplayer',
                'Jogos com Conquistas',
                'Jogos Multiplataforma'
            ],
            'Valor': [
                len(df),
                len(df[df['is_free'] == True]),
                len(df[df['is_multiplayer'] == True]),
                len(df[df['has_achievements'] == True]),
                len(df[df['is_multiplatform'] == True])
            ],
            'Percentual': [
                100.0,
                (len(df[df['is_free'] == True]) / len(df) * 100),
                (len(df[df['is_multiplayer'] == True]) / len(df) * 100),
                (len(df[df['has_achievements'] == True]) / len(df) * 100),
                (len(df[df['is_multiplatform'] == True]) / len(df) * 100)
            ]
        })
        stats_df['Percentual'] = stats_df['Percentual'].round(1)
        st.dataframe(stats_df, hide_index=True)
    
    with col2:
        st.write("**Top 5 Desenvolvedores por Receita**")
        dev_revenue = df.groupby('developer')['estimated_revenue'].sum().sort_values(ascending=False).head(5)
        dev_df = pd.DataFrame({
            'Desenvolvedor': dev_revenue.index,
            'Receita Total ($)': [f"${x/1e6:.1f}M" for x in dev_revenue.values],
            'Jogos': [len(df[df['developer'] == dev]) for dev in dev_revenue.index]
        })
        st.dataframe(dev_df, hide_index=True)

def main():
    """Função principal do dashboard"""
    # Título principal
    st.markdown(f'<h1 class="main-header">{DASHBOARD_TITLE}</h1>', unsafe_allow_html=True)
    
    # Carregar dados
    with st.spinner("🔄 Carregando dados..."):
        df = load_data()
    
    # Sidebar com filtros
    filters = create_sidebar_filters(df)
    
    # Aplicar filtros
    filtered_df = apply_filters(df, filters)
    
    # Mostrar informações sobre filtros aplicados
    if len(filtered_df) != len(df):
        st.info(f"📊 Mostrando {len(filtered_df):,} de {len(df):,} jogos (filtros aplicados)")
    
    # KPIs principais
    create_kpi_metrics(filtered_df)
    
    st.markdown("---")
    
    # Gráficos principais
    create_top_games_charts(filtered_df)
    
    st.markdown("---")
    
    # Análises por categoria
    col1, col2 = st.columns(2)
    
    with col1:
        create_time_analysis(filtered_df)
    
    with col2:
        create_genre_analysis(filtered_df)
    
    st.markdown("---")
    
    create_price_analysis(filtered_df)
    
    st.markdown("---")
    
    create_detailed_stats(filtered_df)
    
    # Tabela de dados brutos (opcional)
    with st.expander("🔍 Ver Dados Brutos"):
        st.dataframe(
            filtered_df[['name', 'release_year', 'primary_genre', 'price', 
                        'positive_percentage', 'estimated_revenue', 'quality_score']].head(100)
        )
    
    # Informações sobre o dataset
    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    **ℹ️ Informações do Dataset**
    
    • **Total de jogos**: {len(df):,}
    • **Período**: {int(df['release_year'].min())} - {int(df['release_year'].max())}
    • **Última atualização**: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    **🔧 Como usar:**
    1. Use os filtros à esquerda para refinar os dados
    2. Explore os diferentes gráficos e métricas
    3. Clique em "Ver Dados Brutos" para detalhes
    """)


if __name__ == "__main__":
    main()
