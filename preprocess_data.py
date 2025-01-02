import pandas as pd

# Warnings
import warnings
warnings.filterwarnings('ignore')


# def check_integrity(data)

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

    return sales
