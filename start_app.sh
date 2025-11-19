#!/bin/bash
# Skrypt uruchamiający aplikację Liquidity Monitor

echo "============================================"
echo "  Liquidity Monitor - Uruchamianie..."
echo "============================================"
echo ""

# Sprawdź czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "BŁĄD: Python3 nie jest zainstalowany!"
    echo "Zainstaluj Python3 przed uruchomieniem."
    exit 1
fi

# Sprawdź czy streamlit jest zainstalowany
if ! command -v streamlit &> /dev/null; then
    echo "Instaluję zależności..."
    pip3 install -r requirements.txt
fi

# Załaduj zmienne środowiskowe z .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Uruchom aplikację Streamlit
echo ""
echo "Uruchamianie aplikacji webowej..."
echo "Aplikacja otworzy się w przeglądarce na http://localhost:8501"
echo ""
echo "Aby zatrzymać aplikację, naciśnij Ctrl+C"
echo ""

streamlit run app.py
