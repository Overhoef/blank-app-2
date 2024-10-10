import streamlit as st
import pandas as pd
import matplotlib as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

df = pd.read_csv('schedule_airport.csv')
file_path = '/Users/olavverhoef/Desktop/Minor/Case3/blank-app-1/airports-extended-clean.csv'
airports = pd.read_csv(file_path, sep=';')


#homepage
st.title("🛫 VLUCHTEN 🛬")


st.subheader('Kaart van alle luchthavens')

airports_filtered = airports[airports['Type'] == 'airport']

airports_filtered['Latitude'] = airports_filtered['Latitude'].str.replace(',', '.', regex=False)
airports_filtered['Latitude'] = airports_filtered['Latitude'].astype(float)
airports_filtered['Longitude'] = airports_filtered['Longitude'].str.replace(',', '.', regex=False)
airports_filtered['Longitude'] = airports_filtered['Longitude'].astype(float)

airports_filtered['ICAO_First_Letter'] = airports_filtered['ICAO'].str[0]

# Count the occurrences of each first letter
icao_first_letter_counts = airports_filtered['ICAO_First_Letter'].value_counts()

# Get a list of Viridis colors (adjust the number as needed)
inferno_colors = px.colors.sequential.Inferno[:10]  # Example: Take the first 10 colors

# Create the colormap
colormap = {}
for letter, count in icao_first_letter_counts.items():
    if count > 3:
        # Calculate a color index within the available color list range
        color_index = count % len(inferno_colors)
        colormap[letter] = inferno_colors[color_index]
    else:
        colormap[letter] = 'black'  # Black for less frequent letters

# Create the scatter plot with color based on ICAO_First_Letter
fig = px.scatter_geo(
    airports_filtered,
    lat='Latitude',
    lon='Longitude',
    hover_name='Name',
    hover_data={'City': True, 'Country': True, 'IATA': True, 'ICAO': True},
    projection='natural earth',
    color='ICAO_First_Letter',
    color_discrete_map=colormap,
)

fig.update_layout(
    height=800,
    margin={"r":0,"t":0,"l":0,"b":0},
    geo=dict(
        showland=True,
        landcolor="rgb(240, 240, 240)",
        coastlinecolor="black",
        projection_type='natural earth',
        bgcolor='darkgrey'
    )
)

st.plotly_chart(fig, use_container_width=True)

#Tabs
delays, data_notes = st.tabs(["vertraging", "notities"])

