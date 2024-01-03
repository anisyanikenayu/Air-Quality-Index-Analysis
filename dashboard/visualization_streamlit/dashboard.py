import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency
import zipfile
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

# Menyiapkan dataframe yang akan digunakan
def monthly_air_quality(df):
    # rata-rata AQI per bulan
    monthly_air_quality_all = df.resample(rule='M', on='date').agg({
        'PM2.5': 'mean',
        'PM10': 'mean',
        'SO2': 'mean',
        'NO2': 'mean',
        'CO': 'mean',
        'O3': 'mean',
    }).reset_index()
    return monthly_air_quality_all

def daily_air_quality(df):
    # rata-rata kualitas udara per hari
    daily_air_quality_all = df.resample(rule='D', on='date').agg({
        'PM2.5': 'mean',
        'PM10': 'mean',
        'SO2': 'mean',
        'NO2': 'mean',
        'CO': 'mean',
        'O3': 'mean'
    }).reset_index()
    return daily_air_quality_all

# def create_geoanalysis(df):
def daily_aqi (df):
    breakpoints = [(0, 12, 50), (12.1, 35.4, 100), (35.5, 55.4, 150), (55.5, 150.4, 200), (150.5, 250.4, 300), (250.5, 5000, 500)]
    
    def calculate_aqi(pollutant_name, concentration):
        for low, high, aqi in breakpoints:
            if low <= concentration <= high:
                return aqi
        return None
    
    def calculate_aqi_all(row):
        aqi_values = []
        concentrations = []
        pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
        for pollutant in pollutants:
            concentration = row[pollutant]
            aqi = calculate_aqi(pollutant, concentration)
            if aqi is not None:
                aqi_values.append(aqi)
                concentrations.append(concentration)
        max_aqi = max(aqi_values, default=None)
        max_concentration = max(concentrations, default=None)
        return max_aqi, max_concentration

    aqi_categories = [
        (0, 50, 'Good'), (51, 100, 'Moderate'), (101, 150, 'Unhealthy for Sensitive Groups'),
        (151, 200, 'Unhealthy'), (201, 300, 'Very Unhealthy'), (301, 500, 'Hazardous')
    ]
    
    def categorize_aqi(aqi_values):
        for low, high, category in aqi_categories:
            if low <= aqi_values <= high:
                return category
        return None

    # Apply the functions to create new columns
    df[['AQI', 'Concentration']] = df.apply(calculate_aqi_all, axis=1, result_type='expand')
    # Add Condition column based on AQI
    df['Condition'] = df['AQI'].apply(categorize_aqi)
    return df

def daily_aqi_merged(df):
    # Call the daily_air_quality function to get the daily air quality DataFrame
    daily_air_quality_data = daily_air_quality(df)
    # Call the daily_aqi function to add AQI and Condition columns
    all_df_with_aqi = daily_aqi(daily_air_quality_data)
    return all_df_with_aqi

# Load cleaned data
all_df = pd.read_csv("dashboard/visualization_streamlit/all_data_changping.csv")

datetime_columns = ["date"]
all_df.sort_values(by="date", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["date"].min()
max_date = all_df["date"].max()

# Menyiapkan data daily aqi
daily_air_quality_data = daily_air_quality(all_df)

st.title('Air Quality at St. Changping from 2013 - 2017')

# Mengambil tanggal dari date_input
selected_date = st.date_input(
        label='Pilih Tanggal',
        min_value=min_date,
        max_value=max_date,
        value=min_date  # Set default value to the minimum date
)

main_df = daily_air_quality_data[daily_air_quality_data["date"] == str(selected_date)]
main_df_hour = all_df[all_df["date"].dt.date == pd.to_datetime(str(selected_date)).date()]

# filtered_df = changping_ds[changping_ds['date'].dt.date == pd.to_datetime(desired_date).date()]

# Filter DataFrame for the selected date
all_df_with_aqi = daily_aqi(main_df)
    
col1, col2, col3 = st.columns(3)

with col1:
    selected_aqi = all_df_with_aqi["AQI"].values
    st.metric('AQI', value=selected_aqi)

with col2:
    selected_concentration = all_df_with_aqi["Concentration"].values
    st.metric('Concentration', value=int(selected_concentration))

with col3:
    selected_condition = all_df_with_aqi["Condition"].values
    st.metric('Status', value=selected_condition[0])

# GRAFIK MENAMPILKAN ALL POLUTANT PADA TANGGAL TERSEBUT
filtered_data = daily_aqi(main_df_hour)
selected_columns = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'RAIN', 'PRES', 'DEWP', 'WSPM']
fig = px.line(filtered_data, x="date", y=selected_columns,
            hover_data={"date": "|%B %d %H:00, %Y"},
              title='\n')
fig.update_xaxes(
    tickformat="%H:00")
st.plotly_chart(fig)

# GRAFIK MENAMPILKAN ALL POLUTANT PADA RENTANG WAKTU TERTENTU
st.subheader("AQI air quality activity at St. Chanping in 2013 - 2017")
min_date_range = daily_air_quality_data["date"].min()
max_date_range = daily_air_quality_data["date"].max()

# Mengambil rentang tanggal
start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date_range,
        max_value=max_date_range,
        value=[min_date_range, max_date_range]
    )

# filter dataframe
filtered_df_range = daily_air_quality_data[(daily_air_quality_data["date"] >= str(start_date)) & 
                                        (daily_air_quality_data["date"] <= str(end_date))]

fig = px.line(filtered_df_range, x='date', y=['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'], line_group='variable')
# Customize the plot
fig.update_layout(title='Polutants Index Activity', xaxis_title='Date', yaxis_title='Polutants')
st.plotly_chart(fig)

# GRAFIK MENAMPILKAN CONCENTRATION IN RANGE DATE
aqi_perday = daily_aqi(filtered_df_range)
bar_fig = px.bar(aqi_perday, x="date", y="Concentration")
max_concentration_index = aqi_perday['Concentration'].idxmax()
bar_fig.update_traces(marker_color=['rgb(204, 0, 0)' if i == max_concentration_index else 'rgb(191, 191, 191)' for i in range(len(aqi_perday))])
bar_fig.update_layout(title_x=0.5, title='Concentration Activity')
bar_fig.update_layout(plot_bgcolor='rgba(210, 239, 250, 0.09)')
st.plotly_chart(bar_fig)

# GRAFIK MENAMPILKAN PIE CHART POLUTANTS
pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
each_ctr = aqi_perday[pollutants].sum()
colors = {'PM2.5': '#BE3144',
          'PM10': '#872341',
          'SO2': '#FFE6C7',
          'NO2': '#FFA559',
          'CO': '#22092C',
          'O3': '#F05941'}
# pull is given as a fraction of the pie radius
fig = go.Figure(data=[go.Pie(labels=pollutants, values=each_ctr, pull=[0, 0, 0, 0, 0.2, 0], marker_colors=[colors[p] for p in pollutants])])
fig.update_layout(height=500, width=500, title="Emission Persentage")
st.plotly_chart(fig)

