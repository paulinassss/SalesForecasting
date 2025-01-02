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


def total_customers_orders(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    num_of_customers =  filtered_sales['Customer_ID'].nunique()
    num_of_orders = filtered_sales['Order_ID'].nunique()
    return num_of_customers, num_of_orders

def weekday_sales_and_transactions(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    filtered_sales['Weekday_Name'] = filtered_sales['Order_Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })
    daily_sales = filtered_sales.groupby('Order_Date')['Sales'].sum().reset_index()
    daily_orders = filtered_sales.groupby('Order_Date')['Order_ID'].count().reset_index()

    daily_sales = daily_sales.merge(filtered_sales[['Order_Date', 'Order_Weekday']].drop_duplicates(), on='Order_Date',
                                    how='left')
    daily_orders = daily_orders.merge(filtered_sales[['Order_Date', 'Order_Weekday']].drop_duplicates(), on='Order_Date',
                                      how='left')

    weekday_sales = daily_sales.groupby('Order_Weekday')['Sales'].sum().reset_index()
    weekday_orders = daily_orders.groupby('Order_Weekday')['Order_ID'].sum().reset_index()

    weekday_count = daily_sales['Order_Weekday'].value_counts().sort_index()

    weekday_sales['Avg_Sales'] = weekday_sales['Sales'] / weekday_count
    weekday_orders['Avg_Orders'] = weekday_orders['Order_ID'] / weekday_count

    return weekday_sales, weekday_orders



