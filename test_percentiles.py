#!/usr/bin/env python3
"""Test percentyli"""

import os
from dotenv import load_dotenv
from liquidity_monitor import LiquidityMonitor

load_dotenv()

api_key = os.environ.get('FRED_API_KEY')
monitor = LiquidityMonitor(fred_api_key=api_key)

print("Pobieram dane...")
indicators = monitor.get_all_indicators(days_back=365)

print(f"\nZnaleziono {len(indicators)} wskaźników")

print("\nObliczam percentyle...")
percentiles = monitor.calculate_percentiles(indicators)

print(f"\nPercentyle obliczone dla {len(percentiles)} wskaźników")

if percentiles:
    print("\nPrzykładowy percentyl:")
    first_key = list(percentiles.keys())[0]
    p = percentiles[first_key]
    print(f"{first_key}: {p}")
else:
    print("\nBRAK PERCENTYLI - BŁĄD!")

    # Debug - sprawdź czy są dane historyczne
    for name, data in indicators.items():
        if 'history' in data:
            print(f"{name}: historia ma {len(data['history'])} wartości")
        else:
            print(f"{name}: BRAK HISTORII!")
