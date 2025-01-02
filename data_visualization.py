import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import io
import base64
from dash import html
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table

# Warnings
import warnings
warnings.filterwarnings('ignore')

custom_colors = ['#A6AEBF', '#C5D3E8', '#D0E8C5', '#A7C5EB', '#9ecbd0', '#cde8e2', '#d7f5e7']

def sales_over_time(data, start_date, end_date, selected_region):
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    formatted_start_date = start_date_obj.strftime("%Y-%m")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    formatted_end_date = end_date_obj.strftime("%Y-%m")
    if selected_region != 'All':
        regional_data = data[data['Region'] == selected_region]
    else:
        regional_data = data
    # Aggregate sales by 'month_year'
    regional_data['Month_Year'] = regional_data['Order_Date'].dt.strftime('%Y-%m')
    monthly_sales = regional_data.groupby('Month_Year')['Sales'].sum().reset_index()
    monthly_sales['Month_Year'] = monthly_sales['Month_Year'].astype(str)
    filtered_sales = monthly_sales[
        (monthly_sales['Month_Year'] >= formatted_start_date) & (monthly_sales['Month_Year'] <= formatted_end_date)]

    fig = px.line(
        filtered_sales,
        x='Month_Year',
        y='Sales',
        title="Sales Trend",
        labels={'Month_Year': 'Month & Year', 'Sales': 'Total Sales ($)'}
    ).update_layout(
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Sales over time", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        ).update_traces(
        line=dict(color='#5470a5', width=1))
    return fig

def weekday_sales_and_transactions_fig(data):
    fig = px.bar(data, x='Weekday_Name', y='Avg_Orders',
                        labels={'Weekday_Name': 'Weekday', 'Avg_Orders': 'Average Orders'},
                        color='Weekday_Name',
                        color_discrete_sequence=custom_colors).update_layout(
        paper_bgcolor='rgb(233, 240, 255)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=25, r=25, t=25, b=25),
        font_family='Inconsolata',
        title=dict(text="Average number of orders per weekday", font=dict(size=15), automargin=False, yref='paper'),
        bargap=0.4
    ).update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
    ).update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
    )
    fig.update_layout(showlegend=False)
    return fig