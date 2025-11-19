# 📊 Liquidity Monitor - Instrukcja instalacji i użytkowania

System do monitorowania wskaźników płynności finansowej: TGA, rezerwy banków, SOFR, reverse repo, bilans Fed.

**NOWA WERSJA:** Dostępna aplikacja webowa z interaktywnym dashboardem! 🎉

## 🚀 Szybki start

### 1. Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt
```

### 2. Aplikacja Webowa (ZALECANE!) 🌐

Nowa wersja z dashboardem Streamlit - pełna wizualizacja, wykresy, alerty!

#### Windows:
```bash
# Uruchom aplikację
start_app.bat
```

#### Linux/Mac:
```bash
# Nadaj uprawnienia
chmod +x start_app.sh

# Uruchom aplikację
./start_app.sh
```

#### Ręcznie:
```bash
streamlit run app.py
```

Aplikacja otworzy się w przeglądarce pod adresem: **http://localhost:8501**

### 3. Skrypt konsolowy (wersja klasyczna)

```bash
# Ustaw klucz API jako zmienną środowiskową
export FRED_API_KEY='fc1ef11c8f65429677a78db10a3a4d2e'

# Uruchom skrypt
python liquidity_monitor.py
```

---

## 🌟 Funkcje Aplikacji Webowej

Aplikacja webowa (`app.py`) oferuje:

### 📊 Dashboard Real-Time
- **Wskaźnik płynności** z gauge meter (-100 do +100)
- **Status rynku**: RISK-ON / NEUTRAL / UWAGA / RISK-OFF
- **Metryki na żywo**: Rezerwy, TGA, RRP, Bilans Fed, SOFR, IORB, EFFR
- **Alerty i sygnały** - natychmiastowe ostrzeżenia o zmianach

### 📈 Wykresy Interaktywne
- **Wykresy czasowe** dla wszystkich wskaźników (Plotly)
- **Multi-panel dashboard** - wszystkie wskaźniki na jednym widoku
- **Zoom, pan, hover** - pełna interaktywność
- **Statystyki**: min, max, średnia, odchylenie standardowe

### 📋 Dane Historyczne
- **Przeglądanie danych** w formie tabelarycznej
- **Eksport do CSV** - pobierz dane dla pojedynczego wskaźnika
- **Eksport do JSON** - pobierz wszystkie dane z analizą
- **Zakres dat**: 30-365 dni historii

### 🔔 System Alertów
- **Konfiguracja email** dla powiadomień
- **Progi alertów** - ustaw custom threshold
- **Historia alertów** - log wszystkich powiadomień
- **Auto-monitoring** warunków płynności

### ⚙️ Dodatkowe
- **Auto-refresh** - odświeżanie co godzinę
- **Cache danych** - szybsze ładowanie
- **Responsywny design** - działa na telefonie i tablecie
- **Dark mode ready** - przyjazny dla oczu

---

## 📖 Instrukcja Użycia Aplikacji Webowej

1. **Uruchom aplikację** (patrz: Szybki start)
2. **Wprowadź API key** w pasku bocznym (lub użyj .env)
3. **Dashboard się załaduje** - zobaczysz wszystkie wskaźniki
4. **Eksploruj zakładki**:
   - 📊 **Wszystkie Wykresy** - przegląd wszystkich wskaźników
   - 📈 **Pojedyncze Wskaźniki** - szczegółowa analiza
   - 📋 **Dane Tabelaryczne** - eksport danych
   - 🔔 **Alerty** - konfiguracja powiadomień

5. **Ustaw auto-refresh** (opcjonalnie) dla ciągłego monitoringu

---

### 2. Uzyskaj klucz API do FRED (WAŻNE!)

Dane pobierane są z Federal Reserve Economic Data (FRED) - oficjalnego źródła danych Fed.

1. Zarejestruj się: https://fred.stlouisfed.org/
2. Uzyskaj klucz API: https://fred.stlouisfed.org/docs/api/api_key.html
3. Ustaw klucz jako zmienną środowiskową:

```bash
# Linux/Mac
export FRED_API_KEY='twoj_klucz_api'

# Windows (PowerShell)
$env:FRED_API_KEY='twoj_klucz_api'

# Lub dodaj do ~/.bashrc / ~/.zshrc (trwale):
echo 'export FRED_API_KEY="twoj_klucz"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Uruchom skrypt

```bash
python liquidity_monitor.py
```

## 📈 Co monitoruje skrypt?

### Kluczowe wskaźniki:

1. **Rezerwy banków (Bank Reserves)** - TOTRESNS
   - Pokazuje ile gotówki jest w systemie bankowym
   - > 3000B = luźne warunki (✅ risk-on)
   - < 2800B = napięte warunki (⚠️ ryzyko)

2. **TGA - Treasury General Account** - WTREGEN
   - Konto rządu w Fed
   - Wzrost TGA = drenuje płynność (❌ negatyw)
   - Spadek TGA = dodaje płynność (✅ pozytyw)

3. **Reverse Repo (ON RRP)** - RRPONTSYD
   - Kasa "zaparkowana" w Fed
   - Wysoki = jest bufor płynności
   - Niski = brak bufora, system wrażliwy

4. **SOFR - Secured Overnight Financing Rate** - SOFR
   - Główna rynkowa stopa procentowa USA
   - Wysoki spread SOFR-IORB = dźwignia drożeje (❌)

5. **IORB - Interest on Reserve Balances** - IORB
   - Stopa Fed na rezerwy banków
   - Punkt odniesienia dla SOFR

6. **Bilans Fed (Fed Balance Sheet)** - WALCL
   - Spadek = QT aktywne (ściąga płynność)
   - Wzrost = QE/RMP (dodaje płynność)

