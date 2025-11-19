#!/usr/bin/env python3
"""
Liquidity Monitor - System monitorowania wskaźników płynności rynkowej
Śledzi: TGA, rezerwy banków, SOFR, reverse repo, bilans Fed
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import time


class LiquidityMonitor:
    """Monitoruje kluczowe wskaźniki płynności finansowej"""
    
    def __init__(self, fred_api_key: Optional[str] = None):
        """
        Args:
            fred_api_key: Klucz API do FRED (opcjonalny, ale zalecany)
                         Rejestracja: https://fred.stlouisfed.org/docs/api/api_key.html
        """
        self.fred_api_key = fred_api_key
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Definicje serii danych FRED
        self.series = {
            # Podstawowe wskazniki plynnosci
            'reserves': 'TOTRESNS',      # Rezerwy bankow w Fed (czesto brak danych)
            'reserves_alt': 'WRESBAL',   # Rezerwy bankow (alternatywa - dziala!)
            'tga': 'WTREGEN',            # Treasury General Account
            'reverse_repo': 'RRPONTSYD', # Reverse Repo (ON RRP)
            'fed_balance': 'WALCL',      # Bilans Fed

            # Stopy procentowe
            'sofr': 'SOFR',              # Secured Overnight Financing Rate
            'iorb': 'IORB',              # Interest on Reserve Balances
            'effr': 'EFFR',              # Effective Federal Funds Rate

            # TIER 1 - Nowe wskazniki
            'm2': 'M2SL',                # M2 Money Supply
            'yield_curve': 'T10Y2Y',     # 10Y-2Y Treasury Spread (recesja!)
            'vix': 'VIXCLS',             # VIX - strach na rynku
            'fin_conditions': 'NFCI',    # Financial Conditions Index
            'dollar_index': 'DTWEXBGS',  # Dollar Index (DXY)

            # TIER 2 - Dodatkowe wskazniki
            'treasury_10y': 'DGS10',     # 10-Year Treasury Rate
            'treasury_2y': 'DGS2',       # 2-Year Treasury Rate
            'inflation_5y': 'T5YIE',     # 5-Year Breakeven Inflation
            'hy_spread': 'BAMLH0A0HYM2', # High Yield Spread
            'unemployment': 'UNRATE',    # Unemployment Rate
        }
        
        # Progi dla alertów
        self.thresholds = {
            # Rezerwy
            'reserves_minimum': 2800,  # mld USD - minimum "wystarczajace"
            'reserves_comfortable': 3000,  # mld USD - komfortowy poziom

            # SOFR spread
            'sofr_iorb_spread_warning': 0.10,  # 10 bps - ostrzezenie
            'sofr_iorb_spread_critical': 0.20,  # 20 bps - krytyczne

            # TIER 1 - Nowe progi
            'yield_curve_inverted': 0.0,  # Ujemna krzywa = recesja blisko!
            'yield_curve_steep': 1.0,  # Bardzo stroma = ekspansja
            'vix_fear': 30,  # VIX > 30 = panika
            'vix_greed': 15,  # VIX < 15 = spokój/zadowolenie
            'nfci_tight': 0.0,  # NFCI > 0 = napięcia finansowe
            'nfci_loose': -0.5,  # NFCI < -0.5 = luźne warunki
            'dollar_strong': 125,  # DXY > 125 = bardzo silny dolar
            'dollar_weak': 100,  # DXY < 100 = słaby dolar

            # TIER 2 - Nowe progi
            'treasury_10y_high': 5.0,  # 10Y > 5% = wysokie stopy
            'treasury_10y_low': 2.0,   # 10Y < 2% = niskie stopy
            'inflation_high': 3.0,     # Inflacja > 3% = wysoka
            'inflation_low': 1.5,      # Inflacja < 1.5% = niska
            'hy_spread_high': 5.0,     # HY spread > 5% = strach o kredyt
            'unemployment_high': 5.0,  # Bezrobocie > 5% = słabe
            'unemployment_low': 4.0,   # Bezrobocie < 4% = mocne
        }

        # === SYSTEM WAG ===
        # Wagi określają jak ważny jest dany wskaźnik (suma = 100%)
        self.indicator_weights = {
            # KRYTYCZNE (łącznie 40%) - bezpośredni wpływ na płynność
            'reserves': 0.15,           # 15% - podstawa systemu
            'yield_curve': 0.15,        # 15% - sygnał recesji
            'sofr_spread': 0.10,        # 10% - napięcia w finansowaniu

            # WAŻNE (łącznie 30%) - warunki rynkowe
            'vix': 0.10,                # 10% - sentyment/strach
            'nfci': 0.10,               # 10% - warunki finansowe
            'hy_spread': 0.10,          # 10% - ryzyko kredytowe

            # POMOCNICZE (łącznie 30%) - kontekst makro
            'tga': 0.08,                # 8% - ruch płynności
            'reverse_repo': 0.07,       # 7% - bufor płynności
            'fed_balance': 0.05,        # 5% - polityka Fed (QE/QT)
            'm2': 0.04,                 # 4% - podaż pieniądza
            'dollar_index': 0.03,       # 3% - globalny wpływ
            'treasury_10y': 0.03,       # 3% - koszt kapitału
            'inflation_5y': 0.03,       # 3% - oczekiwania inflacyjne
            'unemployment': 0.02,       # 2% - rynek pracy
        }

        # === REŻIMY RYNKOWE ===
        # Różne warunki rynkowe wymagają różnej interpretacji sygnałów
        self.market_regimes = {
            'RISK_ON': {
                'name': 'RISK-ON (Ekspansja)',
                'description': 'Rynek w trybie wzrostowym, optymizm',
                'multiplier': 1.0,  # Normalne wagi
                'conditions': {
                    'vix': {'max': 20},
                    'nfci': {'max': 0},
                    'yield_curve': {'min': 0.25},
                }
            },
            'RISK_OFF': {
                'name': 'RISK-OFF (Niepewność)',
                'description': 'Niepewność, zmienność, ostrożność',
                'multiplier': 1.3,  # Sygnały negatywne liczą się mocniej
                'conditions': {
                    'vix': {'min': 20, 'max': 30},
                    'OR': True  # Jeden z warunków wystarczy
                }
            },
            'CRISIS': {
                'name': 'KRYZYS (Panika)',
                'description': 'Kryzysowe warunki, ekstremalne napięcia',
                'multiplier': 1.8,  # Sygnały kryzysowe x2
                'conditions': {
                    'vix': {'min': 30},
                    'OR': [
                        {'yield_curve': {'max': -0.5}},  # Mocno odwrócona
                        {'nfci': {'min': 0.5}},          # Bardzo napięte
                        {'hy_spread': {'min': 7.0}},     # Panika kredytowa
                    ]
                }
            },
        }

    def detect_market_regime(self, indicators: Dict) -> Dict:
        """
        Wykrywa obecny reżim rynkowy na podstawie kluczowych wskaźników

        Returns:
            Dict z informacją o reżimie i multiplikatorze
        """
        regime_info = {
            'regime': 'RISK_ON',  # Domyślnie
            'name': 'RISK-ON (Ekspansja)',
            'description': 'Normalne warunki rynkowe',
            'multiplier': 1.0,
            'triggers': []
        }

        # Sprawdź warunki KRYZYSU (najwyższy priorytet)
        crisis_triggers = []

        if 'vix' in indicators:
            vix = indicators['vix']['current']
            if vix >= 30:
                crisis_triggers.append(f'VIX ekstremalne: {vix:.1f}')

        if 'yield_curve' in indicators:
            curve = indicators['yield_curve']['current']
            if curve <= -0.5:
                crisis_triggers.append(f'Krzywa mocno odwrócona: {curve:.2f}%')

        if 'nfci' in indicators:
            nfci = indicators['nfci']['current']
            if nfci >= 0.5:
                crisis_triggers.append(f'NFCI bardzo napięty: {nfci:.2f}')

        if 'hy_spread' in indicators:
            hy = indicators['hy_spread']['current']
            if hy >= 7.0:
                crisis_triggers.append(f'HY Spread panika: {hy:.2f}%')

        if len(crisis_triggers) >= 1:  # Jeden wystarczy
            regime_info['regime'] = 'CRISIS'
            regime_info['name'] = 'KRYZYS (Panika)'
            regime_info['description'] = 'Ekstremalne napięcia rynkowe'
            regime_info['multiplier'] = 1.8
            regime_info['triggers'] = crisis_triggers
            return regime_info

        # Sprawdź warunki RISK-OFF
        risk_off_triggers = []

        if 'vix' in indicators:
            vix = indicators['vix']['current']
            if 20 <= vix < 30:
                risk_off_triggers.append(f'VIX podwyższony: {vix:.1f}')

        if 'nfci' in indicators:
            nfci = indicators['nfci']['current']
            if nfci > 0:
                risk_off_triggers.append(f'NFCI napięty: {nfci:.2f}')

        if 'yield_curve' in indicators:
            curve = indicators['yield_curve']['current']
            if -0.5 < curve < 0:
                risk_off_triggers.append(f'Krzywa odwrócona: {curve:.2f}%')

        if len(risk_off_triggers) >= 1:
            regime_info['regime'] = 'RISK_OFF'
            regime_info['name'] = 'RISK-OFF (Niepewność)'
            regime_info['description'] = 'Podwyższona niepewność i zmienność'
            regime_info['multiplier'] = 1.3
            regime_info['triggers'] = risk_off_triggers
            return regime_info

        # RISK-ON (domyślny, optymistyczny)
        risk_on_triggers = []

        if 'vix' in indicators:
            vix = indicators['vix']['current']
            if vix < 20:
                risk_on_triggers.append(f'VIX spokojny: {vix:.1f}')

        if 'nfci' in indicators:
            nfci = indicators['nfci']['current']
            if nfci < 0:
                risk_on_triggers.append(f'NFCI luźne warunki: {nfci:.2f}')

        if 'yield_curve' in indicators:
            curve = indicators['yield_curve']['current']
            if curve >= 0.25:
                risk_on_triggers.append(f'Krzywa pozytywna: {curve:.2f}%')

        regime_info['triggers'] = risk_on_triggers if risk_on_triggers else ['Brak wyraźnych sygnałów']

        return regime_info

    def calculate_percentiles(self, indicators: Dict) -> Dict:
        """
        Oblicza percentyle historyczne dla każdego wskaźnika

        Zamiast stałych progów (VIX > 30), używamy percentyli:
        - 95+ percentyl = ekstremalnie wysoki
        - 75-95 = wysoki
        - 25-75 = normalny
        - 5-25 = niski
        - <5 = ekstremalnie niski

        Returns:
            Dict z percentylami dla każdego wskaźnika
        """
        percentiles = {}

        for indicator_name, data in indicators.items():
            if 'history' not in data or len(data['history']) < 10:
                continue  # Nie ma wystarczającej historii

            # Pobierz wartości historyczne (ostatnie N dni)
            history_values = [float(val) for val in data['history'].values if val != '.']

            if len(history_values) < 10:
                continue

            current = data['current']

            # Prostszy sposób - ile % wartości jest mniejszych od obecnej
            below = sum(1 for v in history_values if v < current)
            percentile_rank = (below / len(history_values)) * 100

            percentiles[indicator_name] = {
                'current': current,
                'percentile': percentile_rank,
                'historical_min': min(history_values),
                'historical_max': max(history_values),
                'historical_mean': np.mean(history_values),
                'historical_std': np.std(history_values),
                'interpretation': self._interpret_percentile(percentile_rank, indicator_name)
            }

        print(f"\n[PERCENTILES] Obliczono percentyle dla {len(percentiles)} wskaźników")

        return percentiles

    def _interpret_percentile(self, percentile: float, indicator: str) -> str:
        """Interpretuje percentyl wskaźnika"""

        # Dla wskaźników gdzie WYSOKI = ZŁY (VIX, spreads, NFCI)
        bad_high = ['vix', 'hy_spread', 'nfci', 'sofr', 'treasury_10y', 'unemployment']

        # Dla wskaźników gdzie NISKI = ZŁY (rezerwy, M2, krzywa)
        bad_low = ['reserves', 'm2', 'yield_curve', 'reverse_repo', 'fed_balance']

        if percentile >= 95:
            if any(ind in indicator for ind in bad_high):
                return "🔴 EKSTREMALNIE WYSOKI (top 5%) - bardzo zły!"
            else:
                return "🟢 EKSTREMALNIE WYSOKI (top 5%) - bardzo dobry!"
        elif percentile >= 75:
            if any(ind in indicator for ind in bad_high):
                return "🟡 WYSOKI (top 25%) - powyżej normy"
            else:
                return "🟢 WYSOKI (top 25%) - powyżej normy"
        elif percentile >= 25:
            return "⚪ NORMALNY (środkowe 50%)"
        elif percentile >= 5:
            if any(ind in indicator for ind in bad_low):
                return "🟡 NISKI (bottom 25%) - poniżej normy"
            else:
                return "🟢 NISKI (bottom 25%) - poniżej normy"
        else:
            if any(ind in indicator for ind in bad_low):
                return "🔴 EKSTREMALNIE NISKI (bottom 5%) - bardzo zły!"
            else:
                return "🟢 EKSTREMALNIE NISKI (bottom 5%) - bardzo dobry!"

    def detect_correlations_and_conflicts(self, indicators: Dict) -> Dict:
        """
        Wykrywa korelacje, konflikty i compound signals między wskaźnikami

        Returns:
            Dict z wykrytymi wzorcami, konfliktami i wzmocnieniami
        """
        patterns = {
            'conflicts': [],      # Paradoksy i sprzeczności
            'reinforcements': [], # Wzmocnienia (wskaźniki się zgadzają)
            'compound_signals': [], # Potężne kombinacje (3+ wskaźniki)
            'score_adjustments': 0  # Dodatkowe punkty z korelacji
        }

        # === PARADOKSY / KONFLIKTY ===

        # 1. "Panika mimo płynności"
        if 'vix' in indicators and 'reserves' in indicators:
            vix = indicators['vix']['current']
            reserves = indicators['reserves']['current']

            if vix > 25 and reserves > 3200:
                patterns['conflicts'].append({
                    'type': 'paradox',
                    'name': 'PARADOKS: Panika mimo wysokiej płynności',
                    'description': f'VIX wysoki ({vix:.1f}) ale rezerwy wysokie (${reserves:.0f}B)',
                    'interpretation': 'Strach może być przesadzony - płynność jest dobra. Potencjalna okazja do kupna.',
                    'severity': 'medium',
                    'score_impact': +10  # Paradoks może być pozytywny
                })
                patterns['score_adjustments'] += 10

        # 2. "Spokój mimo napięć"
        if 'vix' in indicators and 'nfci' in indicators:
            vix = indicators['vix']['current']
            nfci = indicators['nfci']['current']

            if vix < 15 and nfci > 0.3:
                patterns['conflicts'].append({
                    'type': 'paradox',
                    'name': 'PARADOKS: VIX spokojny mimo napięć finansowych',
                    'description': f'VIX niski ({vix:.1f}) ale NFCI napięty ({nfci:.2f})',
                    'interpretation': 'Rynek może ignorować realne ryzyko - FALSE CALM. Niebezpieczne!',
                    'severity': 'high',
                    'score_impact': -15
                })
                patterns['score_adjustments'] -= 15

        # 3. "Fed walczy z recesją" (QE w obliczu kryzysu)
        if 'yield_curve' in indicators and 'm2' in indicators:
            curve = indicators['yield_curve']['current']
            m2_change = indicators['m2']['change_7d']

            if curve < -0.2 and m2_change > 50:
                patterns['conflicts'].append({
                    'type': 'policy_response',
                    'name': 'Fed walczy z recesją (QE)',
                    'description': f'Krzywa odwrócona ({curve:.2f}%) ale M2 rośnie (+{m2_change:.0f}B)',
                    'interpretation': 'Fed drukuje pieniądze mimo sygnału recesji. Ratunkowa akcja - bullish dla aktywów.',
                    'severity': 'medium',
                    'score_impact': +20
                })
                patterns['score_adjustments'] += 20

        # === WZMOCNIENIA (Reinforcements) ===

        # 4. "Perfect Risk-On"
        risk_on_signals = []
        if 'vix' in indicators and indicators['vix']['current'] < 15:
            risk_on_signals.append(f"VIX: {indicators['vix']['current']:.1f}")
        if 'nfci' in indicators and indicators['nfci']['current'] < -0.5:
            risk_on_signals.append(f"NFCI: {indicators['nfci']['current']:.2f}")
        if 'yield_curve' in indicators and indicators['yield_curve']['current'] > 0.5:
            risk_on_signals.append(f"Krzywa: {indicators['yield_curve']['current']:.2f}%")
        if 'hy_spread' in indicators and indicators['hy_spread']['current'] < 3.5:
            risk_on_signals.append(f"HY Spread: {indicators['hy_spread']['current']:.2f}%")

        if len(risk_on_signals) >= 3:
            patterns['reinforcements'].append({
                'type': 'perfect_risk_on',
                'name': '🟢 PERFECT RISK-ON',
                'description': f'Wszystkie sygnały zielone: {", ".join(risk_on_signals)}',
                'interpretation': 'Idealne warunki dla wzrostowych aktywów. FULL RISK ON!',
                'strength': len(risk_on_signals),
                'score_impact': +15
            })
            patterns['score_adjustments'] += 15

        # 5. "Triple Threat" (3 sygnały stresowe jednocześnie)
        stress_signals = []
        if 'vix' in indicators and indicators['vix']['current'] > 25:
            stress_signals.append(f"VIX: {indicators['vix']['current']:.1f}")
        if 'yield_curve' in indicators and indicators['yield_curve']['current'] < -0.2:
            stress_signals.append(f"Krzywa: {indicators['yield_curve']['current']:.2f}%")
        if 'hy_spread' in indicators and indicators['hy_spread']['current'] > 5.0:
            stress_signals.append(f"HY Spread: {indicators['hy_spread']['current']:.2f}%")
        if 'nfci' in indicators and indicators['nfci']['current'] > 0.5:
            stress_signals.append(f"NFCI: {indicators['nfci']['current']:.2f}")

        if len(stress_signals) >= 3:
            patterns['reinforcements'].append({
                'type': 'triple_threat',
                'name': '🔴 TRIPLE THREAT (Ekstremalne ryzyko)',
                'description': f'Wielokrotne sygnały stresowe: {", ".join(stress_signals)}',
                'interpretation': 'ALARM! Wszystkie sygnały krzyczą: UCIECZKA! Maksymalna ostrożność.',
                'strength': len(stress_signals),
                'score_impact': -25
            })
            patterns['score_adjustments'] -= 25

        # 6. "Liquidity Drain" (Drenowanie z wielu źródeł)
        drain_signals = []
        if 'reserves' in indicators and indicators['reserves']['change_7d'] < -30:
            drain_signals.append(f"Rezerwy: {indicators['reserves']['change_7d']:.0f}B")
        if 'tga' in indicators and indicators['tga']['change_7d'] > 30:
            drain_signals.append(f"TGA: +{indicators['tga']['change_7d']:.0f}B")
        if 'reverse_repo' in indicators and indicators['reverse_repo']['change_7d'] < -20:
            drain_signals.append(f"RRP: {indicators['reverse_repo']['change_7d']:.0f}B")
        if 'fed_balance' in indicators and indicators['fed_balance']['change_7d'] < -15:
            drain_signals.append(f"Fed BS: {indicators['fed_balance']['change_7d']:.0f}B")

        if len(drain_signals) >= 2:
            patterns['compound_signals'].append({
                'type': 'liquidity_drain',
                'name': '⚠️ LIQUIDITY DRAIN (Wielokrotny odpływ)',
                'description': f'Płynność ucieka z wielu źródeł: {", ".join(drain_signals)}',
                'interpretation': 'Systemowe drenowanie płynności. Fed może zacieśniać - bearish.',
                'components': len(drain_signals),
                'score_impact': -15
            })
            patterns['score_adjustments'] -= 15

        # 7. "Liquidity Flood" (Zalew z wielu źródeł)
        flood_signals = []
        if 'reserves' in indicators and indicators['reserves']['change_7d'] > 30:
            flood_signals.append(f"Rezerwy: +{indicators['reserves']['change_7d']:.0f}B")
        if 'tga' in indicators and indicators['tga']['change_7d'] < -30:
            flood_signals.append(f"TGA: {indicators['tga']['change_7d']:.0f}B")
        if 'fed_balance' in indicators and indicators['fed_balance']['change_7d'] > 15:
            flood_signals.append(f"Fed BS: +{indicators['fed_balance']['change_7d']:.0f}B")
        if 'm2' in indicators and indicators['m2']['change_7d'] > 100:
            flood_signals.append(f"M2: +{indicators['m2']['change_7d']:.0f}B")

        if len(flood_signals) >= 2:
            patterns['compound_signals'].append({
                'type': 'liquidity_flood',
                'name': '💰 LIQUIDITY FLOOD (Zalew płynności)',
                'description': f'Płynność leje się z wielu źródeł: {", ".join(flood_signals)}',
                'interpretation': 'Masywna ekspansja płynności. Fed pompuje - MEGA BULLISH!',
                'components': len(flood_signals),
                'score_impact': +20
            })
            patterns['score_adjustments'] += 20

        # 8. "Credit Crunch Warning"
        credit_signals = []
        if 'hy_spread' in indicators and indicators['hy_spread']['current'] > 6.0:
            credit_signals.append(f"HY Spread: {indicators['hy_spread']['current']:.2f}%")
        if 'sofr' in indicators and 'iorb' in indicators:
            sofr_spread = indicators['sofr']['current'] - indicators['iorb']['current']
            if sofr_spread > 0.15:
                credit_signals.append(f"SOFR spread: {sofr_spread:.2f}%")
        if 'nfci' in indicators and indicators['nfci']['current'] > 0.3:
            credit_signals.append(f"NFCI: {indicators['nfci']['current']:.2f}")

        if len(credit_signals) >= 2:
            patterns['compound_signals'].append({
                'type': 'credit_crunch',
                'name': '🚨 CREDIT CRUNCH WARNING',
                'description': f'Napięcia kredytowe z wielu źródeł: {", ".join(credit_signals)}',
                'interpretation': 'Trudności z finansowaniem! Ryzyko zamrożenia kredytu. DEFENSIVE!',
                'components': len(credit_signals),
                'score_impact': -20
            })
            patterns['score_adjustments'] -= 20

        print(f"\n[CORRELATIONS] Wykryto:")
        print(f"  Konflikty: {len(patterns['conflicts'])}")
        print(f"  Wzmocnienia: {len(patterns['reinforcements'])}")
        print(f"  Compound signals: {len(patterns['compound_signals'])}")
        print(f"  Score adjustment: {patterns['score_adjustments']:+.0f}")

        return patterns

    def fetch_fred_data(self, series_id: str, days_back: int = 90) -> pd.DataFrame:
        """
        Pobiera dane z FRED API
        
        Args:
            series_id: ID serii w FRED
            days_back: Ile dni wstecz pobrać dane
        """
        if not self.fred_api_key:
            print(f"[WARN] Brak klucza API FRED - nie moge pobrac danych dla {series_id}")
            print("   Zarejestruj sie na: https://fred.stlouisfed.org/docs/api/api_key.html")
            return pd.DataFrame()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'series_id': series_id,
            'api_key': self.fred_api_key,
            'file_type': 'json',
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
        }
        
        try:
            response = requests.get(self.fred_base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'observations' not in data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df[['date', 'value']].dropna()
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Blad pobierania {series_id}: {e}")
            return pd.DataFrame()
    
    def fetch_ny_fed_sofr(self) -> Dict:
        """
        Pobiera aktualne dane SOFR z NY Fed
        Strona: https://www.newyorkfed.org/markets/reference-rates/sofr
        """
        # NY Fed ma API, ale wymaga parsowania lub web scraping
        # Dla uproszczenia używamy FRED
        sofr_data = self.fetch_fred_data('SOFR', days_back=30)
        
        if sofr_data.empty:
            return {}
        
        latest = sofr_data.iloc[-1]
        previous = sofr_data.iloc[-2] if len(sofr_data) > 1 else None
        
        return {
            'rate': latest['value'],
            'date': latest['date'].strftime('%Y-%m-%d'),
            'change': latest['value'] - previous['value'] if previous is not None else 0,
        }
    
    def fetch_reverse_repo(self) -> Dict:
        """Pobiera dane ON RRP"""
        rrp_data = self.fetch_fred_data('RRPONTSYD', days_back=30)
        
        if rrp_data.empty:
            return {}
        
        latest = rrp_data.iloc[-1]
        previous = rrp_data.iloc[-2] if len(rrp_data) > 1 else None
        
        return {
            'amount': latest['value'],
            'date': latest['date'].strftime('%Y-%m-%d'),
            'change': latest['value'] - previous['value'] if previous is not None else 0,
        }
    
    def get_all_indicators(self, days_back: int = 90) -> Dict:
        """Pobiera wszystkie kluczowe wskaźniki"""
        print(f"[INFO] Pobieram dane wskaznikow plynnosci (ostatnie {days_back} dni)...")

        indicators = {}

        for name, series_id in self.series.items():
            print(f"   Pobieram {name}...")
            data = self.fetch_fred_data(series_id, days_back=days_back)
            
            if not data.empty:
                latest = data.iloc[-1]
                if len(data) > 1:
                    previous = data.iloc[-2]
                    week_ago = data[data['date'] <= latest['date'] - timedelta(days=7)]
                    week_ago_value = week_ago.iloc[-1]['value'] if not week_ago.empty else latest['value']
                else:
                    previous = latest
                    week_ago_value = latest['value']
                
                indicators[name] = {
                    'current': latest['value'],
                    'date': latest['date'].strftime('%Y-%m-%d'),
                    'change_1d': latest['value'] - previous['value'],
                    'change_7d': latest['value'] - week_ago_value,
                    'data': data,
                    'history': data['value'],  # Dla obliczania percentyli
                }
        
        return indicators
    
    def analyze_liquidity_conditions(self, indicators: Dict) -> Dict:
        """
        Analizuje warunki płynności i generuje ocenę
        
        Returns:
            Dict z oceną warunków i alertami
        """
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': 0,  # -100 do +100
            'signals': [],
            'alerts': [],
            'interpretation': '',
            'market_regime': {},
            'weighted_scores': {},  # Punkty z wagami dla każdego wskaźnika
        }

        score = 0

        # === WYKRYJ REŻIM RYNKOWY ===
        regime = self.detect_market_regime(indicators)
        analysis['market_regime'] = regime

        print(f"[REGIME] {regime['name']} (mnożnik: {regime['multiplier']}x)")
        for trigger in regime['triggers']:
            print(f"  - {trigger}")

        # === OBLICZ PERCENTYLE HISTORYCZNE ===
        percentiles = self.calculate_percentiles(indicators)
        analysis['percentiles'] = percentiles

        # === WYKRYJ KORELACJE I KONFLIKTY ===
        patterns = self.detect_correlations_and_conflicts(indicators)
        analysis['patterns'] = patterns

        # Dodaj wykryte wzorce do sygnałów
        for conflict in patterns['conflicts']:
            analysis['alerts'].append({
                'severity': conflict['severity'],
                'indicator': 'Korelacje',
                'message': f"[{conflict['type'].upper()}] {conflict['name']}: {conflict['interpretation']}"
            })

        for reinforcement in patterns['reinforcements']:
            signal_type = 'positive' if reinforcement['score_impact'] > 0 else 'negative'
            analysis['signals'].append({
                'type': signal_type,
                'indicator': 'Wzmocnienia',
                'message': f"{reinforcement['name']}: {reinforcement['interpretation']}"
            })

        for compound in patterns['compound_signals']:
            signal_type = 'positive' if compound['score_impact'] > 0 else 'negative'
            analysis['signals'].append({
                'type': signal_type,
                'indicator': 'Compound Signals',
                'message': f"{compound['name']}: {compound['interpretation']}"
            })

        # === SCORING Z WAGAMI ===
        # Każdy wskaźnik dostaje punkty -100 do +100, potem mnożone przez wagę
        weighted_score = 0

        # 1. Analiza rezerw banków
        if 'reserves' in indicators:
            reserves = indicators['reserves']['current']
            reserves_change = indicators['reserves']['change_7d']
            
            if reserves > self.thresholds['reserves_comfortable']:
                score += 30
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Rezerwy banków',
                    'message': f'Wysokie rezerwy: ${reserves:.0f}B - system luźny',
                })
            elif reserves < self.thresholds['reserves_minimum']:
                score -= 40
                analysis['alerts'].append({
                    'severity': 'critical',
                    'indicator': 'Rezerwy bankow',
                    'message': f'[CRITICAL] REZERWY NISKIE: ${reserves:.0f}B - ryzyko napiec',
                })
            
            if reserves_change < -50:  # spadek > 50B w tydzień
                score -= 20
                analysis['alerts'].append({
                    'severity': 'warning',
                    'indicator': 'Rezerwy banków',
                    'message': f'Szybki spadek rezerw: {reserves_change:.0f}B/tydzień',
                })
        
        # 2. Analiza TGA
        if 'tga' in indicators:
            tga = indicators['tga']['current']
            tga_change = indicators['tga']['change_7d']
            
            if tga_change > 50:  # wzrost > 50B
                score -= 15
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'TGA',
                    'message': f'TGA rośnie (+${tga_change:.0f}B) - drenuje płynność',
                })
            elif tga_change < -50:  # spadek > 50B
                score += 15
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'TGA',
                    'message': f'TGA spada ({tga_change:.0f}B) - dodaje płynność',
                })
        
        # 3. Analiza SOFR vs IORB
        if 'sofr' in indicators and 'iorb' in indicators:
            sofr = indicators['sofr']['current']
            iorb = indicators['iorb']['current']
            spread = sofr - iorb
            
            if spread > self.thresholds['sofr_iorb_spread_critical']:
                score -= 30
                analysis['alerts'].append({
                    'severity': 'critical',
                    'indicator': 'SOFR spread',
                    'message': f'[CRITICAL] SOFR-IORB spread: {spread:.2f}% - NAPIECIE!',
                })
            elif spread > self.thresholds['sofr_iorb_spread_warning']:
                score -= 15
                analysis['alerts'].append({
                    'severity': 'warning',
                    'indicator': 'SOFR spread',
                    'message': f'[WARN] SOFR-IORB spread: {spread:.2f}% - rosna koszty',
                })
            else:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'SOFR spread',
                    'message': f'SOFR stabilny (spread: {spread:.2f}%)',
                })
        
        # 4. Analiza Reverse Repo
        if 'reverse_repo' in indicators:
            rrp = indicators['reverse_repo']['current']
            rrp_change = indicators['reverse_repo']['change_7d']
            
            if rrp < 100:  # poniżej 100B
                score -= 10
                analysis['signals'].append({
                    'type': 'neutral',
                    'indicator': 'Reverse Repo',
                    'message': f'RRP bardzo niskie: ${rrp:.0f}B - brak bufora',
                })
            elif rrp > 500:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Reverse Repo',
                    'message': f'RRP wysoki: ${rrp:.0f}B - jest bufor płynności',
                })
        
        # 5. Analiza bilansu Fed
        if 'fed_balance' in indicators:
            balance_change = indicators['fed_balance']['change_7d']
            
            if balance_change < -20:  # QT > 20B/tydzień
                score -= 10
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'Bilans Fed',
                    'message': f'QT aktywne: {balance_change:.0f}B/tydzień',
                })
            elif balance_change > 20:  # ekspansja
                score += 15
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Bilans Fed',
                    'message': f'Fed zwieksza bilans: +{balance_change:.0f}B/tydzien',
                })

        # === TIER 1 - Nowe wskazniki ===

        # 6. Analiza krzywej dochodowosci (10Y-2Y)
        if 'yield_curve' in indicators:
            curve = indicators['yield_curve']['current']

            if curve < self.thresholds['yield_curve_inverted']:
                score -= 30
                analysis['alerts'].append({
                    'severity': 'critical',
                    'indicator': 'Krzywa dochodowosci',
                    'message': f'[CRITICAL] KRZYWA ODWROCONA: {curve:.2f}% - Ryzyko recesji!',
                })
            elif curve < 0.25:
                score -= 15
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'Krzywa dochodowosci',
                    'message': f'Krzywa plaska: {curve:.2f}% - Spowolnienie wzrostu',
                })
            elif curve > self.thresholds['yield_curve_steep']:
                score += 15
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Krzywa dochodowosci',
                    'message': f'Krzywa stroma: {curve:.2f}% - Ekspansja gospodarcza',
                })

        # 7. Analiza VIX (strach na rynku)
        if 'vix' in indicators:
            vix = indicators['vix']['current']
            vix_change = indicators['vix']['change_7d']

            if vix > self.thresholds['vix_fear']:
                score -= 25
                analysis['alerts'].append({
                    'severity': 'warning',
                    'indicator': 'VIX',
                    'message': f'[WARN] VIX wysoki: {vix:.1f} - Panika na rynku!',
                })
            elif vix < self.thresholds['vix_greed']:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'VIX',
                    'message': f'VIX niski: {vix:.1f} - Spokoj na rynku',
                })

            if vix_change > 5:  # VIX wzrósł > 5 punktów
                score -= 10
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'VIX',
                    'message': f'VIX gwaltownie rosnie: +{vix_change:.1f}',
                })

        # 8. Analiza warunkow finansowych (NFCI)
        if 'fin_conditions' in indicators:
            nfci = indicators['fin_conditions']['current']

            if nfci > self.thresholds['nfci_tight']:
                score -= 20
                analysis['alerts'].append({
                    'severity': 'warning',
                    'indicator': 'Warunki finansowe',
                    'message': f'[WARN] NFCI dodatni: {nfci:.2f} - Napięcia finansowe',
                })
            elif nfci < self.thresholds['nfci_loose']:
                score += 20
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Warunki finansowe',
                    'message': f'NFCI bardzo ujemny: {nfci:.2f} - Luźne warunki',
                })

        # 9. Analiza indeksu dolara (DXY)
        if 'dollar_index' in indicators:
            dxy = indicators['dollar_index']['current']
            dxy_change = indicators['dollar_index']['change_7d']

            if dxy > self.thresholds['dollar_strong']:
                score -= 10
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'Dollar Index',
                    'message': f'DXY bardzo wysoki: {dxy:.1f} - Silny dolar zabiera plynnosc',
                })
            elif dxy < self.thresholds['dollar_weak']:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Dollar Index',
                    'message': f'DXY niski: {dxy:.1f} - Slaby dolar dodaje plynnosc',
                })

            if dxy_change > 2:  # DXY wzrósł > 2 punkty
                score -= 5
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'Dollar Index',
                    'message': f'DXY gwaltownie rosnie: +{dxy_change:.1f}',
                })

        # 10. Analiza M2 (podaz pieniadza)
        if 'm2' in indicators:
            m2_change = indicators['m2']['change_7d']

            if m2_change < -100:  # M2 spada > 100B
                score -= 10
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'M2 Money Supply',
                    'message': f'M2 spada: {m2_change:.0f}B - Kurczy sie podaz pieniadza',
                })
            elif m2_change > 100:  # M2 rośnie > 100B
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'M2 Money Supply',
                    'message': f'M2 rosnie: +{m2_change:.0f}B - Wzrost podazy pieniadza',
                })

        # === TIER 2 - Nowe wskazniki ===

        # 11. Analiza 10-Year Treasury
        if 'treasury_10y' in indicators:
            t10y = indicators['treasury_10y']['current']

            if t10y > self.thresholds['treasury_10y_high']:
                score -= 15
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': '10Y Treasury',
                    'message': f'10Y wysoko: {t10y:.2f}% - Wysokie koszty dlugu',
                })
            elif t10y < self.thresholds['treasury_10y_low']:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': '10Y Treasury',
                    'message': f'10Y nisko: {t10y:.2f}% - Tanie finansowanie',
                })

        # 12. Analiza High Yield Spread
        if 'hy_spread' in indicators:
            hy = indicators['hy_spread']['current']

            if hy > self.thresholds['hy_spread_high']:
                score -= 20
                analysis['alerts'].append({
                    'severity': 'warning',
                    'indicator': 'High Yield Spread',
                    'message': f'[WARN] HY Spread wysoki: {hy:.2f}% - Strach o kredyt!',
                })
            elif hy < 3.0:
                score += 5
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'High Yield Spread',
                    'message': f'HY Spread niski: {hy:.2f}% - Dobry apetyt na ryzyko',
                })

        # 13. Analiza 5Y Breakeven Inflation
        if 'inflation_5y' in indicators:
            infl = indicators['inflation_5y']['current']

            if infl > self.thresholds['inflation_high']:
                score -= 10
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': '5Y Inflation',
                    'message': f'Oczekiwana inflacja wysoka: {infl:.2f}%',
                })
            elif infl < self.thresholds['inflation_low']:
                score -= 5
                analysis['signals'].append({
                    'type': 'neutral',
                    'indicator': '5Y Inflation',
                    'message': f'Oczekiwana inflacja niska: {infl:.2f}% - Ryzyko deflacji?',
                })

        # 14. Analiza bezrobocia
        if 'unemployment' in indicators:
            unemp = indicators['unemployment']['current']

            if unemp > self.thresholds['unemployment_high']:
                score -= 15
                analysis['signals'].append({
                    'type': 'negative',
                    'indicator': 'Unemployment',
                    'message': f'Bezrobocie wysokie: {unemp:.1f}% - Slaby rynek pracy',
                })
            elif unemp < self.thresholds['unemployment_low']:
                score += 10
                analysis['signals'].append({
                    'type': 'positive',
                    'indicator': 'Unemployment',
                    'message': f'Bezrobocie niskie: {unemp:.1f}% - Mocny rynek pracy',
                })

        # === DODAJ KOREKTY Z KORELACJI ===
        # Najpierw dodajemy punkty z wykrytych wzorców
        correlation_adjustment = patterns['score_adjustments']
        score += correlation_adjustment

        print(f"[CORRELATIONS IMPACT] Score adjustment: {correlation_adjustment:+.0f} (Total przed reżimem: {score:.0f})")

        # === ZASTOSUJ MULTIPLIKATOR REŻIMU ===
        # Sygnały negatywne liczą się mocniej w RISK-OFF i KRYZYS
        regime_multiplier = regime['multiplier']

        # Asymetryczne zastosowanie: tylko negatywne sygnały wzmacniamy
        if score < 0:
            adjusted_score = score * regime_multiplier
        else:
            adjusted_score = score  # Pozytywne bez zmiany

        analysis['overall_score'] = max(-100, min(100, adjusted_score))
        analysis['raw_score'] = score  # Dla debugowania
        analysis['regime_adjustment'] = adjusted_score - score

        print(f"[SCORING] Raw: {score:.1f} | Adjusted: {adjusted_score:.1f} | Final: {analysis['overall_score']:.1f}")

        # === INTERPRETACJA (uwzględnia reżim) ===
        regime_prefix = f"[{regime['regime']}] "

        if analysis['overall_score'] > 40:
            analysis['interpretation'] = regime_prefix + 'Warunki plynnosci sprzyjaja wzrostom (Nasdaq/BTC)'
        elif analysis['overall_score'] > 0:
            analysis['interpretation'] = regime_prefix + 'Warunki plynnosci umiarkowane'
        elif analysis['overall_score'] > -40:
            analysis['interpretation'] = regime_prefix + 'Pogarszajace sie warunki plynnosci'
        else:
            analysis['interpretation'] = regime_prefix + 'Napiecia w plynnosci - ostroznosc!'

        # Dodaj opis reżimu
        analysis['interpretation'] += f"\n{regime['description']}"

        return analysis
    
    def print_report(self, indicators: Dict, analysis: Dict):
        """Wyświetla raport w terminalu"""
        print("\n" + "="*80)
        print("[RAPORT] WSKAZNIKI PLYNNOSCI")
        print("="*80)
        print(f"Czas: {analysis['timestamp']}")
        print(f"\n{analysis['interpretation']}")
        print(f"Ocena ogólna: {analysis['overall_score']}/100")
        
        print("\n" + "-"*80)
        print("KLUCZOWE WSKAŹNIKI:")
        print("-"*80)
        
        for name, data in indicators.items():
            label = {
                'reserves': 'Rezerwy banków',
                'tga': 'TGA (konto rządu)',
                'reverse_repo': 'Reverse Repo',
                'fed_balance': 'Bilans Fed',
                'sofr': 'SOFR',
                'iorb': 'IORB',
                'effr': 'EFFR',
            }.get(name, name)
            
            unit = '%' if name in ['sofr', 'iorb', 'effr'] else 'B USD'
            value = data['current']
            change_7d = data['change_7d']
            change_symbol = '▲' if change_7d > 0 else '▼' if change_7d < 0 else '='
            
            print(f"{label:25} {value:10.2f} {unit:6} | 7d: {change_symbol} {change_7d:+8.2f}")
        
        if 'sofr' in indicators and 'iorb' in indicators:
            spread = indicators['sofr']['current'] - indicators['iorb']['current']
            print(f"{'SOFR-IORB spread':25} {spread:10.2f} {'%':6} |")
        
        # Alerty
        if analysis['alerts']:
            print("\n" + "-"*80)
            print("[ALERTY]:")
            print("-"*80)
            for alert in analysis['alerts']:
                print(f"  • [{alert['severity'].upper()}] {alert['message']}")
        
        # Sygnały
        if analysis['signals']:
            print("\n" + "-"*80)
            print("[SYGNALY]:")
            print("-"*80)
            for signal in analysis['signals']:
                prefix = {'positive': '[+]', 'negative': '[-]', 'neutral': '[=]'}.get(signal['type'], '[?]')
                print(f"  {prefix} {signal['message']}")
        
        print("\n" + "="*80 + "\n")
    
    def save_to_json(self, indicators: Dict, analysis: Dict, filename: str = 'liquidity_data.json'):
        """Zapisuje dane do pliku JSON"""
        output = {
            'timestamp': analysis['timestamp'],
            'analysis': {
                'score': analysis['overall_score'],
                'interpretation': analysis['interpretation'],
                'alerts': analysis['alerts'],
                'signals': analysis['signals'],
            },
            'indicators': {
                name: {
                    'current': data['current'],
                    'date': data['date'],
                    'change_1d': data['change_1d'],
                    'change_7d': data['change_7d'],
                }
                for name, data in indicators.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"[SAVED] Dane zapisane do: {filename}")


def main():
    """Główna funkcja uruchamiająca monitor"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      LIQUIDITY MONITOR - System startuje                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Sprawdź czy jest klucz API
    import os
    api_key = os.environ.get('FRED_API_KEY')
    
    if not api_key:
        print("[WARN] UWAGA: Nie znaleziono klucza FRED_API_KEY")
        print("   Aby uzyskac pelne dane, zarejestruj sie na:")
        print("   https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   Nastepnie ustaw zmienna srodowiskowa:")
        print("   export FRED_API_KEY='twoj_klucz'\n")
        response = input("   Kontynuowac bez klucza (dane demo)? [t/N]: ")
        if response.lower() != 't':
            return
    
    monitor = LiquidityMonitor(fred_api_key=api_key)
    
    # Pobierz wskaźniki
    indicators = monitor.get_all_indicators()
    
    if not indicators:
        print("\n[ERROR] Nie udalo sie pobrac zadnych danych.")
        print("   Sprawdz klucz API i polaczenie internetowe.")
        return
    
    # Analizuj warunki
    analysis = monitor.analyze_liquidity_conditions(indicators)
    
    # Wyświetl raport
    monitor.print_report(indicators, analysis)
    
    # Zapisz do JSON
    monitor.save_to_json(indicators, analysis)


if __name__ == "__main__":
    main()
