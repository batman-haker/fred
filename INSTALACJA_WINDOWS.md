# 🪟 Instalacja na Windows - Krok po kroku

## ❌ Problem: Python nie jest zainstalowany

Twój system Windows nie ma zainstalowanego Pythona lub nie jest poprawnie skonfigurowany.

---

## ✅ ROZWIĄZANIE - Instalacja Python

### Krok 1: Pobierz Python

1. Otwórz stronę: **https://www.python.org/downloads/**
2. Kliknij **"Download Python 3.12.x"** (lub najnowsza wersja)
3. Pobierz instalator (około 25 MB)

### Krok 2: Zainstaluj Python

⚠️ **BARDZO WAŻNE!**

1. Uruchom pobrany instalator `python-3.12.x-amd64.exe`
2. **✅ ZAZNACZ checkbox: "Add Python to PATH"** (NA DOLE!)
3. Kliknij **"Install Now"**
4. Poczekaj na instalację (2-3 minuty)
5. Kliknij **"Close"**

### Krok 3: Zrestartuj Terminal

**WAŻNE:** Musisz zamknąć i otworzyć na nowo terminal/PowerShell!

1. Zamknij wszystkie okna terminala
2. Otwórz nowy terminal (PowerShell lub CMD)
3. Przejdź do folderu projektu:
   ```cmd
   cd C:\FRED
   ```

### Krok 4: Sprawdź instalację

W terminalu wpisz:

```cmd
python --version
```

Powinieneś zobaczyć:
```
Python 3.12.x
```

Jeśli nadal nie działa, wpisz:
```cmd
py --version
```

---

## 📦 Instalacja zależności

Gdy Python już działa, zainstaluj potrzebne biblioteki:

```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Lub:
```cmd
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Instalacja potrwa 2-5 minut.

---

## 🚀 Uruchomienie aplikacji

### Opcja 1: Użyj skryptu .bat

Kliknij dwukrotnie na plik: **`start_app.bat`**

### Opcja 2: Ręcznie w terminalu

```cmd
cd C:\FRED
python -m streamlit run app.py
```

Lub:
```cmd
py -m streamlit run app.py
```

### Opcja 3: Najprostszy test

Uruchom prosty test (utworzony poniżej):
```cmd
python test_setup.py
```

---

## 🔍 Rozwiązywanie problemów

### Problem 1: "python nie jest rozpoznawany"

**Przyczyna:** Python nie jest w PATH

**Rozwiązanie:**
1. Odinstaluj Python (Panel sterowania → Programy)
2. Zainstaluj ponownie i **KONIECZNIE zaznacz "Add Python to PATH"**
3. Zrestartuj komputer

### Problem 2: "ModuleNotFoundError: No module named 'streamlit'"

**Przyczyna:** Nie zainstalowałeś zależności

**Rozwiązanie:**
```cmd
python -m pip install streamlit pandas requests plotly
```

### Problem 3: "Access Denied" / "Permission Error"

**Rozwiązanie:** Uruchom terminal jako Administrator:
1. Prawym klawiszem na PowerShell/CMD
2. "Uruchom jako Administrator"
3. Spróbuj ponownie

### Problem 4: Port 8501 zajęty

**Rozwiązanie:** Aplikacja automatycznie użyje innego portu (8502, 8503...)
Sprawdź w terminalu jaki port został użyty.

### Problem 5: Firewall blokuje

**Rozwiązanie:** Gdy Windows zapyta o dostęp, kliknij "Zezwól"

---

## 🧪 Test instalacji

Stwórz plik `test_setup.py` (lub użyj już utworzonego) i uruchom:

```cmd
python test_setup.py
```

Jeśli wszystko działa, zobaczysz:
```
✅ Python działa!
✅ Requests zainstalowane
✅ Pandas zainstalowane
✅ Streamlit zainstalowane
✅ Plotly zainstalowane
✅ Klucz API znaleziony
✅ Wszystko gotowe!
```

---

## 💡 Alternatywa: Użyj Google Colab

Jeśli nie możesz zainstalować Pythona lokalnie, możesz użyć Google Colab:

1. Wejdź na: https://colab.research.google.com/
2. Utwórz nowy notebook
3. Skopiuj kod z `liquidity_monitor.py`
4. Uruchom w przeglądarce

(Nie będzie interfejsu Streamlit, ale skrypt konsolowy zadziała)

---

## 📞 Pomoc

Jeśli nadal masz problemy:

1. Sprawdź czy Python jest w PATH:
   ```cmd
   echo %PATH%
   ```
   Powinieneś zobaczyć ścieżkę do Pythona

2. Sprawdź wersję pip:
   ```cmd
   python -m pip --version
   ```

3. Przeinstaluj Python z checkboxem "Add to PATH"

---

## ⏭️ Następne kroki po instalacji

Gdy Python zadziała:

1. Zainstaluj zależności: `python -m pip install -r requirements.txt`
2. Uruchom test: `python test_setup.py`
3. Uruchom aplikację: `python -m streamlit run app.py`
4. Otwórz: http://localhost:8501

---

**Powodzenia!** 🎉

Jeśli którykolwiek krok nie działa, daj znać na którym etapie się zatrzymałeś.