## 🎯 Interpretacja wyników

### Scoring (-100 do +100):

- **+40 do +100**: 🟢 RISK-ON
  - Warunki sprzyjają wzrostom
  - Dobre dla Nasdaq, BTC, high-beta stocks

- **0 do +40**: 🟡 NEUTRALNE
  - Umiarkowane warunki

- **-40 do 0**: 🟠 UWAGA
  - Pogarszające się warunki
  - Obserwuj sytuację

- **-100 do -40**: 🔴 RISK-OFF
  - Napięcia w płynności
  - Ostrożność! Prawdopodobne spadki

### Alerty:

- **CRITICAL**: 🚨 Natychmiastowa uwaga wymagana
- **WARNING**: ⚠️  Obserwuj uważnie

## 📊 Przykładowy output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                      RAPORT WSKAŹNIKÓW PŁYNNOŚCI                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
Czas: 2025-11-18 10:30:00

🟢 RISK-ON: Warunki płynności sprzyjają wzrostom (Nasdaq/BTC)
Ocena ogólna: 45/100

────────────────────────────────────────────────────────────────────────────────
KLUCZOWE WSKAŹNIKI:
────────────────────────────────────────────────────────────────────────────────
Rezerwy banków           3250.50 B USD  | 7d: ▲   +12.30
TGA (konto rządu)         650.20 B USD  | 7d: ▼   -45.60
Reverse Repo              320.80 B USD  | 7d: ▼   -15.20
Bilans Fed               7100.40 B USD  | 7d: ▲    +5.10
SOFR                        4.32 %      | 7d: =     0.02
IORB                        4.30 %      | 7d: =     0.00
SOFR-IORB spread            0.02 %      |

────────────────────────────────────────────────────────────────────────────────
📍 SYGNAŁY:
────────────────────────────────────────────────────────────────────────────────
  🟢 Wysokie rezerwy: $3251B - system luźny
  🟢 TGA spada (-45.6B) - dodaje płynność
  🟢 SOFR stabilny (spread: 0.02%)
```

## 🔄 Automatyzacja

### Uruchamianie co godzinę (cron):

```bash
# Edytuj crontab
crontab -e

# Dodaj linię (uruchamia o każdej pełnej godzinie):
0 * * * * cd /ścieżka/do/projektu && /usr/bin/python3 liquidity_monitor.py >> liquidity.log 2>&1
```

### Uruchamianie w tle non-stop:

Stwórz plik `run_monitor_loop.py`:

```python
#!/usr/bin/env python3
import time
from liquidity_monitor import LiquidityMonitor
import os

api_key = os.environ.get('FRED_API_KEY')
monitor = LiquidityMonitor(fred_api_key=api_key)

while True:
    print(f"\n{'='*80}")
    print(f"Aktualizacja: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*80)
    
    indicators = monitor.get_all_indicators()
    if indicators:
        analysis = monitor.analyze_liquidity_conditions(indicators)
        monitor.print_report(indicators, analysis)
        monitor.save_to_json(indicators, analysis)
    
    # Czekaj 1 godzinę
    print("\n⏳ Następna aktualizacja za 1 godzinę...")
    time.sleep(3600)
```

Uruchom:
```bash
python run_monitor_loop.py
```

## 📧 Dodaj powiadomienia email

Możesz rozszerzyć skrypt o wysyłanie alertów:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(analysis):
    if analysis['overall_score'] < -30:  # Risk-off
        msg = MIMEText(analysis['interpretation'])
        msg['Subject'] = '🚨 ALERT: Napięcia w płynności!'
        msg['From'] = 'twoj@email.com'
        msg['To'] = 'twoj@email.com'
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('twoj@email.com', 'hasło')
            server.send_message(msg)
```

## 🔗 Źródła danych

Wszystkie dane pochodzą z oficjalnych źródeł:

- **FRED** (Federal Reserve Economic Data): https://fred.stlouisfed.org/
- **NY Fed** (Markets): https://www.newyorkfed.org/markets
- **US Treasury**: https://fiscaldata.treasury.gov/

## 📚 Dodatkowe zasoby

- Dokumentacja FRED API: https://fred.stlouisfed.org/docs/api/
- NY Fed - SOFR: https://www.newyorkfed.org/markets/reference-rates/sofr
- Treasury Daily Statement: https://fiscaldata.treasury.gov/datasets/treasury-daily-statement/

## 🆘 Rozwiązywanie problemów

### "Brak klucza API"
- Sprawdź czy zmienna środowiskowa jest ustawiona: `echo $FRED_API_KEY`
- Upewnij się że klucz jest aktywny na stronie FRED

### "Connection error"
- Sprawdź połączenie internetowe
- FRED API może mieć limity (120 requests/minute)

### "No data returned"
- Niektóre serie są aktualizowane z opóźnieniem (1-2 dni)
- Weekend/święta - brak nowych danych

## 💡 Wskazówki

1. **Uruchamiaj po godzinach rynkowych** (po 16:00 EST) - wtedy dane są najświeższe
2. **Analizuj trendy**, nie pojedyncze wartości
3. **Łącz z analizą techniczną** - wskaźniki płynności to fundamenty
4. **Zapisuj historię** - zobaczysz wzorce przed dużymi ruchami

## 🎓 Co dalej?

Możesz rozszerzyć skrypt o:
- Wykresy (matplotlib, plotly)
- Dashboard webowy (Streamlit, Flask)
- Integrację z Discordem/Telegram (boty)
- Machine learning (predykcja warunków)
- Korelacje z cenami BTC/SPX

---

**Autor**: Claude  
**Licencja**: MIT  
**Wersja**: 1.0
