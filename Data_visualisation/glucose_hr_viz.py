import streamlit as st
import pandas as pd
import plotly.express as px
import os

#streamlit run glucose_hr_viz.py

st.title('Glykémie a tepová frekvence v čase')

# Načtení dat
@st.cache_data
def load_data():
    # Načtení dat tepové frekvence
    try:
        hr_df = pd.read_csv('hr-output.csv')
        hr_df['timestamp'] = pd.to_datetime(hr_df['date'])
        hr_df = hr_df.rename(columns={'heartrate': 'heart_rate'})
    except Exception as e:
        st.error(f'Chyba při načítání souboru hr-output.csv: {e}')
        return None, None

    # Načtení dat glykémie
    try:
        glucose_df = pd.read_csv('glucose.csv')
        # Spojení sloupců s glykémií (historie a skenování)
        glucose_df['glucose_value'] = glucose_df['Historie údajů o glukóze mmol/L'].str.replace(',', '.').astype(float).fillna(
            glucose_df['Skenovat glukózu mmol/L'].str.replace(',', '.').astype(float)
        )
        # Převod časové značky
        glucose_df['timestamp'] = pd.to_datetime(glucose_df['Časová značka zařízení'], format='%d-%m-%Y %H:%M')

        # Odstranění duplicitních záznamů a seřazení podle času
        glucose_df = glucose_df.sort_values('timestamp').drop_duplicates(subset=['timestamp', 'glucose_value'])
    except Exception as e:
        st.error(f'Chyba při načítání souboru glucose.csv: {e}')
        return None, None

    return hr_df, glucose_df

hr_data, glucose_data = load_data()

if hr_data is not None and glucose_data is not None:
    # Získání unikátních dnů z obou datasetů
    all_dates = pd.concat([
        hr_data['timestamp'].dt.date,
        glucose_data['timestamp'].dt.date
    ]).unique()

    # Widget pro výběr data
    selected_date = st.date_input(
        "Vyberte datum",
        min_value=min(all_dates),
        max_value=max(all_dates),
        value=min(all_dates)
    )

    # Filtrování dat podle vybraného data
    hr_filtered = hr_data[hr_data['timestamp'].dt.date == selected_date]
    glucose_filtered = glucose_data[glucose_data['timestamp'].dt.date == selected_date]

    # Vytvoření grafu
    fig = px.line()

    # Přidání křivky tepové frekvence
    fig.add_scatter(
        x=hr_filtered['timestamp'],
        y=hr_filtered['heart_rate'],
        name='Tepová frekvence',
        line_color='red',
        #mode='lines+markers',  # Přidání bodů
        #marker=dict(size=6),   # Velikost bodů
        connectgaps=True       # Propojení mezer v datech
    )

    # Přidání křivky glykémie
    fig.add_scatter(
        x=glucose_filtered['timestamp'],
        y=glucose_filtered['glucose_value'],
        name='Glykémie',
        line_color='blue',
        yaxis='y2',
        #mode='lines+markers',  # Přidání bodů
        #marker=dict(size=6),   # Velikost bodů
        connectgaps=True,      # Propojení mezer v datech
        line=dict(shape='linear')  # Lineární propojení bodů
    )

    # Úprava layoutu grafu
    fig.update_layout(
        title='Glykémie a tepová frekvence',
        xaxis_title='Čas',
        yaxis_title='Tepová frekvence (tepy/min)',
        yaxis2=dict(
            title='Glykémie (mmol/L)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified'  # Lepší zobrazení hodnot při najetí myší
    )

    # Zobrazení grafu
    st.plotly_chart(fig, use_container_width=True)