#tab vertraging
with delays:
    st.header('Vertraging Info')
    # Formatting 
    df["STA_STD_ltc"] = pd.to_datetime(df["STA_STD_ltc"], errors='coerce')
    df["ATA_ATD_ltc"] = pd.to_datetime(df["ATA_ATD_ltc"], errors='coerce')

    # Verwijderen van de vluchten met missende tijden
    df = df.dropna(subset=["ATA_ATD_ltc"])

    
    airports = df["Org/Des"].unique()

    # Selectbox voor de luchthavens
    selected_airport = st.selectbox("Selecteer een luchthaven om vertraging percentages te gaan vergelijken:", airports)

    # Filteren van de luchthavens
    filtered_df = df[df["Org/Des"] == selected_airport]

    # checkbox show code
    show_outbound = st.checkbox("Toon vertrekkende vluchten (S)", value=True)
    show_inbound = st.checkbox("Toon aankomende vluchten (L)", value=True)

    # Filters van outbound of inbound vlucht gemaakt met checkboxen
    if show_outbound and not show_inbound:
        filtered_df = filtered_df[filtered_df["LSV"] == "S"]
    elif show_inbound and not show_outbound:
        filtered_df = filtered_df[filtered_df["LSV"] == "L"]
    elif not show_outbound and not show_inbound:
        filtered_df = filtered_df.iloc[0:0]

    # Slider code tot 1 uur te wijzigen
    delay_minutes = st.slider("Marge van optijd aanpassen in minuten", min_value=0, max_value=60, value=0)

    # Slider code 
    filtered_df["Adjusted_STA_STD_ltc"] = filtered_df["STA_STD_ltc"] + pd.to_timedelta(delay_minutes, unit='m')

    # Originele status balk code
    filtered_df["Original_Status"] = filtered_df.apply(
        lambda row: "Op tijd" if row["ATA_ATD_ltc"] <= row["STA_STD_ltc"] else "Te laat", axis=1
    )

    # Verandere status balk code
    filtered_df["Adjusted_Status"] = filtered_df.apply(
        lambda row: "Op tijd" if row["ATA_ATD_ltc"] <= row["Adjusted_STA_STD_ltc"] else "Te laat", axis=1
    )

    # Rekensom van de gefilterde vluchten
    on_time_original = len(filtered_df[filtered_df["Original_Status"] == "Op tijd"])
    on_time_adjusted = len(filtered_df[filtered_df["Adjusted_Status"] == "Op tijd"])
    total_flights = len(filtered_df)

    # Foutmelding van 0 waarde delen opgelost
    if total_flights > 0:
        on_time_percentage_original = (on_time_original / total_flights) * 100
        on_time_percentage_adjusted = (on_time_adjusted / total_flights) * 100
    else:
        st.write("Geen vluchten gevonden voor de geselecteerde luchthaven.")
        on_time_percentage_original = None
        on_time_percentage_adjusted = None

    if on_time_percentage_original is not None and on_time_percentage_adjusted is not None:
        # Barchart code
        fig2 = px.bar(
            x=["Originele op-tijd aankomsten", "Aangepaste op-tijd aankomsten"],
            y=[on_time_percentage_original, on_time_percentage_adjusted],
            labels={"x": "Aankomst Status", "y": "Percentage"},
            title=f"Op tijd aankomende/vertrekkende vluchten voor {selected_airport} (Voor en Na Aanpassing)",
            template="plotly_dark",
            width=800
        )

        # Layout verbeteren
        fig2.update_layout(barmode='group')

        # Grafiek showcasen
        st.plotly_chart(fig2, use_container_width=True)

# data notes tab
with data_notes:
    col1, col2 = st.columns(2)
    with col1:


        # Laad de dataset
        airports = pd.read_csv(file_path, sep=';')

        # Filter de dataset op de 'Type' kolom (voor de luchthaventypes)
        luchthaven_types = airports['Type'].unique()

        # Creëer een multiselect widget zodat gebruikers luchthaventypes kunnen kiezen
        selected_types = st.multiselect(
            'Selecteer luchthaventypes om te tonen',
            options=luchthaven_types,
            default=luchthaven_types  # Standaard worden alle types getoond
        )

        # Filter de dataset op de geselecteerde types
        filtered_data = airports[airports['Type'].isin(selected_types)]

        # Groepeer op type en tel het aantal luchthavens per type
        type_counts = filtered_data['Type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Aantal']

        # Maak een taartdiagram met Plotly Express
        fig = px.pie(type_counts, values='Aantal', names='Type', title='Dataset oorspronkelijk')

        # Toon de grafiek in Streamlit
        st.plotly_chart(fig)
       
        # Optioneel: Toon de verdeling ook als bar chart
        if st.checkbox("Toon als staafdiagram"):
            bar_fig = px.bar(type_counts, x='Type', y='Aantal', title='Verdeling van Luchthaventypes (Staafdiagram)')
            st.plotly_chart(bar_fig)

    with col2:
        # Filter alleen de luchthavens met Type 'airport'
        airports_filtered = airports[airports['Type'] == 'airport']

        # Groepeer op type en tel het aantal luchthavens per type
        type_counts = airports_filtered['Type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Aantal']

        # Maak een taartdiagram met Plotly Express
        fig = px.pie(type_counts, values='Aantal', names='Type', title='Gebruikte data')

        # Toon de grafiek in Streamlit
        st.plotly_chart(fig)

        # Optioneel: Toon de verdeling ook als bar chart met een unieke key voor de checkbox
        if st.checkbox("Toon als staafdiagram", key="bar_chart_checkbox"):
            bar_fig = px.bar(type_counts, x='Type', y='Aantal', title='Verdeling van Luchthaventypes (Staafdiagram)')
            st.plotly_chart(bar_fig)
