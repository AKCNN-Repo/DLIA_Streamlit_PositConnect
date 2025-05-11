import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from scipy.stats import gaussian_kde
from tkinter import Tk, filedialog

# Function to open file dialog and get file path
def get_file_path(prompt):
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title=prompt, filetypes=[("CSV Files", "*.csv")])
    root.destroy()
    return file_path

# File selection via Tkinter
st.sidebar.write("Upload Metrics Files")
if st.sidebar.button("Select Event Tracking Metrics File"):
    mean_metrics_path = get_file_path("Select Event Tracking Metrics CSV File")
    st.session_state.mean_metrics_path = mean_metrics_path

if st.sidebar.button("Select iControl Data File"):
    temp_vol_path = get_file_path("Select iControl Data CSV File")
    st.session_state.temp_vol_path = temp_vol_path

# Ensure file paths exist in session state
if 'mean_metrics_path' in st.session_state and 'temp_vol_path' in st.session_state:
    # Load data
    data = pd.read_csv(st.session_state.mean_metrics_path)
    temp_vol_data = pd.read_csv(st.session_state.temp_vol_path)

    # Ensure 'Time' is in numeric format for both datasets
    data['Time'] = pd.to_numeric(data['Time'])
    temp_vol_data['Time'] = pd.to_numeric(temp_vol_data['Time'])

    # Function to smooth data using moving average
    def smooth_data(data, window_size=5):
        return data.rolling(window=window_size).mean()

    # Sidebar controls
    selected_column = st.sidebar.selectbox('Select Data Column', [col for col in data.columns if col != 'Time'])
    time_range = st.sidebar.slider('Select Time Range', min_value=int(data['Time'].min()), max_value=int(data['Time'].max()), value=(int(data['Time'].min()), int(data['Time'].max())), step=1)
    window_size = st.sidebar.slider('Smoothing Window Size', min_value=1, max_value=100, value=5, step=1)
    plot_type = st.sidebar.radio('Select Plot Type', ('Raw', 'Smoothed', 'Filtered'))
    update_button = st.sidebar.button('Update KDE')

    # Store KDE data and time indices
    if 'kde_data' not in st.session_state:
        st.session_state.kde_data = []

    # Filter data based on the selected time range
    filtered_data = data[(data['Time'] >= time_range[0]) & (data['Time'] <= time_range[1])]
    filtered_temp_vol_data = temp_vol_data[(temp_vol_data['Time'] >= time_range[0]) & (temp_vol_data['Time'] <= time_range[1])]

    # Update KDE data
    if update_button:
        kde = gaussian_kde(filtered_data[selected_column])
        extend_fraction = 0.1
        min_val = filtered_data[selected_column].min()
        max_val = filtered_data[selected_column].max()
        range_val = max_val - min_val
        extended_min = min_val - extend_fraction * range_val
        extended_max = max_val + extend_fraction * range_val
        x_range = np.linspace(extended_min, extended_max, 100)
        kde_data = {'x': x_range, 'y': kde(x_range), 'time': (time_range[0], time_range[1]), 'column': selected_column}
        st.session_state.kde_data.append(kde_data)

    # Plot Time Series with Temperature and Volume
    time_series_fig = go.Figure()
    time_series_fig.add_trace(go.Scatter(x=filtered_temp_vol_data['Time'], y=filtered_temp_vol_data['Temperature'], mode='lines', name='Temperature', yaxis='y2', line=dict(color='orange')))
    time_series_fig.add_trace(go.Scatter(x=filtered_temp_vol_data['Time'], y=filtered_temp_vol_data['Volume'], mode='lines', name='Volume', yaxis='y2', line=dict(color='green')))

    if plot_type == 'Raw':
        time_series_fig.add_trace(go.Scatter(x=filtered_data['Time'], y=filtered_data[selected_column], mode='lines', name=f'Raw {selected_column}', line=dict(color='rgba(128, 128, 128, 0.5)')))
    elif plot_type == 'Smoothed':
        time_series_fig.add_trace(go.Scatter(x=filtered_data['Time'], y=smooth_data(filtered_data[selected_column], window_size), mode='lines', name=f'Smoothed {selected_column}', line=dict(color='blue')))
    elif plot_type == 'Filtered':
        filtered_smoothed_data = smooth_data(filtered_data[selected_column], window_size)
        time_series_fig.add_trace(go.Scatter(x=filtered_data['Time'], y=filtered_smoothed_data, mode='lines', name=f'Filtered Smoothed {selected_column}'))

    time_series_fig.update_layout(
        yaxis=dict(title=selected_column, titlefont=dict(color='blue'), tickfont=dict(color='blue'), title_standoff=20, domain=[0, 0.85]),
        yaxis2=dict(title='Temperature / Volume', titlefont=dict(color='orange'), tickfont=dict(color='orange'), overlaying='y', side='right', title_standoff=40, anchor='free', position=0.86),
        xaxis=dict(title='Time [hour]'),
        margin=dict(l=50, r=180, t=50, b=50),
        legend=dict(x=1.05, y=1, xanchor='left', yanchor='top', traceorder='normal', font=dict(family='sans-serif', size=12, color='#000'), bgcolor='#E2E2E2', bordercolor='#FFFFFF', borderwidth=2)
    )

    st.plotly_chart(time_series_fig)

    # Plot KDEs
    kde_fig = go.Figure()
    for kde_data in st.session_state.kde_data:
        if kde_data['column'] == selected_column:
            kde_fig.add_trace(go.Scatter(x=kde_data['x'], y=kde_data['y'], mode='lines', name=f"{selected_column} at Time {kde_data['time']}"))

    kde_fig.update_layout(xaxis=dict(title=selected_column), yaxis=dict(title='Density'))
    st.plotly_chart(kde_fig)
else:
    st.write("Please select both files to proceed.")

