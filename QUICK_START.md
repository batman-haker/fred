# 🚀 QUICK START - Liquidity Monitor Web App

## Co zostało utworzone?

✅ **Aplikacja webowa Streamlit** (`app.py`) - pełny dashboard z wykresami
✅ **Skrypt konsolowy** (`liquidity_monitor.py`) - wersja CLI
✅ **Pliki konfiguracyjne** - API key już skonfigurowany
✅ **Skrypty uruchomieniowe** - Windows i Linux/Mac

---

## 🎯 Jak uruchomić aplikację?

### Krok 1: Zainstaluj Python
Jeśli nie masz Pythona, pobierz z: https://www.python.org/downloads/

**WAŻNE:** Podczas instalacji zaznacz "Add Python to PATH"!

### Krok 2: Zainstaluj zależności

Otwórz terminal w folderze `C:\FRED` i wykonaj:

```bash
pip install -r requirements.txt
```

Lub użyj Python bezpośrednio:
```bash
python -m pip install -r requirements.txt
```

### Krok 3: Uruchom aplikację webową

#### Windows (najłatwiej):
Kliknij dwukrotnie na plik `start_app.bat`

#### Terminal (Windows/Linux/Mac):
```bash
streamlit run app.py
```

### Krok 4: Otwórz w przeglądarce

Aplikacja automatycznie otworzy się w przeglądarce pod adresem:
**http://localhost:8501**

Jeśli nie, wpisz ten adres ręcznie.

---

## 🔑 Twój klucz API

Twój klucz FRED API jest już skonfigurowany w pliku `.env`:
```
fc1ef11c8f65429677a78db10a3a4d2e
```

**Aplikacja automatycznie go użyje!** Możesz też wprowadzić klucz ręcznie w interfejsie webowym.

---

## 📊 Co zobaczysz w aplikacji?

### Dashboard zawiera:

1. **Gauge Meter** - ocena płynności od -100 do +100
2. **Status rynku** - RISK-ON / NEUTRAL / UWAGA / RISK-OFF
3. **8 kluczowych wskaźników**:
   - Rezerwy Banków
   - TGA (konto rządu)
   - Reverse Repo
   - Bilans Fed
   - SOFR
   - IORB
   - EFFR
   - SOFR-IORB Spread

4. **Alerty i sygnały** - ostrzeżenia o zmianach
5. **Wykresy interaktywne** - wszystkie wskaźniki na wykresach
6. **Eksport danych** - CSV i JSON

---

## 🎨 Zakładki aplikacji

### 📊 Wszystkie Wykresy
- Panel 6 wykresów z wszystkimi wskaźnikami
- Idealne do zobaczenia pełnego obrazu rynku

### 📈 Pojedyncze Wskaźniki
- Wybierz konkretny wskaźnik do analizy
- Statystyki: min, max, średnia, odchylenie

### 📋 Dane Tabelaryczne
- Przeglądaj dane w formie tabeli
- Pobierz CSV dla konkretnego wskaźnika
- Eksportuj wszystkie dane do JSON

### 🔔 Alerty
- Skonfiguruj powiadomienia email
- Ustaw próg alertu (score)
- Zobacz historię alertów

---

## ⚙️ Konfiguracja

### Zmiana zakresu dat
W pasku bocznym użyj slidera "Dni historii" (30-365 dni)

### Auto-odświeżanie
Zaznacz checkbox "Auto-odświeżanie (co 1h)" w pasku bocznym

### Ręczne odświeżanie
Kliknij przycisk "🔄 Odśwież dane" w pasku bocznym

---

## 🔍 Interpretacja wyników

### Score płynności:
- **+40 do +100**: 🟢 **RISK-ON** - Warunki sprzyjają wzrostom (Nasdaq/BTC)
- **0 do +40**: 🟡 **NEUTRALNE** - Umiarkowane warunki
- **-40 do 0**: 🟠 **UWAGA** - Pogarszające się warunki
- **-100 do -40**: 🔴 **RISK-OFF** - Napięcia w płynności!

### Kluczowe wskaźniki:

**Rezerwy Banków**
- Wysoki poziom (>3000B) = 🟢 Dużo płynności w systemie
- Niski poziom (<2800B) = 🔴 Ryzyko napięć

**TGA (Treasury General Account)**
- Spadek TGA = 🟢 Dodaje płynność do rynku
- Wzrost TGA = 🔴 Zabiera płynność z rynku

**Reverse Repo**
- Wysoki (>500B) = 🟢 Jest bufor płynności
- Niski (<100B) = 🔴 Brak bufora

**SOFR-IORB Spread**
- Wąski spread (<0.10%) = 🟢 Stabilne warunki
- Szeroki spread (>0.20%) = 🔴 Napięcia w finansowaniu

---

## 💡 Wskazówki użytkowania

1. **Sprawdzaj regularnie** - najlepiej po godzinach rynkowych (po 16:00 EST)
2. **Analizuj trendy** - nie pojedyncze wartości
3. **Łącz z analizą techniczną** - fundamenty + TA = lepsze decyzje
4. **Exportuj dane** - buduj własną bazę historyczną
5. **Ustaw alerty** - nie przegap ważnych zmian

---

## 🐛 Rozwiązywanie problemów

### "ModuleNotFoundError: No module named 'streamlit'"
Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

### "Brak danych" / "Empty DataFrame"
- Sprawdź połączenie internetowe
- Upewnij się, że klucz API jest poprawny
- FRED może mieć limit requestów (120/min)

### Aplikacja nie otwiera się w przeglądarce
Wpisz ręcznie w przeglądarce: `http://localhost:8501`

### Port 8501 zajęty
Streamlit użyje następnego wolnego portu (8502, 8503, etc.)

---

## 🚀 Następne kroki

Możesz rozbudować aplikację o:

1. **Email notifications** - prawdziwe powiadomienia SMTP
2. **Telegram/Discord bot** - alerty na komunikatorach
3. **Machine Learning** - predykcja warunków płynności
4. **Korelacje** - porównanie z cenami BTC/SPX/Nasdaq
5. **Więcej wskaźników** - M2, DXY, VIX, etc.

---

## 📁 Struktura plików

```
C:\FRED\
├── app.py                 # Aplikacja webowa Streamlit ⭐
├── liquidity_monitor.py   # Skrypt konsolowy
├── requirements.txt       # Zależności Python
├── .env                   # Klucz API (nie commituj!)
├── .gitignore            # Git ignore rules
├── start_app.bat         # Uruchom (Windows)
├── start_app.sh          # Uruchom (Linux/Mac)
├── README.md             # Dokumentacja pełna
└── QUICK_START.md        # Ten plik
```

---

## 📞 Pomoc

Jeśli masz problemy:
1. Sprawdź README.md - pełna dokumentacja
2. Upewnij się że Python i pip są zainstalowane
3. Sprawdź czy klucz API działa: https://fred.stlouisfed.org/

---

**Powodzenia z monitoringiem płynności!** 📊📈

Aplikacja stworzona w oparciu o oficjalne dane FRED (Federal Reserve Economic Data)
