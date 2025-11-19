#!/usr/bin/env python3
"""
Liquidity Monitor - Streamlit Web Application
Aplikacja webowa do monitorowania wskaźników płynności rynkowej
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from liquidity_monitor import LiquidityMonitor

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja strony
st.set_page_config(
    page_title="Liquidity Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicjalizacja session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'indicators' not in st.session_state:
    st.session_state.indicators = None
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'alert_email' not in st.session_state:
    st.session_state.alert_email = ""

# Funkcja do ładowania danych
@st.cache_data(ttl=3600)  # Cache na 1 godzinę
def load_data(api_key, days_back=90):
    """Ładuje dane z FRED"""
    monitor = LiquidityMonitor(fred_api_key=api_key)
    indicators = monitor.get_all_indicators(days_back=days_back)  # Przekazujemy days_back!
    if indicators:
        analysis = monitor.analyze_liquidity_conditions(indicators)
        return indicators, analysis, monitor
    return None, None, monitor

def create_metric_card(label, value, change, unit="B USD", inverse=False):
    """Tworzy kartę z metryką"""
    change_color = "inverse" if inverse else "normal"
    delta_color = "inverse" if (change < 0 and not inverse) or (change > 0 and inverse) else "normal"

    if unit == "%":
        st.metric(
            label=label,
            value=f"{value:.2f}%",
            delta=f"{change:+.2f}%",
            delta_color=delta_color
        )
    else:
        st.metric(
            label=label,
            value=f"${value:.1f}B",
            delta=f"${change:+.1f}B",
            delta_color=delta_color
        )

def create_time_series_chart(indicators, metric_name, title):
    """Tworzy interaktywny wykres czasowy"""
    if metric_name not in indicators:
        return None

    data = indicators[metric_name]['data']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['value'],
        mode='lines',
        name=title,
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))

    # Dodaj linię średniej
    mean_value = data['value'].mean()
    fig.add_hline(
        y=mean_value,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Średnia: {mean_value:.2f}",
        annotation_position="right"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title="Wartość",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig

def create_multi_indicator_chart(indicators):
    """Tworzy wykres z wieloma wskaźnikami"""
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Rezerwy Banków', 'TGA',
            'Reverse Repo', 'Bilans Fed',
            'SOFR vs IORB', 'Spread SOFR-IORB'
        ),
        specs=[[{}, {}], [{}, {}], [{}, {}]]
    )

    # Rezerwy
    if 'reserves' in indicators:
        data = indicators['reserves']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='Rezerwy', line=dict(color='blue')),
            row=1, col=1
        )

    # TGA
    if 'tga' in indicators:
        data = indicators['tga']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='TGA', line=dict(color='green')),
            row=1, col=2
        )

    # Reverse Repo
    if 'reverse_repo' in indicators:
        data = indicators['reverse_repo']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='RRP', line=dict(color='orange')),
            row=2, col=1
        )

    # Bilans Fed
    if 'fed_balance' in indicators:
        data = indicators['fed_balance']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='Fed Balance', line=dict(color='purple')),
            row=2, col=2
        )

    # SOFR vs IORB
    if 'sofr' in indicators and 'iorb' in indicators:
        sofr_data = indicators['sofr']['data']
        iorb_data = indicators['iorb']['data']
        fig.add_trace(
            go.Scatter(x=sofr_data['date'], y=sofr_data['value'], name='SOFR', line=dict(color='red')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=iorb_data['date'], y=iorb_data['value'], name='IORB', line=dict(color='darkred')),
            row=3, col=1
        )

        # Spread
        merged = pd.merge(sofr_data, iorb_data, on='date', suffixes=('_sofr', '_iorb'))
        merged['spread'] = merged['value_sofr'] - merged['value_iorb']
        fig.add_trace(
            go.Scatter(x=merged['date'], y=merged['spread'], name='Spread', line=dict(color='crimson')),
            row=3, col=2
        )

    fig.update_layout(
        height=1200,
        showlegend=True,
        template='plotly_white',
        title_text="Wszystkie Wskaźniki Płynności"
    )

    return fig

def create_tier1_charts(indicators):
    """Tworzy wykresy dla Tier 1 wskaźników"""
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'M2 Money Supply', '10Y-2Y Yield Curve',
            'VIX', 'NFCI Financial Conditions',
            'Dollar Index (DXY)', 'Rezerwy (WRESBAL)'
        ),
        specs=[[{}, {}], [{}, {}], [{}, {}]]
    )

    # M2
    if 'm2' in indicators:
        data = indicators['m2']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='M2', line=dict(color='blue')),
            row=1, col=1
        )

    # Yield Curve
    if 'yield_curve' in indicators:
        data = indicators['yield_curve']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='10Y-2Y', line=dict(color='green')),
            row=1, col=2
        )
        # Dodaj linię na 0 (inwersja)
        fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=2)

    # VIX
    if 'vix' in indicators:
        data = indicators['vix']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='VIX', line=dict(color='red')),
            row=2, col=1
        )
        # Dodaj linie progowe
        fig.add_hline(y=30, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=15, line_dash="dash", line_color="green", row=2, col=1)

    # NFCI
    if 'fin_conditions' in indicators:
        data = indicators['fin_conditions']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='NFCI', line=dict(color='purple')),
            row=2, col=2
        )
        # Dodaj linię na 0
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=2)

    # Dollar Index
    if 'dollar_index' in indicators:
        data = indicators['dollar_index']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='DXY', line=dict(color='orange')),
            row=3, col=1
        )

    # Rezerwy (WRESBAL)
    if 'reserves_alt' in indicators:
        data = indicators['reserves_alt']['data']
        fig.add_trace(
            go.Scatter(x=data['date'], y=data['value'], name='Rezerwy', line=dict(color='darkblue')),
            row=3, col=2
        )

    fig.update_layout(
        height=1200,
        showlegend=True,
        template='plotly_white',
        title_text="Tier 1 Indicators - Extended Analysis"
    )

    return fig

def save_alert_settings(email, threshold):
    """Zapisuje ustawienia alertów"""
    settings = {
        'email': email,
        'threshold': threshold,
        'updated_at': datetime.now().isoformat()
    }
    with open('alert_settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

def check_and_send_alerts(analysis, email):
    """Sprawdza warunki i wysyła alerty"""
    if not email:
        return

    score = analysis['overall_score']

    # Tutaj możesz dodać kod do wysyłania emaili
    # Na razie tylko zapisujemy alert do pliku
    if score < -30:
        alert_log = {
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'interpretation': analysis['interpretation'],
            'alerts': analysis['alerts']
        }

        with open('alert_log.json', 'a') as f:
            f.write(json.dumps(alert_log) + '\n')

        st.warning(f"⚠️ Alert zapisany! Score: {score}")

# === GŁÓWNA APLIKACJA ===

# Sidebar - Konfiguracja
st.sidebar.title("⚙️ Konfiguracja")

# Pobierz API Key - obsługa zarówno lokalnego .env jak i Streamlit Cloud secrets
try:
    # Najpierw spróbuj Streamlit secrets (dla Streamlit Cloud)
    api_key = st.secrets.get('FRED_API_KEY', '')
except (AttributeError, FileNotFoundError, KeyError):
    # Jeśli nie ma st.secrets, użyj .env (dla lokalnego użycia)
    api_key = os.environ.get('FRED_API_KEY', '')

# Zakres dat
days_back = st.sidebar.slider(
    "Dni historii",
    min_value=30,
    max_value=18250,  # 50 LAT HISTORII!
    value=365,
    step=365,
    help="Wybierz zakres danych: 30-18250 dni (do 50 LAT!)"
)

# Przycisk odświeżania
if st.sidebar.button("🔄 Odśwież dane", type="primary"):
    st.cache_data.clear()
    st.session_state.last_update = datetime.now()
    st.rerun()

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-odświeżanie (co 1h)", value=False)
if auto_refresh:
    st.sidebar.info("Auto-odświeżanie aktywne")

# Informacje
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Info")
st.sidebar.markdown("""
- **Źródło**: FRED API
- **Aktualizacja**: Dane dzienne
- **Autor**: FRED Monitor
""")

if st.session_state.last_update:
    st.sidebar.markdown(f"**Ostatnia aktualizacja:**  \n{st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# === GŁÓWNA ZAWARTOŚĆ ===

# === CUSTOM CSS - NOWOCZESNY DESIGN ===
st.markdown("""
<style>
    /* Główne kolory - nowoczesna paleta */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
    }

    /* Stylowanie głównego tytułu */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
        text-align: center;
    }

    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    /* Executive Summary Card */
    .exec-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
        margin: 20px 0;
        color: white;
    }

    .exec-summary h2 {
        margin: 0 0 15px 0;
        font-size: 1.8rem;
        font-weight: 700;
    }

    .exec-summary p {
        margin: 10px 0;
        font-size: 1.15rem;
        line-height: 1.6;
    }

    .exec-action {
        background: rgba(255,255,255,0.2);
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        border-left: 4px solid #fff;
    }

    /* Quick Stats Cards */
    .quick-stat {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-left: 4px solid;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .quick-stat:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .quick-stat h4 {
        margin: 0 0 10px 0;
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .quick-stat .value {
        font-size: 2rem;
        font-weight: 700;
        margin: 5px 0;
    }

    .quick-stat .change {
        font-size: 0.95rem;
        margin-top: 5px;
    }

    /* Sekcje z lepszym spacingiem */
    .section-header {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 30px 0 20px 0;
        border-left: 5px solid #667eea;
    }

    .section-header h3 {
        margin: 0;
        color: #2c3e50;
        font-weight: 600;
    }

    /* Better typography */
    .stMarkdown {
        line-height: 1.7;
    }

    /* Metric cards modernization */
    div[data-testid="metric-container"] {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 3px solid #667eea;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        font-weight: 600;
    }

    /* Better spacing globally */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER Z GRADIENTEM ===
st.markdown('<h1 class="main-title">📊 Liquidity Monitor Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Zaawansowany system analizy płynności rynkowej z AI-driven insights</p>', unsafe_allow_html=True)

# Sprawdź czy jest API key
if not api_key:
    st.error("❌ Brak klucza API!")

    # Wykryj czy to Streamlit Cloud czy lokalne środowisko
    is_cloud = os.path.exists('/mount/src')

    if is_cloud:
        st.warning("🌐 **Streamlit Cloud**")
        st.info("""
        **Jak dodać klucz API:**
        1. Dashboard → ⚙️ Settings → Secrets
        2. Wpisz: `FRED_API_KEY = "twoj_klucz"`
        3. Save → Reboot app

        **Nie masz klucza?** https://fred.stlouisfed.org/docs/api/api_key.html
        """)
    else:
        st.warning("💻 **Uruchamiasz lokalnie**")
        st.info("""
        **Jak naprawić:**
        1. Stwórz plik `.env` w folderze projektu
        2. Dodaj: `FRED_API_KEY=twoj_klucz_tutaj`
        3. Zrestartuj aplikację

        **Nie masz klucza?** https://fred.stlouisfed.org/docs/api/api_key.html
        """)
    st.stop()

# Ładuj dane
with st.spinner('Ładowanie danych z FRED...'):
    indicators, analysis, monitor = load_data(api_key, days_back)

if not indicators:
    st.error("❌ Nie udało się pobrać danych. Sprawdź klucz API i połączenie.")
    st.stop()

st.session_state.indicators = indicators
st.session_state.analysis = analysis

# === EXECUTIVE SUMMARY - CO ROBIĆ? ===
score = analysis['overall_score']
regime = analysis.get('market_regime', {})
regime_name = regime.get('regime', 'UNKNOWN')

# Określ action based na score i reżimie
if score > 40:
    action_emoji = "🚀"
    action_text = "FULL RISK-ON"
    action_details = "Zwiększ ekspozycję na wzrostowe aktywa (tech stocks, crypto, emerging markets). Płynność sprzyja ryzyku."
    action_color = "#11998e"
elif score > 0:
    action_emoji = "📊"
    action_text = "BALANCED APPROACH"
    action_details = "Utrzymuj zbalansowany portfel. Warunki neutralne - obserwuj rozwój sytuacji."
    action_color = "#4facfe"
elif score > -40:
    action_emoji = "⚠️"
    action_text = "REDUCE RISK"
    action_details = "Zmniejsz ekspozycję na ryzyko. Zwiększ pozycję w safe-haven (obligacje, złoto, cash)."
    action_color = "#f093fb"
else:
    action_emoji = "🛑"
    action_text = "DEFENSIVE MODE"
    action_details = "Maksymalna ostrożność! Priorytet: ochrona kapitału. Gotówka i bezpieczne aktywa."
    action_color = "#f5576c"

st.markdown(f"""
<div class="exec-summary" style="background: linear-gradient(135deg, {action_color} 0%, {action_color}dd 100%);">
    <h2>{action_emoji} Executive Summary: {action_text}</h2>
    <p><strong>Score:</strong> {score:.0f}/100 | <strong>Reżim:</strong> {regime_name}</p>
    <div class="exec-action">
        <strong>🎯 REKOMENDACJA:</strong><br/>
        {action_details}
    </div>
</div>
""", unsafe_allow_html=True)

# === QUICK STATS - 4 KLUCZOWE METRYKI ===
col1, col2, col3, col4 = st.columns(4)

# Statystyka 1: VIX (strach)
vix_val = indicators.get('vix', {}).get('current', 0)
vix_change = indicators.get('vix', {}).get('change_7d', 0)
vix_color = "#28a745" if vix_val < 20 else ("#ffc107" if vix_val < 30 else "#dc3545")

with col1:
    st.markdown(f"""
    <div class="quick-stat" style="border-left-color: {vix_color};">
        <h4>VIX Index</h4>
        <div class="value" style="color: {vix_color};">{vix_val:.1f}</div>
        <div class="change">{'▲' if vix_change > 0 else '▼'} {abs(vix_change):.1f} (7d)</div>
    </div>
    """, unsafe_allow_html=True)

# Statystyka 2: Yield Curve (recesja)
curve_val = indicators.get('yield_curve', {}).get('current', 0)
curve_color = "#dc3545" if curve_val < 0 else ("#ffc107" if curve_val < 0.5 else "#28a745")

with col2:
    st.markdown(f"""
    <div class="quick-stat" style="border-left-color: {curve_color};">
        <h4>Yield Curve (10Y-2Y)</h4>
        <div class="value" style="color: {curve_color};">{curve_val:.2f}%</div>
        <div class="change">{'Odwrócona 🔴' if curve_val < 0 else ('Płaska 🟡' if curve_val < 0.5 else 'Pozytywna 🟢')}</div>
    </div>
    """, unsafe_allow_html=True)

# Statystyka 3: Rezerwy
reserves_val = indicators.get('reserves', {}).get('current', 0)
reserves_change = indicators.get('reserves', {}).get('change_7d', 0)
reserves_color = "#28a745" if reserves_val > 3000 else ("#ffc107" if reserves_val > 2800 else "#dc3545")

with col3:
    st.markdown(f"""
    <div class="quick-stat" style="border-left-color: {reserves_color};">
        <h4>Bank Reserves</h4>
        <div class="value" style="color: {reserves_color};">${reserves_val:.0f}B</div>
        <div class="change">{'▲' if reserves_change > 0 else '▼'} ${abs(reserves_change):.0f}B (7d)</div>
    </div>
    """, unsafe_allow_html=True)

# Statystyka 4: Liquidity Score
score_color = "#28a745" if score > 40 else ("#4facfe" if score > 0 else ("#ffc107" if score > -40 else "#dc3545"))

with col4:
    st.markdown(f"""
    <div class="quick-stat" style="border-left-color: {score_color};">
        <h4>Liquidity Score</h4>
        <div class="value" style="color: {score_color};">{score:.0f}</div>
        <div class="change">{regime_name}</div>
    </div>
    """, unsafe_allow_html=True)

# === GŁÓWNY DASHBOARD ===
st.markdown('<div class="section-header"><h3>📊 Szczegółowa Analiza</h3></div>', unsafe_allow_html=True)
interpretation = analysis['interpretation']
score = analysis['overall_score']

# Kolorowy header z oceną
if score > 40:
    st.success(f"### {interpretation}")
elif score > 0:
    st.info(f"### {interpretation}")
elif score > -40:
    st.warning(f"### {interpretation}")
else:
    st.error(f"### {interpretation}")

# === INFORMACJA O REŻIMIE RYNKOWYM ===
if 'market_regime' in analysis and analysis['market_regime']:
    regime = analysis['market_regime']

    # Ikona i kolor w zależności od reżimu
    if regime['regime'] == 'RISK_ON':
        regime_icon = "🟢"
        regime_color = "#28a745"
    elif regime['regime'] == 'RISK_OFF':
        regime_icon = "🟡"
        regime_color = "#ffc107"
    else:  # CRISIS
        regime_icon = "🔴"
        regime_color = "#dc3545"

    # Rozszerzone opisy dla każdego reżimu
    regime_details = {
        'RISK_ON': {
            'what_it_means': 'Rynek w trybie "risk-on" - inwestorzy poszukują wyższych zwrotów, są skłonni do ryzyka.',
            'for_you': [
                '✅ Dobry moment na **wzrostowe aktywa** (akcje tech, crypto, emerging markets)',
                '✅ Płynność jest **obfita** - łatwe finansowanie',
                '✅ Volatilność **niska** - stabilne warunki',
                '⚠️ Bądź ostrożny: może to być szczyt euforii (greed)'
            ],
            'watch_out': 'Obserwuj czy VIX nie zaczyna rosnąć lub krzywa się odwraca - to sygnał zmiany reżimu!'
        },
        'RISK_OFF': {
            'what_it_means': 'Rynek w trybie "risk-off" - rosnąca niepewność, inwestorzy stają się ostrożni.',
            'for_you': [
                '⚠️ **Zmniejsz ryzyko** w portfelu - rozważ redukację wzrostowych aktywów',
                '⚠️ Zwiększ **safe-haven**: obligacje, złoto, dolary',
                '⚠️ Sygnały negatywne liczą się teraz **1.3x mocniej**',
                '📊 To może być przejściowe lub początek większego trendu'
            ],
            'watch_out': 'Monitoruj czy nie przejdziemy w KRYZYS (VIX > 30) lub z powrotem do RISK-ON!'
        },
        'CRISIS': {
            'what_it_means': 'ALARM! Ekstremalne napięcia na rynku - panika, strach, gwałtowne ruchy.',
            'for_you': [
                '🔴 **DEFENSYWA TOTALNA** - chroń kapitał!',
                '🔴 Gotówka jest królem - czekaj na lepsze okazje',
                '🔴 Sygnały negatywne liczą się **1.8x mocniej** - ryzyko podwojone!',
                '🔴 Short selling, hedging, ucieczka do bezpiecznych aktywów',
                '💡 To może być też **okazja do kupna** dla odważnych (blood in the streets)'
            ],
            'watch_out': 'Kryzys rzadko trwa długo. Obserwuj VIX, HY spread i krzywą - kiedy złagodzą się, to sygnał odwrotu!'
        }
    }

    details = regime_details.get(regime['regime'], {})

    st.markdown(f"""
    <div style="background-color: {regime_color}22; padding: 15px; border-radius: 10px; border-left: 5px solid {regime_color}; margin: 20px 0;">
        <h4 style="margin: 0; color: {regime_color};">{regime_icon} Reżim Rynkowy: {regime['name']}</h4>
        <p style="margin: 5px 0 10px 0; color: #666;">{regime['description']}</p>
        <p style="margin: 0; font-size: 0.9em;"><strong>Mnożnik sygnałów negatywnych:</strong> {regime['multiplier']}x (pozytywne bez zmiany)</p>
    </div>
    """, unsafe_allow_html=True)

    # Szczegółowe wyjaśnienie
    with st.expander("📖 Co to znaczy dla mnie? (ROZWIŃ)"):
        if details:
            st.markdown(f"**🎯 Co to oznacza:**")
            st.info(details.get('what_it_means', ''))

            st.markdown("**💼 Co robić:**")
            for item in details.get('for_you', []):
                st.markdown(f"{item}")

            st.markdown("**👀 Na co uważać:**")
            st.warning(details.get('watch_out', ''))

    # Triggery reżimu
    with st.expander("🔍 Dlaczego wykryto ten reżim?"):
        st.write("**Sygnały z rynku:**")
        for trigger in regime['triggers']:
            st.write(f"- {trigger}")

    # Scoring breakdown
    if 'raw_score' in analysis:
        raw = analysis['raw_score']
        adjustment = analysis.get('regime_adjustment', 0)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric(
                "Raw Score",
                f"{raw:.1f}",
                help="Surowy wynik przed multiplikatorem reżimu"
            )
        with col_b:
            # Wyjaśnienie dlaczego dostosowanie = 0
            if adjustment == 0 and raw > 0:
                adjustment_help = f"= 0 bo score jest POZYTYWNY ({raw:.1f}). Multiplikator działa TYLKO na negatywne sygnały!"
            elif adjustment == 0 and raw == 0:
                adjustment_help = "Score neutralny, brak dostosowania"
            else:
                adjustment_help = f"Raw score ({raw:.1f}) × Mnożnik ({regime['multiplier']}x) = {adjustment:.1f}"

            st.metric(
                "Dostosowanie",
                f"{adjustment:.1f}",
                help=adjustment_help
            )
        with col_c:
            st.metric(
                "Final Score",
                f"{score:.1f}",
                help=f"Końcowy wynik po zastosowaniu reżimu: {raw:.1f} + {adjustment:.1f} = {score:.1f}"
            )

st.markdown("---")

# === PERCENTYLE HISTORYCZNE ===
if 'percentiles' in analysis and analysis['percentiles']:
    percentiles = analysis['percentiles']

    st.markdown("### 📊 Kontekst Historyczny (Percentyle)")

    with st.expander("📚 CO TO SĄ PERCENTYLE? (kliknij aby przeczytać)", expanded=False):
        st.markdown("""
        ## 🎯 Czym są percentyle historyczne?

        Zamiast pytać "czy VIX = 25 to dużo?", pytamy: **"Jak wysoki jest VIX w porównaniu do ostatnich miesięcy?"**

        ### 📖 Jak to działa?

        **Percentyl** mówi Ci, ile procent historycznych wartości było **niższych** od obecnej.

        **Przykłady:**
        - **VIX = 15 (percentyl 30%)** → Niższy niż 70% historii → Spokojnie, normalnie
        - **VIX = 25 (percentyl 85%)** → Wyższy niż 85% historii → To już wysoko!
        - **VIX = 35 (percentyl 98%)** → Wyższy niż 98% historii → EKSTREMALNIE wysoko!

        ### 🎨 Skala percentyli:

        - 🔴 **95-100%**: EKSTREMALNIE WYSOKI (top 5% historii)
        - 🟡 **75-95%**: WYSOKI (powyżej normy)
        - ⚪ **25-75%**: NORMALNY (typowy zakres)
        - 🟡 **5-25%**: NISKI (poniżej normy)
        - 🔴 **0-5%**: EKSTREMALNIE NISKI (bottom 5% historii)

        ### 💡 Dlaczego to lepsze niż stałe progi?

        **Problem ze stałymi progami:**
        - "VIX > 30 = panika" → Ale 30 w 2020 to norma, a 30 w 2017 to szok!
        - Rynek się zmienia, progi powinny się dostosowywać!

        **Percentyle uwzględniają kontekst:**
        - Porównują obecną wartość do **ostatnich N dni** (np. 365)
        - Automatycznie dostosowują się do zmiennych warunków
        - Dają Ci **relatywny** obraz sytuacji

        **Przykład:**
        - 2020 (COVID): VIX 30 = percentyl 60% (normalny w kryzysie)
        - 2017 (spokój): VIX 30 = percentyl 99% (ekstremalna panika!)

        To samo VIX, ale **zupełnie inny kontekst**!
        """)

    # Wyświetl percentyle dla kluczowych wskaźników
    with st.expander(f"📈 Percentyle wskaźników ({len(percentiles)} dostępnych)", expanded=True):
        # Grupuj po kategoriach
        critical_indicators = ['vix', 'yield_curve', 'reserves', 'nfci', 'hy_spread']
        other_indicators = [k for k in percentiles.keys() if k not in critical_indicators]

        # Kluczowe wskaźniki
        if any(ind in percentiles for ind in critical_indicators):
            st.markdown("**🔥 Kluczowe wskaźniki:**")
            for ind in critical_indicators:
                if ind in percentiles:
                    p = percentiles[ind]
                    percentile = p['percentile']

                    # Kolor paska percentyla
                    if percentile >= 95 or percentile <= 5:
                        bar_color = '#dc3545'  # Czerwony
                    elif percentile >= 75 or percentile <= 25:
                        bar_color = '#ffc107'  # Żółty
                    else:
                        bar_color = '#28a745'  # Zielony

                    st.markdown(f"""
                    <div style="margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <strong>{ind.upper().replace('_', ' ')}</strong>
                            <span style="color: #666;">{p['current']:.2f}</span>
                        </div>
                        <div style="background-color: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                            <div style="background-color: {bar_color}; width: {percentile}%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8em; font-weight: bold;">
                                {percentile:.0f}%
                            </div>
                        </div>
                        <div style="font-size: 0.85em; color: #555; margin-top: 5px;">
                            {p['interpretation']}
                        </div>
                        <div style="font-size: 0.75em; color: #999; margin-top: 3px;">
                            Zakres historyczny: {p['historical_min']:.2f} - {p['historical_max']:.2f} (śr: {p['historical_mean']:.2f})
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Pozostałe wskaźniki
        if other_indicators:
            st.markdown("**📊 Pozostałe wskaźniki:**")
            cols = st.columns(2)
            for idx, ind in enumerate(other_indicators):
                p = percentiles[ind]
                percentile = p['percentile']

                with cols[idx % 2]:
                    if percentile >= 95 or percentile <= 5:
                        status = "🔴"
                    elif percentile >= 75 or percentile <= 25:
                        status = "🟡"
                    else:
                        status = "🟢"

                    st.metric(
                        f"{status} {ind.replace('_', ' ').title()}",
                        f"{p['current']:.2f}",
                        f"Percentyl: {percentile:.0f}%",
                        help=p['interpretation']
                    )

    st.markdown("---")

# === WYKRYTE WZORCE / KORELACJE ===
if 'patterns' in analysis and analysis['patterns']:
    patterns = analysis['patterns']
    total_patterns = (len(patterns.get('conflicts', [])) +
                     len(patterns.get('reinforcements', [])) +
                     len(patterns.get('compound_signals', [])))

    if total_patterns > 0:
        st.markdown("### 🔍 Wykryte Wzorce i Korelacje")

        # LEGENDA - wyjaśnienie co to jest
        with st.expander("📚 CO TO SĄ WZORCE? (kliknij aby przeczytać)", expanded=False):
            st.markdown("""
            ## 🎯 Czym są wzorce i korelacje?

            System analizuje **nie tylko pojedyncze wskaźniki**, ale także **jak działają razem**.
            Czasem dwa wskaźniki razem mówią więcej niż każdy osobno!

            ---

            ### 📖 Typy wzorców:

            #### ⚠️ **KONFLIKTY i PARADOKSY**
            Kiedy wskaźniki się **NIE ZGADZAJĄ** - jeden mówi jedno, drugi coś innego.

            **Przykłady:**
            - 🔸 **Panika mimo płynności**: VIX wysoki (strach!) ale rezerwy wysokie (płynność OK)
              - **Skąd się to wzięło?** Rynek może się bać mimo że fundamenty są dobre
              - **Co to znaczy?** Potencjalna okazja - strach jest przesadzony

            - 🔸 **Spokój mimo napięć** (FALSE CALM): VIX niski (spokój) ale NFCI napięty (problemy!)
              - **Skąd się to wzięło?** Inwestorzy ignorują realne ryzyko
              - **Co to znaczy?** NIEBEZPIECZNE - spokojna powierzchnia, burza pod spodem

            - 🔸 **Fed walczy z recesją**: Krzywa odwrócona (recesja blisko!) ale M2 rośnie (Fed drukuje)
              - **Skąd się to wzięło?** Fed reaguje na złe dane pompując pieniądze
              - **Co to znaczy?** Ratunkowa akcja - bullish dla aktywów (więcej pieniędzy)

            ---

            #### 💪 **WZMOCNIENIA**
            Kiedy **wiele wskaźników mówi TO SAMO** - potężny sygnał!

            **Przykłady:**
            - 🟢 **PERFECT RISK-ON**: VIX niski + NFCI luźny + Krzywa pozytywna + HY Spread niski
              - **Skąd się to wzięło?** Wszystkie miary ryzyka są zielone
              - **Co to znaczy?** Idealne warunki dla akcji, crypto, ryzyka

            - 🔴 **TRIPLE THREAT**: VIX wysoki + Krzywa odwrócona + HY Spread wysoki
              - **Skąd się to wzięło?** Wszystkie alarmy włączone jednocześnie
              - **Co to znaczy?** UCIECZKA! Maksymalna ostrożność, obrona kapitału

            ---

            #### ⚡ **COMPOUND SIGNALS**
            Specjalne kombinacje wskaźników pokazujące **systemowe zjawiska**.

            **Przykłady:**
            - 💰 **LIQUIDITY FLOOD**: Rezerwy rosną + TGA spada + Fed zwiększa bilans + M2 rośnie
              - **Skąd się to wzięło?** Płynność leje się z WIELU źródeł jednocześnie
              - **Co to znaczy?** Fed pompuje system - MEGA BULLISH dla aktywów

            - ⚠️ **LIQUIDITY DRAIN**: Rezerwy spadają + TGA rośnie + RRP spada + Fed BS maleje
              - **Skąd się to wzięło?** Płynność ucieka z wielu źródeł
              - **Co to znaczy?** Fed zacieśnia - BEARISH, mniej pieniędzy w systemie

            - 🚨 **CREDIT CRUNCH**: HY Spread wysoki + SOFR spread wysoki + NFCI napięty
              - **Skąd się to wzięło?** Trudno i drogo pożyczyć pieniądze
              - **Co to znaczy?** Ryzyko zamrożenia kredytu - DEFENSYWA!

            ---

            ### 💡 Dlaczego to ważne?

            **Pojedynczy wskaźnik może kłamać** - może być przejściowy szum, błąd pomiaru, anomalia.

            **Ale gdy 3-4 wskaźniki mówią TO SAMO** - to już nie przypadek! To TREND, ZMIANA, SYGNAŁ!

            **Przykład z życia:**
            - Jeśli tylko termometr pokazuje gorączkę → może być zepsuty
            - Ale jeśli: termometr + ból głowy + kaszel + zmęczenie → TO JEST PRAWDZIWA CHOROBA!

            Tak samo tutaj - **szukamy potwierdzenia z wielu źródeł** zanim damy silny sygnał.

            ---

            ### 📊 Jak czytać wpływ na score?

            - **+20 punktów** = Silny pozytywny sygnał (kupuj ryzyko!)
            - **+10 punktów** = Umiarkowanie pozytywny
            - **0 punktów** = Neutralny/brak wzorca
            - **-10 punktów** = Umiarkowanie negatywny
            - **-25 punktów** = Silny negatywny sygnał (UCIEKAJ!)

            **Łączny wpływ** = suma wszystkich wykrytych wzorców

            Przykład: PERFECT RISK-ON (+15) + LIQUIDITY FLOOD (+20) = **+35 punktów** extra boost!
            """)

        # Konflikty / Paradoksy
        if patterns.get('conflicts'):
            with st.expander(f"⚠️ Konflikty i Paradoksy ({len(patterns['conflicts'])})", expanded=True):
                for conflict in patterns['conflicts']:
                    severity_color = {'low': '#28a745', 'medium': '#ffc107', 'high': '#dc3545'}
                    color = severity_color.get(conflict['severity'], '#6c757d')

                    st.markdown(f"""
                    <div style="background-color: {color}22; padding: 12px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: {color};">{conflict['name']}</h4>
                        <p style="margin: 5px 0; font-size: 0.9em;">{conflict['description']}</p>
                        <p style="margin: 5px 0; font-style: italic; color: #555;">💡 {conflict['interpretation']}</p>
                        <p style="margin: 0; font-size: 0.85em; color: #666;">Wpływ na score: {conflict['score_impact']:+d} punktów</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Wzmocnienia (Reinforcements)
        if patterns.get('reinforcements'):
            with st.expander(f"💪 Wzmocnienia ({len(patterns['reinforcements'])})", expanded=True):
                for reinforcement in patterns['reinforcements']:
                    color = '#28a745' if reinforcement['score_impact'] > 0 else '#dc3545'

                    st.markdown(f"""
                    <div style="background-color: {color}22; padding: 12px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: {color};">{reinforcement['name']}</h4>
                        <p style="margin: 5px 0; font-size: 0.9em;">{reinforcement['description']}</p>
                        <p style="margin: 5px 0; font-style: italic; color: #555;">💡 {reinforcement['interpretation']}</p>
                        <p style="margin: 0; font-size: 0.85em; color: #666;">Siła: {reinforcement['strength']} sygnałów | Wpływ: {reinforcement['score_impact']:+d} punktów</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Compound Signals
        if patterns.get('compound_signals'):
            with st.expander(f"⚡ Compound Signals ({len(patterns['compound_signals'])})", expanded=True):
                for compound in patterns['compound_signals']:
                    color = '#28a745' if compound['score_impact'] > 0 else '#dc3545'

                    st.markdown(f"""
                    <div style="background-color: {color}22; padding: 12px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: {color};">{compound['name']}</h4>
                        <p style="margin: 5px 0; font-size: 0.9em;">{compound['description']}</p>
                        <p style="margin: 5px 0; font-style: italic; color: #555;">💡 {compound['interpretation']}</p>
                        <p style="margin: 0; font-size: 0.85em; color: #666;">Komponenty: {compound['components']} | Wpływ: {compound['score_impact']:+d} punktów</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Podsumowanie wpływu
        total_impact = patterns.get('score_adjustments', 0)
        if total_impact != 0:
            impact_color = '#28a745' if total_impact > 0 else '#dc3545'
            st.markdown(f"""
            <div style="background-color: {impact_color}11; padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px;">
                <strong>Łączny wpływ korelacji na score:</strong> <span style="color: {impact_color}; font-size: 1.2em; font-weight: bold;">{total_impact:+d} punktów</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

# Score gauge
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Ocena Płynności", 'font': {'size': 24}},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-100, -40], 'color': '#ffcccc'},
                {'range': [-40, 0], 'color': '#ffe6cc'},
                {'range': [0, 40], 'color': '#e6f3ff'},
                {'range': [40, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# === KLUCZOWE METRYKI ===

st.markdown("### 📈 Kluczowe Wskaźniki")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if 'reserves' in indicators:
        create_metric_card(
            "Rezerwy Banków",
            indicators['reserves']['current'],
            indicators['reserves']['change_7d']
        )

with col2:
    if 'tga' in indicators:
        create_metric_card(
            "TGA",
            indicators['tga']['current'],
            indicators['tga']['change_7d'],
            inverse=True
        )

with col3:
    if 'reverse_repo' in indicators:
        create_metric_card(
            "Reverse Repo",
            indicators['reverse_repo']['current'],
            indicators['reverse_repo']['change_7d']
        )

with col4:
    if 'fed_balance' in indicators:
        create_metric_card(
            "Bilans Fed",
            indicators['fed_balance']['current'],
            indicators['fed_balance']['change_7d']
        )

# Dodatkowe metryki stóp procentowych
col5, col6, col7, col8 = st.columns(4)

with col5:
    if 'sofr' in indicators:
        create_metric_card(
            "SOFR",
            indicators['sofr']['current'],
            indicators['sofr']['change_7d'],
            unit="%"
        )

with col6:
    if 'iorb' in indicators:
        create_metric_card(
            "IORB",
            indicators['iorb']['current'],
            indicators['iorb']['change_7d'],
            unit="%"
        )

with col7:
    if 'effr' in indicators:
        create_metric_card(
            "EFFR",
            indicators['effr']['current'],
            indicators['effr']['change_7d'],
            unit="%"
        )

with col8:
    if 'sofr' in indicators and 'iorb' in indicators:
        spread = indicators['sofr']['current'] - indicators['iorb']['current']
        prev_spread = (indicators['sofr']['current'] - indicators['sofr']['change_7d']) - \
                      (indicators['iorb']['current'] - indicators['iorb']['change_7d'])
        spread_change = spread - prev_spread
        st.metric(
            label="SOFR-IORB Spread",
            value=f"{spread:.2f}%",
            delta=f"{spread_change:+.2f}%",
            delta_color="inverse"
        )

# === TIER 1 - NOWE WSKAŹNIKI ===

st.markdown("### 🎯 Tier 1 Indicators (Expanded)")

col9, col10, col11, col12, col13, col14 = st.columns(6)

with col9:
    if 'reserves_alt' in indicators:
        create_metric_card(
            "Rezerwy (WRESBAL)",
            indicators['reserves_alt']['current'],
            indicators['reserves_alt']['change_7d']
        )

with col10:
    if 'm2' in indicators:
        m2_value = indicators['m2']['current']
        m2_change = indicators['m2']['change_7d']
        st.metric(
            label="M2 Money Supply",
            value=f"${m2_value:.0f}B",
            delta=f"${m2_change:+.0f}B"
        )

with col11:
    if 'yield_curve' in indicators:
        curve = indicators['yield_curve']['current']
        curve_change = indicators['yield_curve']['change_7d']
        st.metric(
            label="10Y-2Y Spread",
            value=f"{curve:.2f}%",
            delta=f"{curve_change:+.2f}%",
            delta_color="normal" if curve > 0 else "inverse"
        )

with col12:
    if 'vix' in indicators:
        vix = indicators['vix']['current']
        vix_change = indicators['vix']['change_7d']
        st.metric(
            label="VIX",
            value=f"{vix:.1f}",
            delta=f"{vix_change:+.1f}",
            delta_color="inverse"
        )

with col13:
    if 'fin_conditions' in indicators:
        nfci = indicators['fin_conditions']['current']
        nfci_change = indicators['fin_conditions']['change_7d']
        st.metric(
            label="NFCI",
            value=f"{nfci:.2f}",
            delta=f"{nfci_change:+.2f}",
            delta_color="inverse"
        )

with col14:
    if 'dollar_index' in indicators:
        dxy = indicators['dollar_index']['current']
        dxy_change = indicators['dollar_index']['change_7d']
        st.metric(
            label="Dollar Index (DXY)",
            value=f"{dxy:.1f}",
            delta=f"{dxy_change:+.1f}",
            delta_color="inverse"
        )

st.markdown("---")

# === ALERTY ===

if analysis['alerts']:
    st.markdown("### ⚠️ Alerty")
    for alert in analysis['alerts']:
        severity = alert['severity']
        message = alert['message']
        if severity == 'critical':
            st.error(f"🚨 **KRYTYCZNE**: {message}")
        elif severity == 'warning':
            st.warning(f"⚠️ **OSTRZEŻENIE**: {message}")

# === SYGNAŁY ===

if analysis['signals']:
    st.markdown("### 📍 Sygnały Rynkowe")

    signal_cols = st.columns(3)
    for idx, signal in enumerate(analysis['signals']):
        with signal_cols[idx % 3]:
            signal_type = signal['type']
            message = signal['message']

            if signal_type == 'positive':
                st.success(f"🟢 {message}")
            elif signal_type == 'negative':
                st.error(f"🔴 {message}")
            else:
                st.info(f"🟡 {message}")

st.markdown("---")

# === ZAKŁADKI Z WYKRESAMI ===

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Wszystkie Wykresy", "🎯 Tier 1 Indicators", "📈 Pojedyncze Wskaźniki", "📋 Dane Tabelaryczne", "🔔 Alerty", "📚 Słownik Pojęć"])

with tab1:
    st.markdown("### Wszystkie Wskaźniki na Jednym Wykresie")
    multi_chart = create_multi_indicator_chart(indicators)
    st.plotly_chart(multi_chart, use_container_width=True)

with tab2:
    st.markdown("### Tier 1 Indicators - Extended Analysis")
    st.info("""
    **Tier 1 Indicators** to najważniejsze wskaźniki makroekonomiczne:
    - **M2 Money Supply**: Podaż pieniądza
    - **10Y-2Y Yield Curve**: Krzywa dochodowości (ujemna = recesja!)
    - **VIX**: Indeks strachu na rynku
    - **NFCI**: Warunki finansowe (>0 = napięcia)
    - **Dollar Index (DXY)**: Siła dolara
    - **Rezerwy (WRESBAL)**: Alternatywna miara rezerw bankowych
    """)
    tier1_chart = create_tier1_charts(indicators)
    st.plotly_chart(tier1_chart, use_container_width=True)

with tab3:
    st.markdown("### Wybierz Wskaźnik do Analizy")

    indicator_options = {
        '=== PODSTAWOWE ===': None,
        'Rezerwy Banków': 'reserves',
        'Rezerwy (WRESBAL)': 'reserves_alt',
        'TGA': 'tga',
        'Reverse Repo': 'reverse_repo',
        'Bilans Fed': 'fed_balance',
        'SOFR': 'sofr',
        'IORB': 'iorb',
        'EFFR': 'effr',
        '=== TIER 1 ===': None,
        'M2 Money Supply': 'm2',
        '10Y-2Y Yield Curve': 'yield_curve',
        'VIX': 'vix',
        'NFCI Financial Conditions': 'fin_conditions',
        'Dollar Index (DXY)': 'dollar_index',
        '=== TIER 2 ===': None,
        '10-Year Treasury': 'treasury_10y',
        '2-Year Treasury': 'treasury_2y',
        '5Y Breakeven Inflation': 'inflation_5y',
        'High Yield Spread': 'hy_spread',
        'Unemployment Rate': 'unemployment'
    }

    # Filtruj None values
    indicator_options = {k: v for k, v in indicator_options.items() if v is not None}

    selected_indicator = st.selectbox(
        "Wybierz wskaźnik:",
        options=list(indicator_options.keys())
    )

    chart = create_time_series_chart(
        indicators,
        indicator_options[selected_indicator],
        selected_indicator
    )

    if chart:
        st.plotly_chart(chart, use_container_width=True)

        # Statystyki
        data = indicators[indicator_options[selected_indicator]]['data']
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Min", f"{data['value'].min():.2f}")
        with col2:
            st.metric("Max", f"{data['value'].max():.2f}")
        with col3:
            st.metric("Średnia", f"{data['value'].mean():.2f}")
        with col4:
            st.metric("Std Dev", f"{data['value'].std():.2f}")

with tab4:
    st.markdown("### Dane Historyczne")

    # Wybór wskaźnika
    selected_for_table = st.selectbox(
        "Wybierz wskaźnik do wyświetlenia:",
        options=list(indicator_options.keys()),
        key="table_selector"
    )

    data = indicators[indicator_options[selected_for_table]]['data'].copy()
    data['date'] = data['date'].dt.strftime('%Y-%m-%d')
    data = data.sort_values('date', ascending=False)

    st.dataframe(data, use_container_width=True, height=400)

    # Eksport do CSV
    csv = data.to_csv(index=False)
    st.download_button(
        label="📥 Pobierz CSV",
        data=csv,
        file_name=f"{selected_for_table}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    # Eksport wszystkich danych
    all_data = {}
    for name, ind_data in indicators.items():
        df = ind_data['data'].copy()
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        all_data[name] = df

    # JSON export
    json_data = json.dumps({
        'timestamp': datetime.now().isoformat(),
        'analysis': {
            'score': analysis['overall_score'],
            'interpretation': analysis['interpretation'],
        },
        'indicators': {
            name: data.to_dict('records')
            for name, data in all_data.items()
        }
    }, indent=2)

    st.download_button(
        label="📥 Pobierz wszystkie dane (JSON)",
        data=json_data,
        file_name=f"liquidity_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

with tab5:
    st.markdown("### 🔔 Ustawienia Alertów")

    st.info("""
    Skonfiguruj powiadomienia, które będą wysyłane gdy warunki płynności się pogorszą.
    """)

    alert_email = st.text_input(
        "Email do powiadomień",
        value=st.session_state.alert_email,
        placeholder="twoj@email.com"
    )

    alert_threshold = st.slider(
        "Próg alertu (score)",
        min_value=-100,
        max_value=0,
        value=-30,
        help="Wyślij alert gdy score spadnie poniżej tej wartości"
    )

    if st.button("💾 Zapisz ustawienia alertów"):
        st.session_state.alert_email = alert_email
        save_alert_settings(alert_email, alert_threshold)
        st.success("✅ Ustawienia zapisane!")

    # Sprawdź czy wysłać alert
    if alert_email and analysis['overall_score'] < alert_threshold:
        check_and_send_alerts(analysis, alert_email)

    # Historia alertów
    st.markdown("### 📜 Historia Alertów")

    if os.path.exists('alert_log.json'):
        alerts_history = []
        with open('alert_log.json', 'r') as f:
            for line in f:
                alerts_history.append(json.loads(line))

        if alerts_history:
            df_alerts = pd.DataFrame(alerts_history)
            df_alerts = df_alerts.sort_values('timestamp', ascending=False)
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("Brak alertów w historii")
    else:
        st.info("Brak alertów w historii")

with tab6:
    st.markdown("### 📚 Słownik Pojęć - Przewodnik dla Początkujących")

    st.info("""
    👋 **Witaj!** Ten słownik wyjaśnia wszystkie wskaźniki w prostych słowach, bez żargonu finansowego.
    Każdy wskaźnik ma wyjaśnienie "co to jest" i "jak to rozumieć".
    """)

    # Podstawowe pojęcia
    with st.expander("🎯 PODSTAWOWE POJĘCIA"):
        st.markdown("""
        ### Czym jest płynność?

        **Płynność** = ile pieniędzy krąży w systemie finansowym.

        - **Dużo płynności** 💰 = dużo pieniędzy → akcje/Bitcoin rosną
        - **Mało płynności** 💸 = mało pieniędzy → akcje/Bitcoin spadają

        Fed (bank centralny USA) kontroluje ile pieniędzy jest w systemie.

        ---

        ### Score płynności (-100 do +100)

        - **+40 do +100**: 🟢 **RISK-ON** - Kup akcje/Bitcoin!
        - **0 do +40**: 🟡 **NEUTRALNE** - Spokój
        - **-40 do 0**: 🟠 **UWAGA** - Ostrożnie!
        - **-100 do -40**: 🔴 **RISK-OFF** - Sprzedaj, zejdź do gotówki!
        """)

    # Podstawowe wskaźniki
    with st.expander("📊 PODSTAWOWE WSKAŹNIKI"):
        st.markdown("""
        ### 1. 💰 Rezerwy Banków (Bank Reserves)

        **Co to jest?**
        - Gotówka którą banki trzymają w Fed (banku centralnym)
        - Im więcej = więcej pieniędzy do pożyczania

        **Jak rozumieć?**
        - **> 3000 mld**: 🟢 Dużo płynności - banki mają kasę
        - **< 2800 mld**: 🔴 Za mało - ryzyko problemów

        ---

        ### 2. 🏛️ TGA - Treasury General Account

        **Co to jest?**
        - Konto rządu USA w Fed
        - Gdy rząd płaci (emerytury, kontrakty) = kasa z TGA idzie do ludzi

        **Jak rozumieć?**
        - **TGA rośnie**: 🔴 Rząd zabiera pieniądze z rynku (podatki)
        - **TGA spada**: 🟢 Rząd wpompowuje pieniądze do rynku

        ---

        ### 3. 🔄 Reverse Repo (RRP)

        **Co to jest?**
        - Miejsce gdzie firmy "parkują" nadmiar gotówki na noc
        - Jak "parkingnoc dla pieniędzy" w Fed

        **Jak rozumieć?**
        - **Wysoki RRP (>500B)**: 🟢 Jest rezerwa płynności
        - **Niski RRP (<100B)**: 🔴 Brak bufora bezpieczeństwa

        ---

        ### 4. 📈 Bilans Fed (Fed Balance Sheet)

        **Co to jest?**
        - Suma wszystkich aktywów Fed (obligacje, które kupił)
        - Fed kupuje = drukuje pieniądze (QE)
        - Fed sprzedaje = zabiera pieniądze (QT)

        **Jak rozumieć?**
        - **Bilans rośnie**: 🟢 Fed drukuje $ (QE) - akcje/BTC rosną!
        - **Bilans spada**: 🔴 Fed zabiera $ (QT) - akcje/BTC spadają
        """)

    # Tier 1
    with st.expander("🎯 TIER 1 INDICATORS - Makroekonomia"):
        st.markdown("""
        ### 5. 💵 M2 Money Supply

        **Co to jest?**
        - Suma wszystkich pieniędzy w gospodarce (gotówka + konta bankowe)
        - Najważniejszy wskaźnik podaży pieniądza

        **Jak rozumieć?**
        - **M2 rośnie**: 🟢 Więcej $ w obiegu → inflacja → Bitcoin/złoto rosną
        - **M2 spada**: 🔴 Mniej $ → deflacja → wszystko spada

        **Obecnie**: ~22 bilionów $

        ---

        ### 6. 📉 Krzywa Dochodowości 10Y-2Y

        **Co to jest?**
        - Różnica między stopą 10-letnią a 2-letnią obligacji USA
        - Najlepszy wskaźnik recesji!

        **Jak rozumieć?**
        - **> 1%**: 🟢 Stroma krzywa = gospodarka rośnie
        - **0-1%**: 🟡 Płaska = spowolnienie
        - **< 0% (INWERSJA)**: 🔴 Recesja za 12-18 miesięcy! (sprawdza się w 100%)

        **Dlaczego?** Gdy 2Y > 10Y = inwestorzy spodziewają się że Fed obniży stopy bo będzie recesja.

        ---

        ### 7. 😱 VIX - Indeks Strachu

        **Co to jest?**
        - Mierzy jak bardzo inwestorzy się boją
        - "Termometr paniki" na giełdzie

        **Jak rozumieć?**
        - **> 30**: 🔴 PANIKA! Wszyscy się boją
        - **20-30**: 🟠 Podwyższona niepewność
        - **15-20**: 🟢 Normalny poziom
        - **< 15**: 💚 Wszyscy zadowoleni (może za bardzo?)

        **Obecnie**: ~22 = lekka niepewność

        ---

        ### 8. 🏦 NFCI - Warunki Finansowe

        **Co to jest?**
        - Kompleksowy wskaźnik Chicago Fed
        - Mierzy czy kredyt jest łatwy czy trudny do zdobycia

        **Jak rozumieć?**
        - **> 0**: 🔴 Napięte warunki - trudno dostać kredyt
        - **< -0.5**: 🟢 Bardzo luźne - każdy może pożyczyć
        - **-0.5 do 0**: 🟡 Normalne

        ---

        ### 9. 💵 Dollar Index (DXY)

        **Co to jest?**
        - Siła dolara vs inne waluty (euro, jen, funt)
        - Gdy DXY rośnie = dolar się wzmacnia

        **Jak rozumieć?**
        - **> 125**: 🔴 Bardzo silny dolar = zabiera płynność ze świata
        - **100-125**: 🟡 Normalny
        - **< 100**: 🟢 Słaby dolar = płynność dla świata (Bitcoin rośnie!)

        **Dlaczego?** Gdy dolar mocny → inne kraje tracą $ → mniej płynności globalnie
        """)

    # Tier 2
    with st.expander("📊 TIER 2 INDICATORS - Zaawansowane"):
        st.markdown("""
        ### 10. 📈 10-Year Treasury Rate

        **Co to jest?**
        - Oprocentowanie 10-letniej obligacji USA
        - "Benchmark" rynku - wszystko się od tego liczy

        **Jak rozumieć?**
        - **> 5%**: 🔴 Wysokie stopy = drogi kredyt = akcje spadają
        - **2-4%**: 🟡 Normalny zakres
        - **< 2%**: 🟢 Niskie stopy = tani kredyt = akcje rosną

        ---

        ### 11. 💳 High Yield Spread

        **Co to jest?**
        - Różnica między "junk bonds" (ryzykowne) a bezpiecznymi obligacjami
        - Mierzy apetyt na ryzyko

        **Jak rozumieć?**
        - **> 5%**: 🔴 Strach! Nikt nie chce ryzyka
        - **3-5%**: 🟡 Normalny
        - **< 3%**: 🟢 Wszyscy chcą ryzyka (Bitcoin czas!)

        ---

        ### 12. 🔥 5Y Breakeven Inflation

        **Co to jest?**
        - Jaka inflacja jest oczekiwana za 5 lat
        - Wyliczona z cen obligacji

        **Jak rozumieć?**
        - **> 3%**: 🔴 Rynek spodziewa się wysokiej inflacji
        - **2-3%**: 🟢 Zdrowa inflacja (cel Fed = 2%)
        - **< 1.5%**: 🔴 Ryzyko deflacji

        ---

        ### 13. 👔 Unemployment Rate

        **Co to jest?**
        - % ludzi bez pracy
        - Wskaźnik zdrowia gospodarki

        **Jak rozumieć?**
        - **> 5%**: 🔴 Słaba gospodarka
        - **4-5%**: 🟡 OK
        - **< 4%**: 🟢 Mocna gospodarka

        **Uwaga**: Zbyt niskie (<3.5%) może oznaczać przegrzanie gospodarki!
        """)

    # Stopy procentowe
    with st.expander("💰 STOPY PROCENTOWE - SOFR, IORB, EFFR"):
        st.markdown("""
        ### SOFR - Secured Overnight Financing Rate

        **Co to jest?**
        - Stopa procentowa na którą banki pożyczają sobie $ na noc
        - Zastąpiła LIBOR jako główny benchmark

        **Obecnie**: ~4.0%

        ---

        ### IORB - Interest on Reserve Balances

        **Co to jest?**
        - Ile Fed płaci bankom za trzymanie $ w rezerwie
        - Ustalona przez Fed

        **Obecnie**: ~3.9%

        ---

        ### SOFR-IORB Spread

        **Co to jest?**
        - Różnica SOFR - IORB
        - Mierzy napięcie w systemie bankowym

        **Jak rozumieć?**
        - **> 0.20%**: 🔴 NAPIĘCIE! Bankom brakuje płynności
        - **0.10-0.20%**: 🟠 Ostrzeżenie
        - **< 0.10%**: 🟢 Wszystko OK
        """)

    # Praktyczne wskazówki
    with st.expander("💡 JAK TO WSZYSTKO WYKORZYSTAĆ?"):
        st.markdown("""
        ### Strategia dla początkujących:

        **1. Sprawdź Score płynności:**
        - **> 40**: Kup akcje/Bitcoin
        - **< -40**: Sprzedaj, zejdź do gotówki

        **2. Obserwuj 3 najważniejsze:**
        - **Krzywa 10Y-2Y**: Czy jest inwersja? (recesja!)
        - **Bilans Fed**: Czy rośnie czy spada?
        - **VIX**: Czy ludzie się boją?

        **3. Długoterminowa strategia:**
        - **M2 rośnie**: Trzymaj Bitcoin/złoto (zabezpieczenie przed inflacją)
        - **M2 spada**: Trzymaj gotówkę

        **4. Czerwone flagi (SPRZEDAJ!):**
        - ✖️ Krzywa odwrócona (10Y-2Y < 0)
        - ✖️ VIX > 30
        - ✖️ Bilans Fed spada szybko
        - ✖️ SOFR-IORB spread > 0.20%

        **5. Zielone światła (KUP!):**
        - ✅ Score > 40
        - ✅ Bilans Fed rośnie
        - ✅ VIX < 20
        - ✅ M2 rośnie
        """)

st.markdown("---")
st.markdown("### 💡 Wskazówki")
st.markdown("""
- **Score > 40**: 🟢 RISK-ON - Warunki sprzyjają wzrostom (Nasdaq/BTC)
- **Score 0-40**: 🟡 NEUTRALNE - Umiarkowane warunki
- **Score -40-0**: 🟠 UWAGA - Pogarszające się warunki
- **Score < -40**: 🔴 RISK-OFF - Napięcia w płynności
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Liquidity Monitor v1.0 | Dane z <a href='https://fred.stlouisfed.org/' target='_blank'>FRED</a></p>
</div>
""", unsafe_allow_html=True)
