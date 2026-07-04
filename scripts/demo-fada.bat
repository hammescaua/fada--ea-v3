@echo off
REM ===========================================================================
REM  FADA - demonstracao de 1 clique (Windows)
REM  Sobe a API + a web e abre o navegador ja com o talhao de demonstracao.
REM  Uso: dê um duplo-clique neste arquivo (ou rode no Prompt de Comando).
REM  Pre-requisito: o projeto ja instalado uma vez
REM    (apps\api\.venv criado e apps\web\node_modules instalado).
REM ===========================================================================
setlocal
cd /d "%~dp0\.."

echo.
echo  FADA - preparando a demonstracao...
echo.

if not exist "apps\api\.venv\Scripts\activate.bat" (
  echo  [ERRO] Falta o ambiente da API ^(apps\api\.venv^).
  echo         Rode uma vez:  cd apps\api ^&^& python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -e .
  pause
  exit /b 1
)
if not exist "apps\web\node_modules" (
  echo  [ERRO] Falta instalar a web ^(apps\web\node_modules^).
  echo         Rode uma vez:  cd apps\web ^&^& npm install
  pause
  exit /b 1
)

echo  -^> subindo a API (porta 8000) em uma nova janela...
start "FADA API" cmd /k "cd apps\api && call .venv\Scripts\activate && uvicorn app.main:app --port 8000"

echo  -^> subindo a interface web (porta 3000) em uma nova janela...
start "FADA Web" cmd /k "cd apps\web && npx next dev -p 3000"

echo  -^> aguardando os servidores iniciarem (cerca de 20s)...
timeout /t 20 /nobreak >nul

echo  -^> abrindo o navegador com o talhao de demonstracao...
start "" "http://localhost:3000/fada-demo-seed.html"

echo.
echo  Pronto! A demonstracao esta no ar.
echo    - App:   http://localhost:3000
echo    - Recarregar dados de demo:  http://localhost:3000/fada-demo-seed.html
echo.
echo  A primeira vez que abrir cada pagina leva alguns segundos para compilar.
echo  Para encerrar: feche as duas janelas "FADA API" e "FADA Web".
echo.
pause
endlocal
