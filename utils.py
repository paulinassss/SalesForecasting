import pandas as pd
import numpy as np
from pandas.conftest import axis_1
from pandas.tseries.offsets import MonthBegin

# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV

import io
import base64
from dash import html
import plotly.express as px

# Warnings
import warnings
warnings.filterwarnings('ignore')

# def check_integrity(data)

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return df

def preprocess_data(sales):
    # Clean Data
    sales.drop(['Postal_Code'], axis=1, inplace=True)

    # Modify Data
    sales['Order_Date'] = pd.to_datetime(sales['Order_Date'], format='%d/%m/%Y')
    sales['Ship_Date'] = pd.to_datetime(sales['Ship_Date'], format='%d/%m/%Y')

    # Feature Engineering
    sales['Order_Month'] = sales['Order_Date'].dt.month
    sales['Order_Year'] = sales['Order_Date'].dt.year
    sales['Order_Day'] = sales['Order_Date'].dt.day
    sales['Order_Weekday'] = sales['Order_Date'].dt.weekday
    sales['Quarter'] = sales['Order_Date'].dt.quarter
    sales['Shipping_Time'] = (sales['Ship_Date'] - sales['Order_Date']).dt.days

    # Encode categorical features
    categorical_cols = ['Ship_Mode', 'Segment', 'Category', 'City', 'State', 'Product_Name']
    label_encoders = {}
    for col in categorical_cols:
        label_encoders[col] = LabelEncoder()
        sales[col] = label_encoders[col].fit_transform(sales[col])

    return sales

def generate_monthly_sales(sales):
    sales['Month_Year'] = sales['Order_Date'].dt.strftime('%Y-%m')

    # Aggregate sales by 'month_year'
    monthly_sales = sales.groupby('Month_Year')['Sales'].sum().reset_index()

    # Sort by 'month_year' to ensure proper calculation of lag and rolling features
    monthly_sales = monthly_sales.sort_values('Month_Year').reset_index(drop=True)
    monthly_sales['Month_Year'] = monthly_sales['Month_Year'].astype(str)

    # Add lag features
    monthly_sales['sales_lag_1'] = monthly_sales['Sales'].shift(1)
    monthly_sales['sales_lag_2'] = monthly_sales['Sales'].shift(2)
    monthly_sales['sales_lag_3'] = monthly_sales['Sales'].shift(3)

    # Add rolling window features
    monthly_sales['rolling_avg_3'] = monthly_sales['Sales'].rolling(window=3).mean()
    monthly_sales['rolling_avg_6'] = monthly_sales['Sales'].rolling(window=6).mean()

    # Drop missing values after rolling
    monthly_sales = monthly_sales.dropna()
    return monthly_sales

def train_model(monthly_sales):
    # Separate target variable (Sales) from the predictors
    target = 'Sales'
    features = ['sales_lag_1', 'sales_lag_2', 'sales_lag_3', 'rolling_avg_3', 'rolling_avg_6']

    X = monthly_sales[features]
    y = monthly_sales[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Initialize the model
    rf_model = RandomForestRegressor(random_state=42, n_estimators=205, max_depth=3, min_samples_split=2)

    # Train the model
    rf_model.fit(X_train, y_train)

    # Make predictions
    y_pred = rf_model.predict(X_test)

    # Evaluate performance
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)

    return rf_model, mae, rmse, X_test

def forecast_sales(rf_model, monthly_sales, X_test, forecast_period): #forecast_period - only 1 month, 3 months and 6 months options
    # The most recent actual data
    latest_actual_sales = monthly_sales.iloc[-1]['Sales']
    latest_data = X_test.iloc[-1].copy()

    # Replace lagged features
    latest_data['sales_lag_1'] = latest_actual_sales
    latest_data['sales_lag_2'] = monthly_sales.iloc[-2]['Sales']
    latest_data['sales_lag_3'] = monthly_sales.iloc[-3]['Sales']
    latest_data['rolling_avg_3'] = monthly_sales['Sales'][-3:].mean()
    latest_data['rolling_avg_6'] = monthly_sales['Sales'][-6:].mean()
    monthly_sales_copy = monthly_sales.copy()

    # Empty list to store forecast values
    forecast = []

    # Forecast the next {forecast_period} months
    for i in range(forecast_period):
        # predict the next month's sales
        predicted_sales = rf_model.predict(latest_data.values.reshape(1, -1))
        # Get the latest month in the 'Month_Year' column
        latest_month = pd.to_datetime(monthly_sales_copy['Month_Year'].max(), format='%Y-%m')
        # Calculate the next month by adding one month
        next_month = (latest_month + pd.DateOffset(months=1)).strftime('%Y-%m')
        # Append the forecast for the next month
        forecast.append({'Month_Year': next_month, 'Sales': predicted_sales})

        # append the forecasted data to the initial dataset
        new_row = pd.DataFrame({'Month_Year': [next_month], 'Sales': [predicted_sales]})
        monthly_sales_copy = pd.concat([monthly_sales_copy, new_row], ignore_index=True)

        # update tha lag features for the next month
        latest_data['sales_lag_3'] = latest_data['sales_lag_2']
        latest_data['sales_lag_2'] = latest_data['sales_lag_1']
        latest_data['sales_lag_1'] = predicted_sales

        # update the rolling window features
        latest_data['rolling_avg_3'] = monthly_sales_copy['Sales'][-3:].mean()
        latest_data['rolling_avg_6'] = monthly_sales_copy['Sales'][-6:].mean()

    forecast_df = pd.DataFrame(forecast)
    forecast_df['Month_Year'] = forecast_df['Month_Year'].astype(str)
    forecast_df['Sales'] = forecast_df['Sales'].astype(str)

    # Return the forecast for the next 3 month
    return forecast_df

def create_graph(data):
    monthly_sales = generate_monthly_sales(data)
    monthly_sales['Month_Year'] = pd.to_datetime(monthly_sales['Month_Year'])
    sales_trend_fig = px.line(
        monthly_sales,
        x='Month_Year',
        y='Sales',
        title="Sales Trend",
        labels={'x': 'Month', 'y': 'Sales'}
    )
    return sales_trend_fig

def generate_default_dates(data):
    min_date = data['Order_Date'].min()
    max_date = data['Order_Date'].max()
    start_date = min_date.strftime('%Y-%m-%d')
    end_date = max_date.strftime('%Y-%m-%d')

    return start_date, end_date

def total_sales(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    # Calculate the total sales within the date range
    total_sales = filtered_sales['Sales'].sum()
    total_sales = "${:,.2f}".format(total_sales)
    return total_sales
'''
test_set = pd.read_csv('superstore_final_dataset.csv')
test_sales = preprocess_data(test_set)
test_monthly_sales = generate_monthly_sales(test_sales)
test_model, error1, error2, X_test = train_model(test_monthly_sales)
test_forecast = forecast_sales(test_model, test_monthly_sales, X_test, 3)

print(f"Prediction for the next 3 months: \n {test_forecast}")
print(f"MAE: {error1}")
print(f"RMSE: {error2}")
print(test_forecast.info())
'''






