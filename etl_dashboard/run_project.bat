@echo off
REM Script para executar o projeto ETL Dashboard Steam
REM Autor: ETL Dashboard Team

echo ================================
echo    🎮 Steam ETL Dashboard    
echo ================================
echo.

REM Verificar se estamos no diretório correto
if not exist "run_pipeline.py" (
    echo ❌ Erro: Execute este script no diretório raiz do projeto
    echo    Procurando por run_pipeline.py...
    pause
    exit /b 1
)

REM Definir caminho do Python
set PYTHON_PATH=G:\Users\Windows\Downloads\codes\ETL-Projects\.venv\Scripts\python.exe
set STREAMLIT_PATH=G:\Users\Windows\Downloads\codes\ETL-Projects\.venv\Scripts\streamlit.exe

echo 🔧 Verificando ambiente Python...
if not exist "%PYTHON_PATH%" (
    echo ❌ Ambiente virtual não encontrado!
    echo    Execute primeiro: python -m venv .venv
    echo    E instale as dependências: pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Ambiente Python encontrado
echo.

:MENU
echo ================================
echo    Escolha uma opção:
echo ================================
echo 1. 🚀 Executar Pipeline ETL Completo
echo 2. 📊 Abrir Dashboard (requer dados processados)
echo 3. 🔄 Executar apenas Extração
echo 4. 🔧 Executar apenas Transformação  
echo 5. 💾 Executar apenas Carga
echo 6. 🧹 Limpar dados processados
echo 7. ❌ Sair
echo ================================
set /p choice="Digite sua escolha (1-7): "

if "%choice%"=="1" goto RUN_FULL_PIPELINE
if "%choice%"=="2" goto OPEN_DASHBOARD
if "%choice%"=="3" goto RUN_EXTRACT
if "%choice%"=="4" goto RUN_TRANSFORM
if "%choice%"=="5" goto RUN_LOAD
if "%choice%"=="6" goto CLEAN_DATA
if "%choice%"=="7" goto EXIT

echo ❌ Opção inválida! Tente novamente.
echo.
goto MENU

:RUN_FULL_PIPELINE
echo.
echo 🚀 Executando Pipeline ETL Completo...
echo ================================
"%PYTHON_PATH%" run_pipeline.py --verbose
if %ERRORLEVEL%==0 (
    echo.
    echo ✅ Pipeline executado com sucesso!
    echo 📊 Para ver o dashboard, escolha a opção 2 no menu
) else (
    echo.
    echo ❌ Erro na execução do pipeline!
)
echo.
pause
goto MENU

:OPEN_DASHBOARD
echo.
echo 📊 Verificando se existem dados processados...
if not exist "steam.db" (
    echo ❌ Banco de dados não encontrado!
    echo    Execute primeiro o Pipeline ETL (opção 1)
    echo.
    pause
    goto MENU
)

echo ✅ Dados encontrados. Abrindo dashboard...
echo.
echo 🌐 Dashboard será aberto em: http://localhost:8501
echo 💡 Pressione Ctrl+C para parar o servidor
echo ================================
"%STREAMLIT_PATH%" run src\dashboard.py
goto MENU

:RUN_EXTRACT
echo.
echo 📥 Executando apenas Extração...
echo ================================
"%PYTHON_PATH%" run_pipeline.py --skip-transform --skip-load --verbose
echo.
pause
goto MENU

:RUN_TRANSFORM
echo.
echo 🔧 Executando apenas Transformação...
echo ================================
"%PYTHON_PATH%" run_pipeline.py --skip-extract --skip-load --verbose
echo.
pause
goto MENU

:RUN_LOAD
echo.
echo 💾 Executando apenas Carga...
echo ================================
"%PYTHON_PATH%" run_pipeline.py --skip-extract --skip-transform --verbose
echo.
pause
goto MENU

:CLEAN_DATA
echo.
echo 🧹 Limpando dados processados...
echo ================================
echo ⚠️  Esta ação irá remover:
echo    - Arquivos CSV e Excel processados
echo    - Banco de dados SQLite
echo    - Logs de execução
echo.
set /p confirm="Tem certeza? (S/N): "
if /i "%confirm%"=="S" (
    if exist "data\processed\*" del /q "data\processed\*"
    if exist "steam.db" del "steam.db"
    if exist "*.log" del "*.log"
    echo ✅ Dados limpos com sucesso!
) else (
    echo ❌ Operação cancelada
)
echo.
pause
goto MENU

:EXIT
echo.
echo 👋 Obrigado por usar o Steam ETL Dashboard!
echo.
exit /b 0
