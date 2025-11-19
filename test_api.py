#!/usr/bin/env python3
"""
Test FRED API - Sprawdza czy klucz działa i jakie dane można pobrać
"""

import requests
from datetime import datetime, timedelta

API_KEY = 'fc1ef11c8f65429677a78db10a3a4d2e'
BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

print("="*70)
print("  TEST FRED API KEY")
print("="*70)
print(f"\nKlucz API: {API_KEY}")
print()

# Definicje serii do testowania
test_series = {
    'TOTRESNS': 'Rezerwy Banków (Bank Reserves)',
    'WTREGEN': 'TGA (Treasury General Account)',
    'RRPONTSYD': 'Reverse Repo (ON RRP)',
    'WALCL': 'Bilans Fed (Fed Balance Sheet)',
    'SOFR': 'SOFR (Secured Overnight Financing Rate)',
    'IORB': 'IORB (Interest on Reserve Balances)',
    'EFFR': 'EFFR (Effective Federal Funds Rate)',
}

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

print("Testuję pobieranie danych dla każdej serii...\n")
print("-"*70)

successful = 0
failed = 0

for series_id, name in test_series.items():
    print(f"\n[TEST] {name} ({series_id})")
    print("   Pobieranie danych...")

    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'observation_start': start_date.strftime('%Y-%m-%d'),
        'observation_end': end_date.strftime('%Y-%m-%d'),
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        print(f"   Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'observations' in data and len(data['observations']) > 0:
                observations = data['observations']
                latest = observations[-1]

                print(f"   [OK] SUKCES!")
                print(f"   Najnowsza data: {latest['date']}")
                print(f"   Wartosc: {latest['value']}")
                print(f"   Liczba obserwacji: {len(observations)}")
                successful += 1
            else:
                print(f"   [WARN] Brak danych w odpowiedzi")
                print(f"   Odpowiedz: {data}")
                failed += 1

        elif response.status_code == 400:
            error_data = response.json()
            print(f"   [ERROR] BLAD 400: {error_data.get('error_message', 'Nieznany blad')}")
            failed += 1

        elif response.status_code == 403:
            print(f"   [ERROR] BLAD 403: Brak dostepu - klucz API nieprawidlowy!")
            failed += 1

        else:
            print(f"   [ERROR] BLAD {response.status_code}")
            print(f"   Odpowiedz: {response.text[:200]}")
            failed += 1

    except requests.exceptions.Timeout:
        print(f"   [ERROR] TIMEOUT - serwer nie odpowiada")
        failed += 1

    except Exception as e:
        print(f"   [ERROR] BLAD: {e}")
        failed += 1

print("\n" + "="*70)
print("  PODSUMOWANIE")
print("="*70)
print(f"\n[OK] Udane: {successful}/{len(test_series)}")
print(f"[ERROR] Nieudane: {failed}/{len(test_series)}")

if successful == len(test_series):
    print("\n[SUCCESS] WSZYSTKO DZIALA! Klucz API jest prawidlowy!")
    print("\nMozesz uzyc tego klucza w aplikacji.")
elif successful > 0:
    print("\n[WARN] Klucz dziala, ale niektore serie nie sa dostepne.")
    print("   To normalne - niektore serie moga byc aktualizowane z opoznieniem.")
else:
    print("\n[ERROR] KLUCZ API NIE DZIALA!")
    print("\nMozliwe przyczyny:")
    print("1. Klucz jest nieprawidlowy")
    print("2. Klucz wygasl lub zostal dezaktywowany")
    print("3. Brak polaczenia z internetem")
    print("4. Problem z serwerem FRED")
    print("\nZarejestruj nowy klucz na:")
    print("https://fred.stlouisfed.org/docs/api/api_key.html")

print("\n" + "="*70)
