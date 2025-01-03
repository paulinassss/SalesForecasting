import pandas as pd
import numpy as np

# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Warnings
import warnings
warnings.filterwarnings('ignore')

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
    forecast_df['Sales'] = forecast_df['Sales'].astype(float)  # Ensure the values are floats
    forecast_df['Sales'] = forecast_df['Sales'].map("${:,.2f}".format)
    # Return the forecast for the next 3 month
    return forecast_df