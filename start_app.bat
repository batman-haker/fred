@echo off
REM Skrypt uruchamiający aplikację Liquidity Monitor
echo ============================================
echo   Liquidity Monitor - Uruchamianie...
echo ============================================
echo.

REM Sprawdź czy Python jest zainstalowany
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   BŁĄD: Python nie jest zainstalowany!
    echo ========================================
    echo.
    echo 1. Pobierz Python z: https://www.python.org/downloads/
    echo 2. Podczas instalacji ZAZNACZ: "Add Python to PATH"
    echo 3. Po instalacji ZRESTARTUJ terminal
    echo.
    echo Szczegółowa instrukcja: INSTALACJA_WINDOWS.md
    echo.
    pause
    exit /b 1
)

echo ✓ Python znaleziony
python --version
echo.

REM Sprawdź czy streamlit jest zainstalowany
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Streamlit nie jest zainstalowany. Instaluję zależności...
    echo To może potrwać 2-5 minut...
    echo.
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo BŁĄD: Nie udało się zainstalować zależności!
        echo Spróbuj ręcznie: python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo ✓ Zależności OK
echo.

REM Uruchom aplikację Streamlit
echo ============================================
echo   Uruchamianie aplikacji webowej...
echo ============================================
echo.
echo Aplikacja otworzy się w przeglądarce
echo Adres: http://localhost:8501
echo.
echo Aby zatrzymać aplikację, naciśnij Ctrl+C
echo.

python -m streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   BŁĄD podczas uruchamiania!
    echo ========================================
    echo.
    echo Spróbuj uruchomić test:
    echo   python test_setup.py
    echo.
    pause
)

pause
