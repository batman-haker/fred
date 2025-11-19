#!/usr/bin/env python3
"""
Test Setup - Sprawdza czy wszystko jest poprawnie zainstalowane
"""

import sys

print("="*60)
print("  TEST INSTALACJI - Liquidity Monitor")
print("="*60)
print()

# Test 1: Python
print(f"✅ Python działa! Wersja: {sys.version.split()[0]}")

# Test 2: Moduły
modules_to_test = [
    ('requests', 'Requests'),
    ('pandas', 'Pandas'),
    ('streamlit', 'Streamlit'),
    ('plotly', 'Plotly'),
]

missing_modules = []

for module_name, display_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {display_name} zainstalowane")
    except ImportError:
        print(f"❌ {display_name} BRAK - zainstaluj: pip install {module_name}")
        missing_modules.append(module_name)

# Test 3: Klucz API
import os
print()
if os.path.exists('.env'):
    print("✅ Plik .env znaleziony")
    with open('.env', 'r') as f:
        content = f.read()
        if 'FRED_API_KEY' in content:
            print("✅ Klucz API skonfigurowany w .env")
        else:
            print("⚠️  Klucz API nie znaleziony w .env")
else:
    print("⚠️  Plik .env nie znaleziony - będziesz musiał wprowadzić klucz ręcznie")

# Test 4: Pliki
print()
required_files = [
    'app.py',
    'liquidity_monitor.py',
    'requirements.txt',
]

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file} - OK")
    else:
        print(f"❌ {file} - BRAK!")

print()
print("="*60)

if missing_modules:
    print("❌ BRAK MODUŁÓW!")
    print()
    print("Zainstaluj brakujące moduły:")
    print(f"  python -m pip install {' '.join(missing_modules)}")
    print()
    print("Lub wszystkie naraz:")
    print("  python -m pip install -r requirements.txt")
else:
    print("✅ WSZYSTKO GOTOWE!")
    print()
    print("Uruchom aplikację:")
    print("  python -m streamlit run app.py")
    print()
    print("Lub kliknij dwukrotnie: start_app.bat")

print("="*60)
