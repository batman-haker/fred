#!/usr/bin/env python3
"""
Odkrywanie dodatkowych wskaźników FRED
Testuje dostępność i jakość danych
"""

import requests
from datetime import datetime, timedelta

API_KEY = 'fc1ef11c8f65429677a78db10a3a4d2e'
BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

# Dodatkowe wskaźniki do przetestowania
additional_indicators = {
    # === PODAŻ PIENIĄDZA ===
    'M1SL': 'M1 Money Supply (podaz pieniadza M1)',
    'M2SL': 'M2 Money Supply (podaz pieniadza M2)',
    'M2V': 'M2 Velocity (predkosc obiegu M2)',

    # === RYNEK KREDYTOWY ===
    'TOTLL': 'Total Loans and Leases (calkowite pozyczki)',
    'BUSLOANS': 'Commercial and Industrial Loans (pozyczki biznesowe)',
    'TOTCI': 'Commercial Paper Outstanding (papiery komercyjne)',

    # === SPREAD RATES ===
    'T10Y2Y': '10-Year minus 2-Year Treasury Spread',
    'T10Y3M': '10-Year minus 3-Month Treasury Spread',
    'BAMLH0A0HYM2': 'High Yield Spread (obligacje wysokodochodowe)',
    'TEDRATE': 'TED Spread (LIBOR-Treasury)',

    # === TREASURY RATES ===
    'DGS10': '10-Year Treasury Rate',
    'DGS2': '2-Year Treasury Rate',
    'DGS3MO': '3-Month Treasury Rate',

    # === WARUNKI FINANSOWE ===
    'NFCI': 'Chicago Fed National Financial Conditions Index',
    'ANFCI': 'Adjusted National Financial Conditions Index',
    'STLFSI4': 'St. Louis Fed Financial Stress Index',

    # === INFLACJA ===
    'CPIAUCSL': 'Consumer Price Index (CPI)',
    'CPILFESL': 'Core CPI (bez żywnosci i energii)',
    'PCEPI': 'PCE Price Index',
    'T5YIE': '5-Year Breakeven Inflation Rate',
    'T10YIE': '10-Year Breakeven Inflation Rate',

    # === RYNEK PRACY ===
    'UNRATE': 'Unemployment Rate (stopa bezrobocia)',
    'PAYEMS': 'Nonfarm Payrolls (zatrudnienie poza rolnictwem)',
    'ICSA': 'Initial Jobless Claims (wnioski o zasilek)',

    # === PKB I WZROST ===
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real GDP',
    'GDPPOT': 'Potential GDP',

    # === REPO MARKET ===
    'RPONTSYD': 'Overnight Reverse Repo (RRP - mamy już)',
    'REPO': 'Repo Rate',

    # === DOLAR I FOREX ===
    'DTWEXBGS': 'Trade Weighted U.S. Dollar Index (DXY)',
    'DEXUSEU': 'USD/EUR Exchange Rate',

    # === VOLATILITY ===
    'VIXCLS': 'CBOE Volatility Index (VIX)',

    # === CREDIT CONDITIONS ===
    'DRSFRMACBS': 'Net Percentage Banks Tightening Standards',
    'DRTSCILM': 'Net % Banks Tightening Standards - Large Firms',

    # === BANK RESERVES - ALTERNATIVE ===
    'BOGMBASE': 'Monetary Base (baza monetarna)',
    'WRESBAL': 'Reserve Balances with Federal Reserve Banks',

    # === FED OPERATIONS ===
    'WORAL': 'Federal Reserve Assets (aktywa Fed)',
    'WSHOMCB': 'Mortgage-Backed Securities Held by Fed',
}

print("="*80)
print("  ODKRYWANIE DODATKOWYCH WSKAZNIKOW FRED")
print("="*80)
print(f"\nTestuje {len(additional_indicators)} nowych wskaznikow...\n")

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

results = {
    'available': [],
    'limited': [],
    'unavailable': []
}

