import pandas as pd
import numpy as np
from pandas.conftest import axis_1

# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV

# Warnings
import warnings
warnings.filterwarnings('ignore')

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

def train_model(monthly_sales):
    # Separate target variable (Sales) from the predictors
    target = 'Sales'
    features = ['sales_lag_1', 'sales_lag_2', 'sales_lag_3', 'rolling_avg_3', 'rolling_avg_6']

    X = monthly_sales[features]
    y = monthly_sales[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Initialize the model
    rf_model = RandomForestRegressor(random_state=42, n_estimators=165, max_depth=10, min_samples_split=3)

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
        next_month = monthly_sales_copy['Month Year'].max() + 1
        forecast.append({'Month Year': next_month, 'Sales': predicted_sales})

        # append the forecasted data to the initial dataset
        new_row = pd.DataFrame({'Month Year': [next_month], 'Sales': [predicted_sales]})
        monthly_sales_copy = pd.concat([monthly_sales_copy, new_row], ignore_index=True)

        # update tha lag features for the next month
        latest_data['sales_lag_3'] = latest_data['sales_lag_2']
        latest_data['sales_lag_2'] = latest_data['sales_lag_1']
        latest_data['sales_lag_1'] = predicted_sales

        # update the rolling window features
        latest_data['rolling_avg_3'] = monthly_sales_copy['Sales'][-3:].mean()
        latest_data['rolling_avg_6'] = monthly_sales_copy['Sales'][-6:].mean()

    forecast_df = pd.DataFrame(forecast)

    # Return the forecast for the next 3 months
    return forecast_df

'''
test_sales = preprocess_data("stores_sales_forecasting.csv")
test_monthly_sales = generate_monthly_sales(test_sales)
test_model, error1, error2, X_test = train_model(test_monthly_sales)
test_forecast = forecast_sales(test_model, test_monthly_sales, X_test, 3)

print(f"Prediction for the next 3 months: \n {test_forecast}")
print(f"MAE: {error1}")
print(f"RMSE: {error2}")
'''



