#!/usr/bin/env python3
"""
Script de conveniência para executar o projeto ETL Dashboard Steam
Compatível com Windows, Linux e macOS
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def get_python_executable():
    """Retorna o caminho do executável Python correto"""
    if sys.platform == "win32":
        venv_python = Path("../../.venv/Scripts/python.exe").resolve()
    else:
        venv_python = Path("../../.venv/bin/python").resolve()
    
    if venv_python.exists():
        return str(venv_python)
    
    # Fallback para python do sistema
    return sys.executable

def get_streamlit_executable():
    """Retorna o caminho do executável Streamlit correto"""
    if sys.platform == "win32":
        venv_streamlit = Path("../../.venv/Scripts/streamlit.exe").resolve()
    else:
        venv_streamlit = Path("../../.venv/bin/streamlit").resolve()
    
    if venv_streamlit.exists():
        return str(venv_streamlit)
    
    # Fallback para streamlit do sistema
    return "streamlit"

def run_command(command, description):
    """Executa um comando e retorna o resultado"""
    print(f"\n🔄 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"\n✅ {description} - Concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - Erro: {e}")
        return False

def show_menu():
    """Exibe o menu principal"""
    print("\n" + "=" * 50)
    print("    🎮 Steam ETL Dashboard")
    print("=" * 50)
    print("1. 🚀 Executar Pipeline ETL Completo")
    print("2. 📊 Abrir Dashboard")
    print("3. 🔄 Executar apenas Extração")
    print("4. 🔧 Executar apenas Transformação")
    print("5. 💾 Executar apenas Carga")
    print("6. 🧹 Limpar dados processados")
    print("7. 📋 Mostrar status do projeto")
    print("8. ❌ Sair")
    print("=" * 50)

def check_environment():
    """Verifica se o ambiente está configurado corretamente"""
    issues = []
    
    # Verificar arquivo principal
    if not Path("run_pipeline.py").exists():
        issues.append("Arquivo run_pipeline.py não encontrado")
    
    # Verificar dados brutos
    if not Path("data/raw/steam.csv").exists():
        issues.append("Arquivo de dados brutos não encontrado: data/raw/steam.csv")
    
    # Verificar Python
    python_path = get_python_executable()
    try:
        subprocess.run([python_path, "--version"], check=True, capture_output=True)
    except:
        issues.append(f"Python não encontrado em: {python_path}")
    
    return issues

def show_status():
    """Mostra o status atual do projeto"""
    print("\n📋 Status do Projeto")
    print("=" * 50)
    
    # Verificar arquivos de saída
    csv_file = Path("data/processed/steam_clean.csv")
    excel_file = Path("data/processed/steam_clean.xlsx")
    db_file = Path("steam.db")
    
    print(f"📄 CSV processado: {'✅ Existe' if csv_file.exists() else '❌ Não encontrado'}")
    print(f"📊 Excel processado: {'✅ Existe' if excel_file.exists() else '❌ Não encontrado'}")
    print(f"🗄️ Banco SQLite: {'✅ Existe' if db_file.exists() else '❌ Não encontrado'}")
    
    if db_file.exists():
        size_mb = db_file.stat().st_size / 1024 / 1024
        print(f"   Tamanho do banco: {size_mb:.2f} MB")
    
    # Verificar ambiente
    issues = check_environment()
    if issues:
        print(f"\n⚠️ Problemas encontrados:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"\n✅ Ambiente configurado corretamente")

def clean_data():
    """Remove dados processados"""
    print("\n🧹 Limpando dados processados...")
    
    files_to_remove = [
        Path("data/processed/steam_clean.csv"),
        Path("data/processed/steam_clean.xlsx"),
        Path("steam.db")
    ]
    
    removed_count = 0
    for file_path in files_to_remove:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Removido: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Erro ao remover {file_path}: {e}")
    
    if removed_count == 0:
        print("ℹ️ Nenhum arquivo processado encontrado")
    else:
        print(f"✅ {removed_count} arquivo(s) removido(s)")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Steam ETL Dashboard - Script de Conveniência')
    parser.add_argument('--run-pipeline', action='store_true', help='Executar pipeline completo')
    parser.add_argument('--dashboard', action='store_true', help='Abrir dashboard')
    parser.add_argument('--clean', action='store_true', help='Limpar dados processados')
    parser.add_argument('--status', action='store_true', help='Mostrar status')
    
    args = parser.parse_args()
    
    # Verificar se estamos no diretório correto
    if not Path("run_pipeline.py").exists():
        print("❌ Erro: Execute este script no diretório raiz do projeto")
        print("   Procurando por run_pipeline.py...")
        sys.exit(1)
    
    python_path = get_python_executable()
    streamlit_path = get_streamlit_executable()
    
    # Executar ações diretas se especificadas
    if args.run_pipeline:
        run_command(f'"{python_path}" run_pipeline.py --verbose', "Pipeline ETL Completo")
        return
    
    if args.dashboard:
        if not Path("steam.db").exists():
            print("❌ Banco de dados não encontrado! Execute o pipeline primeiro.")
            return
        print("🌐 Dashboard será aberto em: http://localhost:8501")
        print("💡 Pressione Ctrl+C para parar o servidor")
        subprocess.run([streamlit_path, "run", "src/dashboard.py"])
        return
    
    if args.clean:
        clean_data()
        return
    
    if args.status:
        show_status()
        return
    
    # Menu interativo
    while True:
        show_menu()
        
        try:
            choice = input("\nDigite sua escolha (1-8): ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Saindo...")
            break
        
        if choice == "1":
            run_command(f'"{python_path}" run_pipeline.py --verbose', "Pipeline ETL Completo")
        
        elif choice == "2":
            if not Path("steam.db").exists():
                print("❌ Banco de dados não encontrado! Execute o pipeline primeiro.")
                continue
            
            print("\n🌐 Dashboard será aberto em: http://localhost:8501")
            print("💡 Pressione Ctrl+C para parar o servidor")
            try:
                subprocess.run([streamlit_path, "run", "src/dashboard.py"])
            except KeyboardInterrupt:
                print("\n📊 Dashboard encerrado")
        
        elif choice == "3":
            run_command(f'"{python_path}" run_pipeline.py --skip-transform --skip-load --verbose', "Extração")
        
        elif choice == "4":
            run_command(f'"{python_path}" run_pipeline.py --skip-extract --skip-load --verbose', "Transformação")
        
        elif choice == "5":
            run_command(f'"{python_path}" run_pipeline.py --skip-extract --skip-transform --verbose', "Carga")
        
        elif choice == "6":
            clean_data()
        
        elif choice == "7":
            show_status()
        
        elif choice == "8":
            print("\n👋 Obrigado por usar o Steam ETL Dashboard!")
            break
        
        else:
            print("❌ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    main()