for series_id, description in additional_indicators.items():
    print(f"[TEST] {series_id}: {description}")

    params = {
        'series_id': series_id,
        'api_key': API_KEY,
        'file_type': 'json',
        'observation_start': start_date.strftime('%Y-%m-%d'),
        'observation_end': end_date.strftime('%Y-%m-%d'),
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'observations' in data:
                obs = data['observations']
                valid_obs = [o for o in obs if o['value'] != '.']

                if len(valid_obs) > 0:
                    latest = valid_obs[-1]
                    print(f"   [OK] Dostepne! Najnowsze: {latest['date']} = {latest['value']}")
                    print(f"   Obserwacji: {len(valid_obs)}")

                    results['available'].append({
                        'id': series_id,
                        'name': description,
                        'latest_date': latest['date'],
                        'latest_value': latest['value'],
                        'count': len(valid_obs)
                    })
                else:
                    print(f"   [WARN] Seria istnieje, ale brak danych w ostatnich 90 dniach")
                    results['limited'].append({
                        'id': series_id,
                        'name': description
                    })
            else:
                print(f"   [WARN] Brak obserwacji")
                results['unavailable'].append(series_id)
        else:
            print(f"   [ERROR] Status {response.status_code}")
            results['unavailable'].append(series_id)

    except Exception as e:
        print(f"   [ERROR] {e}")
        results['unavailable'].append(series_id)

    print()

# Podsumowanie
print("="*80)
print("  PODSUMOWANIE")
print("="*80)

print(f"\n[OK] Dostepne i aktualne ({len(results['available'])}):")
print("-"*80)
for item in results['available']:
    print(f"  {item['id']:15} - {item['name']}")
    print(f"  {'':15}   Najnowsze: {item['latest_date']} = {item['latest_value']}")

print(f"\n[WARN] Ograniczone dane ({len(results['limited'])}):")
print("-"*80)
for item in results['limited']:
    print(f"  {item['id']:15} - {item['name']}")

print(f"\n[ERROR] Niedostepne ({len(results['unavailable'])}):")
print("-"*80)
for series_id in results['unavailable']:
    print(f"  {series_id}")

print("\n" + "="*80)

# Rekomendacje
print("\n[REKOMENDACJE] Wskazniki do dodania:")
print("-"*80)

# Grupuj po kategoriach
categories = {
    'Podaz pieniadza': ['M1SL', 'M2SL', 'M2V', 'BOGMBASE'],
    'Stopy procentowe': ['DGS10', 'DGS2', 'DGS3MO', 'T10Y2Y', 'T10Y3M'],
    'Warunki finansowe': ['NFCI', 'ANFCI', 'STLFSI4', 'VIXCLS'],
    'Inflacja': ['CPIAUCSL', 'CPILFESL', 'T5YIE', 'T10YIE'],
    'Kredyt': ['TOTLL', 'BUSLOANS', 'TEDRATE'],
    'Dolar': ['DTWEXBGS'],
    'Rynek pracy': ['UNRATE', 'PAYEMS'],
    'Alternatywne rezerwy': ['WRESBAL', 'WORAL']
}

available_ids = [item['id'] for item in results['available']]

print("\nNajwazniejsze dla analizy plynnosci:")
priority_indicators = [
    ('M2SL', 'Podaz pieniadza M2 - kluczowy wskaznik plynnosci'),
    ('WRESBAL', 'Rezerwy bankow (alternatywa dla TOTRESNS)'),
    ('DGS10', 'Stopa 10-letnia - benchmark rynku'),
    ('T10Y2Y', 'Krzywa dochodowosci - wskaznik recesji'),
    ('NFCI', 'Warunki finansowe - kompleksowy wskaznik'),
    ('VIXCLS', 'VIX - strach na rynku'),
    ('DTWEXBGS', 'Indeks dolara - wplyw na globalna plynnosc'),
    ('TEDRATE', 'TED Spread - napicia w systemie bankowym'),
    ('CPIAUCSL', 'Inflacja - wplyw na polityka Fed'),
]

for series_id, reason in priority_indicators:
    if series_id in available_ids:
        print(f"  [+] {series_id:12} - {reason}")
    else:
        print(f"  [-] {series_id:12} - {reason} (NIEDOSTEPNE)")

print("\n" + "="*80)
