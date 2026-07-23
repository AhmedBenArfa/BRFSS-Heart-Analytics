@echo off
REM ===========================================================================
REM  BRFSS Heart Analytics - Lanceur de l'application web
REM
REM  Double-cliquez sur ce fichier pour demarrer l'application. Concu pour
REM  fonctionner sur n'importe quel PC Windows :
REM    - trouve un Python utilisable (lanceur py, PATH, ou Anaconda),
REM    - ignore le faux "python" du Microsoft Store,
REM    - cree un environnement isole la premiere fois,
REM    - installe les dependances, puis lance Streamlit.
REM
REM  La premiere execution est plus longue (creation de l'environnement et
REM  telechargement des dependances). Les suivantes sont quasi immediates.
REM ===========================================================================

title BRFSS Heart Analytics - Application
cd /d "%~dp0"

echo ============================================================
echo   BRFSS Heart Analytics - Estimation du risque cardiaque
echo ============================================================
echo.

REM --- 1. Trouver un Python utilisable --------------------------------------
REM On teste chaque candidat en executant un petit script. Le stub Microsoft
REM Store echoue a ce test (code de retour non nul), il est donc ecarte.

set "PYCMD="

py -3 -c "import sys" 1>nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD python -c "import sys" 1>nul 2>nul && set "PYCMD=python"
if not defined PYCMD if exist "%USERPROFILE%\anaconda3\python.exe" set PYCMD="%USERPROFILE%\anaconda3\python.exe"
if not defined PYCMD if exist "%USERPROFILE%\miniconda3\python.exe" set PYCMD="%USERPROFILE%\miniconda3\python.exe"
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYCMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYCMD if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYCMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

if not defined PYCMD (
    echo [ERREUR] Aucun Python utilisable n'a ete trouve sur ce PC.
    echo.
    echo   Installez Python 3.10 ou plus recent depuis :
    echo     https://www.python.org/downloads/
    echo   En cochant la case "Add python.exe to PATH" pendant l'installation.
    echo   Puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)

echo Python detecte : %PYCMD%
echo.

REM --- 2. Environnement isole (cree une seule fois) -------------------------

if not exist ".venv\Scripts\python.exe" (
    echo Premiere execution : creation de l'environnement isole...
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] La creation de l'environnement a echoue.
        pause
        exit /b 1
    )
)

set "VENVPY=.venv\Scripts\python.exe"

REM --- 3. Dependances (rapide si deja installees) ---------------------------

echo Verification des dependances...
"%VENVPY%" -m pip install --quiet --disable-pip-version-check --requirement requirements.txt
if errorlevel 1 (
    echo [ERREUR] L'installation des dependances a echoue.
    echo Verifiez votre connexion internet, puis relancez ce fichier.
    pause
    exit /b 1
)

REM --- 4. Lancement ---------------------------------------------------------

echo.
echo ------------------------------------------------------------
echo   Application prete. Elle va s'ouvrir dans votre navigateur.
echo   Adresse : http://localhost:8501
echo   Fermez cette fenetre (ou Ctrl+C) pour arreter l'application.
echo ------------------------------------------------------------
echo.

"%VENVPY%" -m streamlit run streamlit_app.py

echo.
echo Application arretee.
pause
