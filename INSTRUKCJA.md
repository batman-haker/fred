# 📊 Liquidity Monitor Pro - Dokumentacja Techniczna

## 📋 Spis Treści
1. [Przegląd Projektu](#przegląd-projektu)
2. [Instalacja i Konfiguracja](#instalacja-i-konfiguracja)
3. [Architektura Systemu](#architektura-systemu)
4. [Algorytm Analizy - 3 Kroki](#algorytm-analizy)
5. [Wskaźniki (18 Total)](#wskaźniki)
6. [Funkcje Kluczowe](#funkcje-kluczowe)
7. [Interfejs Użytkownika](#interfejs-użytkownika)
8. [Jak Rozbudować](#jak-rozbudować)
9. [Troubleshooting](#troubleshooting)

---

## 📖 Przegląd Projektu

**Liquidity Monitor Pro** to zaawansowana aplikacja webowa do monitorowania płynności rynku amerykańskiego w czasie rzeczywistym.

### 🎯 Cel
Analiza kondycji finansowej rynku USA poprzez monitoring 18 kluczowych wskaźników z FRED (Federal Reserve Economic Data), wykorzystując zaawansowany algorytm scoringowy z:
- Systemem wag wskaźników
- Wykrywaniem reżimów rynkowych (RISK_ON, RISK_OFF, CRISIS)
- Detekcją korelacji i konfliktów między wskaźnikami
- Kontekstem historycznym (percentyle)

### 🛠️ Technologie
- **Backend**: Python 3.x
- **Frontend**: Streamlit
- **API**: FRED (Federal Reserve Economic Data)
- **Analiza**: Pandas, NumPy
- **Wizualizacja**: Plotly

### 📁 Struktura Plików
```
C:\FRED\
├── app.py                      # Główna aplikacja Streamlit (UI)
├── liquidity_monitor.py        # Logika biznesowa (algorytm)
├── requirements.txt            # Zależności Python
├── .env                        # Klucz API (NIE commituj do git!)
├── test_percentiles.py         # Testy percentyli
├── discover_indicators.py      # Skrypt do testowania nowych wskaźników
└── INSTRUKCJA.md              # Ta dokumentacja
```

---

## ⚙️ Instalacja i Konfiguracja

### 1️⃣ Wymagania Wstępne
- Python 3.8 lub nowszy
- Połączenie z internetem
- Klucz API FRED (darmowy)

### 2️⃣ Instalacja Zależności
```bash
cd C:\FRED
pip install -r requirements.txt
```

**requirements.txt zawiera:**
```
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
streamlit>=1.28.0
plotly>=5.17.0
python-dotenv>=1.0.0
```

### 3️⃣ Konfiguracja Klucza API

**Jak uzyskać klucz FRED:**
1. Zarejestruj się: https://fred.stlouisfed.org/
2. Uzyskaj klucz: https://fred.stlouisfed.org/docs/api/api_key.html
3. Klucz będzie wysłany na email

**Konfiguracja:**
Stwórz plik `.env` w głównym katalogu:
```
FRED_API_KEY=twoj_klucz_tutaj
```

⚠️ **WAŻNE:** NIE commituj pliku `.env` do git! Dodaj go do `.gitignore`.

### 4️⃣ Uruchomienie Aplikacji
```bash
py -m streamlit run app.py
```

Aplikacja otworzy się w przeglądarce na: `http://localhost:8501`

---

## 🏗️ Architektura Systemu

### Podział Odpowiedzialności

#### `liquidity_monitor.py` - Backend
**Rola:** Logika biznesowa, pobieranie danych, algorytm scoringowy

**Kluczowe metody:**
- `get_all_indicators()` - Pobiera wszystkie 18 wskaźników z FRED
- `analyze_liquidity_conditions()` - Główna metoda analizy
- `detect_market_regime()` - Wykrywa reżim rynkowy
- `detect_correlations_and_conflicts()` - Wykrywa wzorce
- `calculate_percentiles()` - Oblicza kontekst historyczny

#### `app.py` - Frontend
**Rola:** Interfejs użytkownika, wizualizacja, prezentacja danych

**Sekcje UI:**
- Executive Summary (rekomendacja CO ROBIĆ?)
- Quick Stats (4 kluczowe metryki)
- Szczegółowa Analiza (wszystkie wskaźniki)
- Reżim Rynkowy (z wyjaśnieniami)
- Wzorce i Korelacje (8 pattern types)
- Percentyle Historyczne (kontekst)
- Dane Szczegółowe (tabele)
- Wykresy Historyczne (Plotly)
- Słownik Pojęć (edukacja)

---

## 🧠 Algorytm Analizy - 3 Kroki

### KROK 1: System Wag + Reżimy Rynkowe

#### System Wag Wskaźników
**Lokalizacja:** `liquidity_monitor.py:86-109`

Każdy wskaźnik ma wagę określającą jego wpływ na końcowy score:

```python
self.indicator_weights = {
    # === KRYTYCZNE (40%) ===
    'reserves': 0.15,           # Rezerwy bankowe - fundament płynności
    'yield_curve': 0.15,        # Krzywa dochodowości - sygnał recesji
    'sofr_spread': 0.10,        # SOFR vs Fed Funds - stres bankowy

    # === WAŻNE (30%) ===
    'vix': 0.10,                # VIX - strach na rynku
    'nfci': 0.10,               # NFCI - warunki finansowe
    'hy_spread': 0.10,          # High Yield Spread - ryzyko kredytowe

    # === POMOCNICZE (30%) ===
    'tga': 0.08,                # Treasury General Account
    'reverse_repo': 0.07,       # Overnight RRP
    'ted_spread': 0.05,         # TED Spread - napięcie LIBOR
    'dollar_index': 0.05,       # Indeks dolara
    'mortgage_spread': 0.05,    # Spread hipoteczny
    'financial_stress': 0.05,   # St. Louis Fed Stress Index
    'commercial_paper': 0.03,   # Papiery komercyjne
    'credit_conditions': 0.03,  # Warunki kredytowe
    'fed_balance_sheet': 0.02,  # Bilans Fed
    'm2_money_supply': 0.02,    # Podaż pieniądza M2
    'inflation_expectations': 0.02,  # Oczekiwania inflacyjne
    'unemployment': 0.02        # Bezrobocie
}
```

**Dlaczego różne wagi?**
- Rezerwy bankowe (15%) - bezpośredni miernik płynności systemu
- Yield curve (15%) - historycznie najlepszy predyktor recesji
- VIX (10%) - natychmiastowa reakcja rynku na stres
- Bezrobocie (2%) - opóźniony wskaźnik, mniej przydatny w short-term trading

#### Reżimy Rynkowe
**Lokalizacja:** `liquidity_monitor.py:111-145`

System wykrywa 3 reżimy:

```python
self.market_regimes = {
    'RISK_ON': {
        'multiplier': 1.0,      # Brak modyfikacji
        'conditions': {
            'vix': '<20',       # VIX spokojny
            'nfci': '<0',       # Warunki finansowe luźne
            'hy_spread': '<5',  # Niskie ryzyko kredytowe
            'yield_curve': '>0' # Normalna krzywa
        }
    },
    'RISK_OFF': {
        'multiplier': 1.3,      # Wzmocnienie negatywnych sygnałów o 30%
        'conditions': {
            'vix': '20-30',
            'nfci': '0-0.5',
            'hy_spread': '5-7'
        }
    },
    'CRISIS': {
        'multiplier': 1.8,      # Wzmocnienie negatywnych sygnałów o 80%
        'conditions': {
            'vix': '>30',       # VIX powyżej 30 = panika
            'nfci': '>0.5',     # Napięte warunki
            'hy_spread': '>7'   # Wysokie ryzyko
        }
    }
}
```

**Asymetryczne Zastosowanie Multiplikatora:**
```python
if score < 0:
    adjusted_score = score * regime_multiplier  # TYLKO negatywne wzmacniamy
else:
    adjusted_score = score  # Pozytywne bez zmian
```

**Dlaczego asymetrycznie?**
- W kryzysie (CRISIS) negatywne sygnały są bardziej wiarygodne
- Pozytywne sygnały w kryzysie mogą być "dead cat bounce"
- Chroni przed false positive w bull trapach

#### Metoda: `detect_market_regime()`
**Lokalizacja:** `liquidity_monitor.py:147-239`

```python
def detect_market_regime(self, indicators: Dict) -> Dict:
    """Wykrywa obecny reżim rynkowy"""

    # Priorytet: CRISIS > RISK_OFF > RISK_ON

    # 1. Sprawdź CRISIS (najwyższy priorytet)
    crisis_triggers = []
    if vix >= 30:
        crisis_triggers.append('VIX ekstremalne')
    if nfci >= 0.5:
        crisis_triggers.append('NFCI napięte')
    if hy_spread >= 7:
        crisis_triggers.append('HY Spread wysokie')

    # Wystarczy 1 trigger dla CRISIS
    if len(crisis_triggers) >= 1:
        return {
            'regime': 'CRISIS',
            'multiplier': 1.8,
            'triggers': crisis_triggers
        }

    # 2. Sprawdź RISK_OFF
    # ... podobna logika ...

    # 3. Default: RISK_ON
    return {
        'regime': 'RISK_ON',
        'multiplier': 1.0,
        'triggers': []
    }
```

---

### KROK 2: Korelacje i Konflikty

**Lokalizacja:** `liquidity_monitor.py:323-423`

System wykrywa 8 typów wzorców w relacjach między wskaźnikami.

#### Metoda: `detect_correlations_and_conflicts()`

```python
def detect_correlations_and_conflicts(self, indicators: Dict) -> Dict:
    """Wykrywa korelacje, konflikty i compound signals"""

    patterns = {
        'conflicts': [],           # Sprzeczności
        'reinforcements': [],      # Wzmocnienia
        'compound_signals': [],    # Złożone sygnały
        'score_adjustments': 0     # Modyfikacja score
    }

    # === KONFLIKTY (paradoksy) ===

    # 1. "Panika mimo płynności"
    if vix > 25 and reserves > 3200:
        patterns['conflicts'].append({
            'type': 'paradox',
            'name': 'PARADOKS: Panika mimo wysokiej płynności',
            'details': 'VIX wysoki ale rezerwy wysokie',
            'score_impact': +10  # POZYTYWNE - strach przesadzony
        })
        patterns['score_adjustments'] += 10

    # 2. "Fałszywy spokój"
    if vix < 15 and (ted_spread > 0.5 or hy_spread > 6):
        patterns['conflicts'].append({
            'type': 'false_calm',
            'name': 'FALSE CALM: VIX spokojny ale spread wysokie',
            'score_impact': -15  # NEGATYWNE - ukryty stres
        })
        patterns['score_adjustments'] -= 15

    # 3. "Fed walczy z recesją"
    if yield_curve < -0.3 and reserves_increasing:
        patterns['conflicts'].append({
            'type': 'fed_fighting',
            'name': 'Fed walczy z odwróconą krzywą',
            'score_impact': +5
        })
        patterns['score_adjustments'] += 5

    # === WZMOCNIENIA (reinforcements) ===

    # 4. "Perfect Risk-On"
    if vix < 15 and nfci < -0.3 and hy_spread < 4:
        patterns['reinforcements'].append({
            'type': 'perfect_risk_on',
            'name': 'PERFECT RISK-ON: Wszystko zielone',
            'score_impact': +20
        })
        patterns['score_adjustments'] += 20

    # 5. "Triple Threat"
    if vix > 30 and nfci > 0.5 and hy_spread > 7:
        patterns['reinforcements'].append({
            'type': 'triple_threat',
            'name': 'TRIPLE THREAT: VIX + NFCI + HY wszstko złe',
            'score_impact': -25
        })
        patterns['score_adjustments'] -= 25

    # === COMPOUND SIGNALS (złożone) ===

    # 6. "Liquidity Flood"
    if reserves_increasing and rrp_decreasing and tga_decreasing:
        patterns['compound_signals'].append({
            'type': 'liquidity_flood',
            'name': 'LIQUIDITY FLOOD: Pieniądze zalewają system',
            'score_impact': +15
        })
        patterns['score_adjustments'] += 15

    # 7. "Liquidity Drain"
    if reserves_decreasing and rrp_increasing and tga_increasing:
        patterns['compound_signals'].append({
            'type': 'liquidity_drain',
            'name': 'LIQUIDITY DRAIN: Pieniądze wysysane',
            'score_impact': -15
        })
        patterns['score_adjustments'] -= 15

    # 8. "Credit Crunch"
    if ted_spread > 0.5 and hy_spread > 6 and nfci > 0.3:
        patterns['compound_signals'].append({
            'type': 'credit_crunch',
            'name': 'CREDIT CRUNCH: Zaciśnięcie kredytu',
            'score_impact': -20
        })
        patterns['score_adjustments'] -= 20

    return patterns
```

**Przykład działania:**
- VIX = 28 (panika)
- Reserves = 3500B (bardzo wysokie)
- → System wykrywa "Panika mimo płynności"
- → Score +10 (strach jest przesadzony, potencjalna okazja)

---

### KROK 3: Percentyle Historyczne

**Lokalizacja:** `liquidity_monitor.py:241-289`

Zamiast stałych progów ("VIX > 30 = źle"), używamy kontekstu historycznego.

#### Metoda: `calculate_percentiles()`

```python
def calculate_percentiles(self, indicators: Dict) -> Dict:
    """Oblicza percentyle historyczne dla każdego wskaźnika"""

    percentiles = {}

    for indicator_name, data in indicators.items():
        if 'history' not in data or len(data['history']) < 10:
            continue  # Za mało danych

        history_values = [float(val) for val in data['history'].values
                          if val != '.']
        current = data['current']

        # Oblicz percentyl
        below = sum(1 for v in history_values if v < current)
        percentile_rank = (below / len(history_values)) * 100

        percentiles[indicator_name] = {
            'current': current,
            'percentile': percentile_rank,
            'historical_min': min(history_values),
            'historical_max': max(history_values),
            'historical_mean': np.mean(history_values),
            'interpretation': self._interpret_percentile(
                percentile_rank,
                indicator_name
            )
        }

    return percentiles
```

#### Interpretacja Percentyli

```python
def _interpret_percentile(self, percentile: float, indicator_name: str) -> str:
    """Interpretuje co percentyl oznacza"""

    # Dla większości wskaźników: wyższy = gorszy
    inverted_indicators = ['reserves', 'yield_curve', 'm2_money_supply']

    if indicator_name in inverted_indicators:
        # Odwrócona logika (więcej = lepiej)
        if percentile > 90:
            return "Ekstremalnie wysokie (pozytywne)"
        elif percentile > 75:
            return "Wysoko (dobre)"
        elif percentile > 25:
            return "Normalnie"
        elif percentile > 10:
            return "Nisko (uwaga)"
        else:
            return "Ekstremalnie niskie (negatywne)"
    else:
        # Normalna logika (więcej = gorzej)
        if percentile > 90:
            return "Ekstremalnie wysokie (negatywne)"
        elif percentile > 75:
            return "Wysoko (uwaga)"
        elif percentile > 25:
            return "Normalnie"
        elif percentile > 10:
            return "Nisko (pozytywne)"
        else:
            return "Ekstremalnie niskie (bardzo pozytywne)"
```

**Przykład:**
- **2020 COVID:** VIX = 30, percentyl = 60% (w czasie kryzysu to norma)
- **2017 Spokój:** VIX = 30, percentyl = 99% (ekstremalna panika!)
- **Ta sama wartość, zupełnie inny kontekst!**

---

## 📊 Wskaźniki (18 Total)

### Kategorie Wskaźników

#### 🔴 Tier 0: Podstawowe (8)
| Wskaźnik | Seria FRED | Waga | Co mierzy |
|----------|-----------|------|-----------|
| **Rezerwy Bankowe** | TOTRESNS | 15% | Płynność w systemie bankowym |
| **Krzywa Dochodowości** | T10Y2Y | 15% | Różnica 10Y-2Y Treasury (recesja gdy <0) |
| **VIX** | VIXCLS | 10% | Indeks strachu na rynku |
| **NFCI** | NFCI | 10% | Warunki finansowe (Chicago Fed) |
| **TGA** | WTREGEN | 8% | Konto Treasury (gdy rośnie = wysysa płynność) |
| **Reverse Repo** | RRPONTSYD | 7% | Overnight RRP (gotówka parkowana w Fed) |
| **High Yield Spread** | BAMLH0A0HYM2 | 10% | Spread obligacji HY (ryzyko kredytowe) |
| **SOFR Spread** | SOFR minus EFFR | 10% | SOFR vs Fed Funds (stres w repo) |

#### 🟡 Tier 1: Rozszerzone (5)
| Wskaźnik | Seria FRED | Waga | Co mierzy |
|----------|-----------|------|-----------|
| **TED Spread** | TEDRATE | 5% | LIBOR minus Treasury (stres bankowy) |
| **Indeks Dolara** | DTWEXBGS | 5% | Siła dolara (globalny risk appetite) |
| **Mortgage Spread** | MORTGAGE30US minus DGS10 | 5% | Spread hipoteczny (koszt kredytu) |
| **Financial Stress Index** | STLFSI4 | 5% | St. Louis Fed Stress Index |
| **Commercial Paper** | CPFF | 3% | Papiery komercyjne (short-term funding) |

#### 🟢 Tier 2: Zaawansowane (5)
| Wskaźnik | Seria FRED | Waga | Co mierzy |
|----------|-----------|------|-----------|
| **Credit Conditions** | DRTSCILM | 3% | Warunki kredytowe (Senior Loan Survey) |
| **Fed Balance Sheet** | WALCL | 2% | Bilans Fedu (QE/QT) |
| **M2 Money Supply** | M2SL | 2% | Podaż pieniądza M2 |
| **Inflation Expectations** | T5YIE | 2% | Oczekiwania inflacyjne 5Y |
| **Unemployment** | UNRATE | 2% | Stopa bezrobocia |

### Scoring Każdego Wskaźnika

**Lokalizacja:** `liquidity_monitor.py:425-602`

Każdy wskaźnik ma swoją funkcję scoringową:

```python
# Przykład: Rezerwy Bankowe
def _score_reserves(self, value: float) -> float:
    """
    Rezerwy > 3200B = bardzo dobre (+15)
    Rezerwy < 2500B = źle (-15)
    """
    if value > 3200:
        return 15
    elif value > 3000:
        return 10
    elif value > 2800:
        return 5
    elif value > 2500:
        return -5
    else:
        return -15

# Przykład: VIX
def _score_vix(self, value: float) -> float:
    """
    VIX < 15 = spokój (+10)
    VIX > 35 = panika (-15)
    """
    if value < 12:
        return 10
    elif value < 15:
        return 5
    elif value < 20:
        return 0
    elif value < 25:
        return -5
    elif value < 30:
        return -10
    else:
        return -15
```

---

## 🔧 Funkcje Kluczowe

### 1. `get_all_indicators(days_back=90)`
**Plik:** `liquidity_monitor.py:291-321`

**Co robi:**
- Pobiera wszystkie 18 wskaźników z FRED API
- Oblicza zmiany 1-day i 7-day
- Zwraca dict z danymi i historią

**Przykład użycia:**
```python
from liquidity_monitor import LiquidityMonitor

monitor = LiquidityMonitor(fred_api_key='twoj_klucz')
indicators = monitor.get_all_indicators(days_back=365)

print(indicators['vix'])
# Output:
# {
#     'current': 18.5,
#     'date': '2024-01-15',
#     'change_1d': -0.3,
#     'change_7d': 2.1,
#     'data': <DataFrame>,
#     'history': <Series>  # Dla percentyli
# }
```

---

### 2. `analyze_liquidity_conditions()`
**Plik:** `liquidity_monitor.py:604-960`

**Co robi:**
Główna metoda łącząca wszystkie 3 kroki algorytmu.

**Pipeline:**
```python
def analyze_liquidity_conditions(self, indicators: Dict) -> Dict:
    """Główna analiza - KROK 1+2+3"""

    # === KROK 1a: Scoring poszczególnych wskaźników ===
    scores = {}
    for name, data in indicators.items():
        score_func = getattr(self, f'_score_{name}')
        scores[name] = score_func(data['current']) * self.indicator_weights[name]

    raw_score = sum(scores.values())

    # === KROK 1b: Wykryj reżim rynkowy ===
    regime = self.detect_market_regime(indicators)

    # === KROK 2: Wykryj korelacje i konflikty ===
    patterns = self.detect_correlations_and_conflicts(indicators)
    correlation_adjustment = patterns['score_adjustments']

    # === KROK 3: Oblicz percentyle ===
    percentiles = self.calculate_percentiles(indicators)

    # === Zastosuj korekty ===
    score_with_patterns = raw_score + correlation_adjustment

    # Asymetryczne zastosowanie multiplikatora reżimu
    if score_with_patterns < 0:
        final_score = score_with_patterns * regime['multiplier']
    else:
        final_score = score_with_patterns

    # Ogranicz do [-100, 100]
    final_score = max(-100, min(100, final_score))

    # === Zwróć kompletną analizę ===
    return {
        'overall_score': final_score,
        'raw_score': raw_score,
        'regime_adjustment': final_score - score_with_patterns,
        'correlation_adjustment': correlation_adjustment,
        'interpretation': self._interpret_score(final_score),
        'market_regime': regime,
        'patterns': patterns,
        'percentiles': percentiles,
        'individual_scores': scores,
        'indicators': indicators
    }
```

**Output example:**
```python
{
    'overall_score': 15.2,
    'raw_score': 18.0,
    'regime_adjustment': 0,
    'correlation_adjustment': 10,
    'interpretation': 'Warunki płynności: Umiarkowanie pozytywne',
    'market_regime': {
        'regime': 'RISK_ON',
        'multiplier': 1.0,
        'triggers': []
    },
    'patterns': {
        'conflicts': [...],
        'reinforcements': [...],
        'compound_signals': [...],
        'score_adjustments': 10
    },
    'percentiles': {...},
    'individual_scores': {...}
}
```

---

### 3. `load_data()` - Streamlit Cache
**Plik:** `app.py:261-285`

**Co robi:**
- Pobiera dane (używa cache Streamlit)
- Obsługuje błędy API
- Zarządza stanem sesji

```python
@st.cache_data(ttl=300)  # Cache na 5 minut
def load_data(api_key: str, days_back: int):
    """Ładuje dane z FRED (z cache)"""
    try:
        monitor = LiquidityMonitor(fred_api_key=api_key)
        indicators = monitor.get_all_indicators(days_back=days_back)
        analysis = monitor.analyze_liquidity_conditions(indicators)
        return indicators, analysis, monitor
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None, None, None
```

**Dlaczego cache?**
- FRED API ma limity (120 requests/minutę)
- Dane aktualizują się raz dziennie
- Znacznie przyspiesza ładowanie

---

## 🎨 Interfejs Użytkownika

### Sekcje UI (od góry)

#### 1. Header + Executive Summary
**Plik:** `app.py:475-540`

```python
# Gradient title
st.markdown('<h1 class="main-title">📊 Liquidity Monitor Pro</h1>')

# Executive Summary - CO ROBIĆ?
if score > 40:
    action = "FULL RISK-ON"
    details = "Zwiększ ekspozycję na wzrostowe aktywa..."
elif score > 0:
    action = "BALANCED APPROACH"
# ... etc

st.markdown(f"""
<div class="exec-summary">
    <h2>{action_emoji} Executive Summary: {action_text}</h2>
    <div class="exec-action">
        <strong>🎯 REKOMENDACJA:</strong><br/>
        {action_details}
    </div>
</div>
""")
```

#### 2. Quick Stats (4 metryki)
**Plik:** `app.py:542-596`

- **VIX Index** - Strach na rynku
- **Yield Curve** - Krzywa dochodowości (recesja?)
- **Bank Reserves** - Płynność systemu
- **Liquidity Score** - Końcowy wynik

```python
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="quick-stat" style="border-left-color: {vix_color};">
        <h4>VIX Index</h4>
        <div class="value">{vix_val:.1f}</div>
        <div class="change">▲ {vix_change:.1f} (7d)</div>
    </div>
    """)
```

**Hover effects:**
```css
.quick-stat:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
```

#### 3. Reżim Rynkowy
**Plik:** `app.py:613-682`

- Wyświetla aktualny reżim (RISK_ON/RISK_OFF/CRISIS)
- Kolor i ikona w zależności od reżimu
- Expander "Co to znaczy dla mnie?" z praktycznymi poradami

```python
if regime['regime'] == 'RISK_ON':
    regime_icon = "🟢"
    regime_color = "green"
elif regime['regime'] == 'RISK_OFF':
    regime_icon = "🟡"
    regime_color = "orange"
else:
    regime_icon = "🔴"
    regime_color = "red"

st.markdown(f"""
<div style="background: {regime_color}; padding: 15px;">
    {regime_icon} Reżim: {regime['regime']}
</div>
""")
```

#### 4. Wzorce i Korelacje
**Plik:** `app.py:684-755`

- Wyświetla wykryte wzorce (conflicts, reinforcements, compound signals)
- Legenda wyjaśniająca co to są wzorce
- Analogia medyczna: "termometr + kaszel + ból = CHOROBA"

#### 5. Percentyle Historyczne
**Plik:** `app.py:757-850`

- Tabela z percentylami wszystkich wskaźników
- Progress bar wizualizujący percentyl
- Legenda "Dlaczego percentyle są lepsze niż stałe progi?"

#### 6. Słownik Pojęć
**Plik:** `app.py:1100-1350`

5 sekcji:
- Podstawowe pojęcia płynności
- Rezerwy i operacje Fed
- Stopy procentowe i spready
- Wskaźniki ryzyka
- Inflacja i makro

---

## 🔨 Jak Rozbudować

### Dodanie Nowego Wskaźnika

**Przykład: Dodajmy "LIBOR 3M"**

#### Krok 1: Dodaj do `INDICATOR_MAPPINGS`
**Plik:** `liquidity_monitor.py:44-85`

```python
self.INDICATOR_MAPPINGS = {
    # ... existing indicators ...

    # Dodaj nowy wskaźnik
    'libor_3m': {
        'series_id': 'USD3MTD156N',  # FRED series ID
        'name': 'LIBOR 3-miesięczny',
        'description': 'London Interbank Offered Rate 3M'
    }
}
```

#### Krok 2: Dodaj wagę
**Plik:** `liquidity_monitor.py:86-109`

```python
self.indicator_weights = {
    # ... existing weights ...
    'libor_3m': 0.03  # 3% wagi
}
```

#### Krok 3: Dodaj funkcję scoringową
**Plik:** `liquidity_monitor.py` (dodaj przed `analyze_liquidity_conditions`)

```python
def _score_libor_3m(self, value: float) -> float:
    """
    LIBOR 3M scoring
    Niższy = lepsza płynność (+)
    Wyższy = napięcie w systemie (-)
    """
    if value < 3.0:
        return 5
    elif value < 4.0:
        return 0
    elif value < 5.0:
        return -5
    else:
        return -10
```

#### Krok 4: Dodaj do UI (opcjonalne)
**Plik:** `app.py` (w sekcji Dane Szczegółowe)

```python
# W tabeli wskaźników
st.markdown(f"""
| **LIBOR 3M** | {indicators['libor_3m']['current']:.2f}% |
| Zmiana 7d | {indicators['libor_3m']['change_7d']:+.2f}% |
""")
```

#### Krok 5: Test
```bash
py test_percentiles.py
```

---

### Modyfikacja Systemu Wag

**Scenariusz:** Chcesz zwiększyć wagę VIX z 10% do 15%

**Plik:** `liquidity_monitor.py:86-109`

```python
self.indicator_weights = {
    'vix': 0.15,  # Zmieniono z 0.10 na 0.15
    # WAŻNE: Suma wag powinna = 1.0 (100%)
    # Zmniejsz inne wagi proporcjonalnie
}
```

**Weryfikacja sumy wag:**
```python
total_weight = sum(self.indicator_weights.values())
print(f"Suma wag: {total_weight}")  # Powinno być 1.0
```

---

### Dodanie Nowego Wzorca (Pattern)

**Przykład: "Dollar Strength + VIX Low = Global Risk-On"**

**Plik:** `liquidity_monitor.py:323-423`

```python
def detect_correlations_and_conflicts(self, indicators: Dict) -> Dict:
    # ... existing code ...

    # Dodaj nowy wzorzec
    if 'dollar_index' in indicators and 'vix' in indicators:
        dollar = indicators['dollar_index']['current']
        vix = indicators['vix']['current']

        # Silny dolar + niski VIX = globalne risk-on
        if dollar > 105 and vix < 15:
            patterns['reinforcements'].append({
                'type': 'global_risk_on',
                'name': 'GLOBAL RISK-ON: Silny dolar + spokojny VIX',
                'details': f'DXY={dollar:.1f}, VIX={vix:.1f}',
                'score_impact': +12
            })
            patterns['score_adjustments'] += 12

    return patterns
```

---

### Zmiana Progów Reżimów

**Scenariusz:** Chcesz bardziej konserwatywne progi dla CRISIS

**Plik:** `liquidity_monitor.py:111-145`

```python
self.market_regimes = {
    'CRISIS': {
        'multiplier': 1.8,
        'conditions': {
            'vix': '>25',       # Było >30, teraz >25
            'nfci': '>0.3',     # Było >0.5, teraz >0.3
            'hy_spread': '>6'   # Było >7, teraz >6
        }
    }
}
```

**Efekt:** System będzie szybciej wykrywał kryzysy.

---

## 🐛 Troubleshooting

### Problem 1: "Brak klucza API"
**Error:**
```
❌ Brak klucza API w pliku .env!
```

**Rozwiązanie:**
1. Sprawdź czy istnieje plik `.env` w `C:\FRED\`
2. Otwórz `.env` i upewnij się że zawiera:
   ```
   FRED_API_KEY=twoj_klucz_tutaj
   ```
3. Klucz NIE może mieć spacji ani cudzysłowów
4. Zrestartuj aplikację: `Ctrl+C` → `py -m streamlit run app.py`

---

### Problem 2: "Rate limit exceeded"
**Error:**
```
429 Too Many Requests
```

**Przyczyna:** Przekroczony limit FRED API (120 requests/min)

**Rozwiązanie:**
1. Zaczekaj 1 minutę
2. Kliknij "🔄 Odśwież dane"
3. Zmniejsz `days_back` w sidebarze (365 → 90)
4. Cache Streamlit pomoże (dane są cached na 5 minut)

---

### Problem 3: "Nie widzę zmian w UI"
**Symptomy:**
- Zmieniłeś kod ale aplikacja wygląda tak samo
- Brak nowych sekcji

**Rozwiązanie:**
1. **Hard refresh przeglądarki:**
   - Windows: `Ctrl + Shift + R` lub `Ctrl + F5`
   - Mac: `Cmd + Shift + R`
2. **Wyczyść cache Streamlit:**
   - Kliknij przycisk "🔄 Odśwież dane" w sidebarze
   - Lub naciśnij `C` w konsoli Streamlit → Clear cache
3. **Zrestartuj aplikację:**
   ```bash
   # Zatrzymaj (Ctrl+C w konsoli)
   # Uruchom ponownie
   py -m streamlit run app.py
   ```

---

### Problem 4: "UnicodeEncodeError"
**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f534'
```

**Przyczyna:** Emoji w konsoli Windows (cp1250 encoding)

**Rozwiązanie:**
- Emoji są tylko w Streamlit UI (działa dobrze)
- W console prints unikaj emoji lub użyj:
  ```python
  print("[CRISIS]")  # Zamiast: print("🔴 CRISIS")
  ```

---

### Problem 5: "Percentyle nie obliczają się"
**Symptomy:**
- `len(percentiles) == 0`
- Brak sekcji percentyli w UI

**Debug:**
```python
# Uruchom test
py test_percentiles.py

# Sprawdź output
print(f"Znaleziono {len(percentiles)} wskaźników")
```

**Możliwe przyczyny:**
1. Za mało historii (potrzeba min. 10 punktów danych)
2. `days_back` ustawione na zbyt małą wartość

**Rozwiązanie:**
```python
# Zwiększ days_back
indicators = monitor.get_all_indicators(days_back=365)  # Zamiast 30
```

---

### Problem 6: "Aplikacja wolno się ładuje"
**Przyczyna:** Pobieranie 18 wskaźników z FRED API

**Optymalizacja:**
1. **Cache jest już włączony** (5 minut TTL)
2. **Zmniejsz days_back:**
   - 90 dni wystarczy dla większości analiz
   - 365 dni tylko dla percentyli i długoterminowych trendów
3. **Uruchom z headless mode:**
   ```bash
   py -m streamlit run app.py --server.headless true
   ```

---

### Problem 7: "Wzorce nie wykrywają się"
**Debug:**

```python
# Dodaj logging w liquidity_monitor.py
def detect_correlations_and_conflicts(self, indicators: Dict) -> Dict:
    patterns = {...}

    # Debug output
    print(f"VIX: {indicators.get('vix', {}).get('current')}")
    print(f"Reserves: {indicators.get('reserves', {}).get('current')}")

    # ... existing code ...

    print(f"Wykryto {len(patterns['conflicts'])} konfliktów")
    print(f"Score adjustment: {patterns['score_adjustments']}")

    return patterns
```

**Sprawdź:**
- Czy wartości wskaźników są w zakresie progów?
- Czy warunki wzorca są spełnione?

---

## 📚 Przydatne Linki

### FRED API
- **Dokumentacja:** https://fred.stlouisfed.org/docs/api/fred/
- **Rejestracja klucza:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Browser danych:** https://fred.stlouisfed.org/

### Streamlit
- **Dokumentacja:** https://docs.streamlit.io/
- **API Reference:** https://docs.streamlit.io/library/api-reference
- **Cache:** https://docs.streamlit.io/library/api-reference/performance/st.cache_data

### Wskaźniki Finansowe
- **VIX (CBOE):** https://www.cboe.com/tradable_products/vix/
- **NFCI (Chicago Fed):** https://www.chicagofed.org/publications/nfci/index
- **Yield Curve:** https://www.treasury.gov/resource-center/data-chart-center/interest-rates/

---

## 🎓 Dalsze Kroki

### Rekomendowane Ulepszenia

#### 1. Alerty Email/SMS
```python
# Dodaj w liquidity_monitor.py
def send_alert(score: float, regime: str):
    if score < -50 or regime == 'CRISIS':
        # Wyślij email przez SendGrid/Gmail API
        send_email(
            to='twoj@email.com',
            subject='🚨 CRISIS ALERT',
            body=f'Score: {score}, Regime: {regime}'
        )
```

#### 2. Backtesting
```python
# Testuj algorytm na danych historycznych
def backtest(start_date, end_date):
    results = []
    for date in date_range(start_date, end_date):
        indicators = monitor.get_all_indicators(as_of_date=date)
        analysis = monitor.analyze_liquidity_conditions(indicators)
        results.append({
            'date': date,
            'score': analysis['overall_score'],
            'regime': analysis['market_regime']['regime']
        })
    return results
```

#### 3. Machine Learning
```python
# Użyj ML do optymalizacji wag
from sklearn.ensemble import RandomForestRegressor

# Train model
X = historical_indicators  # Features
y = future_market_returns  # Target
model = RandomForestRegressor()
model.fit(X, y)

# Get optimal weights
importances = model.feature_importances_
```

#### 4. Real-time WebSocket
```python
# Zamiast co 5 minut, real-time updates
import websocket

def on_message(ws, message):
    # Aktualizuj wskaźniki real-time
    update_indicators(message)

ws = websocket.WebSocketApp(
    "wss://fred-realtime.example.com",
    on_message=on_message
)
ws.run_forever()
```

---

## ✅ Checklist: Przed Deploymentem

- [ ] Plik `.env` NIE jest w repozytorium git
- [ ] `.gitignore` zawiera `.env`
- [ ] `requirements.txt` jest aktualny
- [ ] Testy działają: `py test_percentiles.py`
- [ ] Aplikacja uruchamia się: `py -m streamlit run app.py`
- [ ] Cache jest włączony (sprawdź `@st.cache_data`)
- [ ] Error handling dla wszystkich API calls
- [ ] Dokumentacja jest aktualna (ten plik!)

---

## 📝 Changelog

### 2024-01-15: Initial Release v1.0
- ✅ 18 wskaźników FRED
- ✅ System wag (3-tier)
- ✅ Reżimy rynkowe (RISK_ON/RISK_OFF/CRISIS)
- ✅ Wykrywanie 8 wzorców korelacji
- ✅ Percentyle historyczne
- ✅ Modern UI z gradientami
- ✅ Executive Summary
- ✅ Quick Stats cards
- ✅ Słownik pojęć

---

## 🤝 Support

**Masz pytania?**
1. Przeczytaj sekcję [Troubleshooting](#troubleshooting)
2. Sprawdź [FRED API docs](https://fred.stlouisfed.org/docs/api/fred/)
3. Przeczytaj [Streamlit docs](https://docs.streamlit.io/)

**Znalazłeś bug?**
- Dodaj logging w odpowiedniej funkcji
- Sprawdź czy dane z API są poprawne
- Uruchom `test_percentiles.py` do debugowania

---

## 📄 Licencja

Projekt prywatny. Nie udostępniaj klucza API publicznie!

---

**Wersja dokumentacji:** 1.0
**Data:** 2024-01-15
**Autor:** FRED Liquidity Monitor Team

---

## 🚀 Quick Start (TL;DR)

```bash
# 1. Instalacja
cd C:\FRED
pip install -r requirements.txt

# 2. Konfiguracja
echo FRED_API_KEY=twoj_klucz > .env

# 3. Uruchomienie
py -m streamlit run app.py

# 4. Otwórz w przeglądarce
# http://localhost:8501
```

**Gotowe! 🎉**
