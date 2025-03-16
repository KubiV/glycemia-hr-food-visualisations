import streamlit as st
import pandas as pd
import plotly.express as px
import os

#streamlit run glucose_hr_food.py

st.title('Glykémie a tepová frekvence v čase')

# Načtení dat
@st.cache_data
def load_data():
    # Načtení dat tepové frekvence
    try:
        hr_df = pd.read_csv('hr.csv')
        hr_df['timestamp'] = pd.to_datetime(hr_df['date'])
        hr_df = hr_df.rename(columns={'heartrate': 'heart_rate'})
    except Exception as e:
        st.error(f'Chyba při načítání souboru hr-output.csv: {e}')
        return None, None, None

    # Načtení dat glykémie
    try:
        glucose_df = pd.read_csv('glc.csv')
        # Spojení sloupců s glykémií (historie a skenování)
        glucose_df['glucose_value'] = glucose_df['Historie údajů o glukóze mmol/L'].str.replace(',', '.').astype(float).fillna(
            glucose_df['Skenovat glukózu mmol/L'].str.replace(',', '.').astype(float)
        )
        # Převod časové značky
        glucose_df['timestamp'] = pd.to_datetime(glucose_df['Časová značka zařízení'], format='%d-%m-%Y %H:%M')

        # Odstranění duplicitních záznamů a seřazení podle času
        glucose_df = glucose_df.sort_values('timestamp').drop_duplicates(subset=['timestamp', 'glucose_value'])

        # Vytvoření sloupce pro značení jídla
        glucose_df['has_food'] = glucose_df['Karbohydráty (gramy)'].notna() | glucose_df['Karbohydráty (porce)'].notna()

    except Exception as e:
        st.error(f'Chyba při načítání souboru glucose.csv: {e}')
        return None, None, None

    # Načtení dat o jídle
    try:
        food_df = pd.read_csv('food.csv')

        # Převod českých názvů dnů na anglické
        day_mapping = {
            'Pondělí': 'Monday', 'Úterý': 'Tuesday', 'Středa': 'Wednesday',
            'Čtvrtek': 'Thursday', 'Pátek': 'Friday', 'Sobota': 'Saturday',
            'Neděle': 'Sunday'
        }

        # Upravení formátu data
        food_df['datum'] = food_df['datum'].apply(lambda x: ' '.join(x.split()[1:]) if any(day in x for day in day_mapping.keys()) else x)

        # Spojení data a času a převod na timestamp
        food_df['timestamp'] = pd.to_datetime(food_df['datum'] + ' ' + food_df['cas'],
                                            format='%d.%m.%Y %H:%M')

        # Odstranění řádků s 0 kaloriemi
        food_df = food_df[food_df['kcal'] > 0]

    except Exception as e:
        st.error(f'Chyba při načítání souboru food_table_converted.csv: {e}')
        return None, None, None

    return hr_df, glucose_df, food_df

hr_data, glucose_data, food_data = load_data()

if hr_data is not None and glucose_data is not None and food_data is not None:
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

    # Filtrování dat jídla podle vybraného data
    food_filtered = food_data[food_data['timestamp'].dt.date == selected_date]

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

    # Přidání značek pro jídlo
    food_data = glucose_filtered[glucose_filtered['has_food']]
    if not food_data.empty:
        fig.add_scatter(
            x=food_data['timestamp'],
            y=[7] * len(food_data),  # Konstantní Y pozice pro značky
            mode='markers',
            name='Jídlo',
            marker=dict(
                symbol='triangle-down',
                size=15,
                color='green'
            ),
            yaxis='y2'
        )

    # Přidání bodů pro jídlo s informacemi
    if not food_filtered.empty:
        fig.add_scatter(
            x=food_filtered['timestamp'],
            y=[0] * len(food_filtered),  # Umístění na spodní část grafu
            mode='markers+text',
            name='Jídlo',
            marker=dict(
                symbol='triangle-up',
                size=food_filtered['kcal'] / 20,  # Velikost podle kalorií
                color='orange',
            ),
            text=food_filtered['nazev_jidla'],
            textposition="top center",
            yaxis='y3',
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "Čas: %{x}<br>" +
                "Kalorie: %{customdata[0]:.0f} kcal<br>" +
                "Sacharidy: %{customdata[1]:.1f} g<br>" +
                "Cukry: %{customdata[2]:.1f} g<br>" +
                "<extra></extra>"
            ),
            customdata=food_filtered[['kcal', 'sacharidy_g', 'cukry_g']]
        )

    # Úprava layoutu grafu
    fig.update_layout(
        title='Glykémie, tepová frekvence a jídlo',
        xaxis_title='Čas',
        yaxis_title='Tepová frekvence (tepy/min)',
        yaxis2=dict(
            title='Glykémie (mmol/L)',
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title='Jídlo',
            overlaying='y',
            side='left',
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, 1]  # Rozsah pro správné umístění značek jídla
        ),
        hovermode='x unified',
        showlegend=True,
        height=800  # Zvětšení výšky grafu pro lepší čitelnost
    )

    # Zobrazení grafu
    st.plotly_chart(fig, use_container_width=True)

