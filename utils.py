import pandas as pd
import numpy as np


from sklearn.preprocessing import LabelEncoder


def preprocess_data(file_path):
    # Load Data
    sales = pd.read_csv(file_path, encoding='latin1')

    # Clean Data
    sales.drop(['Row ID', 'Postal Code', 'Region'], axis=1, inplace=True)

    # Modify Data
    sales['Order Date'] = pd.to_datetime(sales['Order Date'])
    sales['Ship Date'] = pd.to_datetime(sales['Ship Date'])

    # Feature Engineering
    sales['Order Month'] = sales['Order Date'].dt.month
    sales['Order Year'] = sales['Order Date'].dt.year
    sales['Order Day'] = sales['Order Date'].dt.day
    sales['Order Weekday'] = sales['Order Date'].dt.weekday
    sales['Quarter'] = sales['Order Date'].dt.quarter
    sales['Shipping Time'] = (sales['Ship Date'] - sales['Order Date']).dt.days

    # Encode categorical features
    categorical_cols = ['Ship Mode', 'Segment', 'Category', 'City', 'State', 'Product Name']
    label_encoders = {}
    for col in categorical_cols:
        label_encoders[col] = LabelEncoder()
        sales[col] = label_encoders[col].fit_transform(sales[col])

    return sales

def generate_monthly_sales(sales):
    sales['Month Year'] = sales['Order Date'].dt.to_period('M')

    # Aggregate data
    monthly_sales = sales.groupby('Month Year').agg({'Sales': 'sum'}).reset_index()

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

print(generate_monthly_sales(preprocess_data("stores_sales_forecasting.csv")))