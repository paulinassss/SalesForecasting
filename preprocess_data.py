import pandas as pd
import io
import base64
import pandas as pd
import io
import base64
from dash import html

# Warnings
import warnings
warnings.filterwarnings('ignore')

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

def validate_dataset_format(user_df):
    is_valid = False
    # Oczekiwane nazwy kolumn i ich typy danych
    expected_columns = {
        "Row_ID": "int64",
        "Order_ID": "object",
        "Order_Date": "object",
        "Ship_Date": "object",
        "Ship_Mode": "object",
        "Customer_ID": "object",
        "Customer_Name": "object",
        "Segment": "object",
        "Country": "object",
        "City": "object",
        "State": "object",
        "Postal_Code": "float64",
        "Region": "object",
        "Product_ID": "object",
        "Category": "object",
        "Sub_Category": "object",
        "Product_Name": "object",
        "Sales": "float64"
    }
    # Sprawdzenie, czy kolumny się zgadzają
    user_columns = user_df.dtypes.to_dict()
    user_columns = {col: str(dtype) for col, dtype in user_columns.items()}
    # Porównanie nazw kolumn
    missing_columns = set(expected_columns.keys()) - set(user_columns.keys())
    extra_columns = set(user_columns.keys()) - set(expected_columns.keys())
    if missing_columns:
        return is_valid, html.Div([f"Missing columns: {missing_columns}"])
    if extra_columns:
        return is_valid, html.Div([f"Extra columns: {extra_columns}"])
    # Porównanie typów danych
    mismatched_types = {
        col: {"expected": expected_columns[col], "actual": user_columns[col]}
        for col in expected_columns
        if expected_columns[col] != user_columns.get(col)
    }
    if mismatched_types:
        return is_valid, html.Div([f"Data types do not match: {mismatched_types}"])
    return is_valid, html.Div(["Dataset is valid!"])

def preprocess_data(sales):
    # Clean Data
    sales.drop(['Row_ID', 'Postal_Code'], axis=1, inplace=True)
    sales.dropna()
    sales.drop_duplicates()
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

    return sales
