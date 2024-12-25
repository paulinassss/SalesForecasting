from pyexpat.errors import messages

import pandas as pd
import numpy as np
from pandas.conftest import axis_1
from pandas.tseries.offsets import MonthBegin
from datetime import datetime, timedelta


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
import plotly.graph_objects as go
from dash import dash_table

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

def create_graph(data, start_date, end_date):
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    formatted_start_date = start_date_obj.strftime("%Y-%m")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    formatted_end_date = end_date_obj.strftime("%Y-%m")
    # Aggregate sales by 'month_year'
    data['Month_Year'] = data['Order_Date'].dt.strftime('%Y-%m')
    monthly_sales = data.groupby('Month_Year')['Sales'].sum().reset_index()
    monthly_sales['Month_Year'] = monthly_sales['Month_Year'].astype(str)
    #monthly_sales['Month_Year'] = pd.to_datetime(monthly_sales['Month_Year'])
    filtered_sales = monthly_sales[(monthly_sales['Month_Year'] >= formatted_start_date) & (monthly_sales['Month_Year'] <= formatted_end_date)]
    sales_trend_fig = px.line(
        filtered_sales,
        x='Month_Year',
        y='Sales',
        title="Sales Trend",
        labels={'x': 'Month', 'y': 'Sales'}
    )
    return sales_trend_fig

def create_weekday_sales_graph(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    daily_sales = filtered_sales.groupby('Order_Date')['Sales'].sum().reset_index()

    daily_sales = daily_sales.merge(filtered_sales[['Order_Date', 'Order_Weekday']].drop_duplicates(), on='Order_Date',
                                    how='left')

    weekday_sales = daily_sales.groupby('Order_Weekday')['Sales'].sum().reset_index()
    weekday_count = daily_sales['Order_Weekday'].value_counts().sort_index()
    weekday_sales['Avg_Sales'] = weekday_sales['Sales'] / weekday_count
    weekday_sales['Weekday_Name'] = weekday_sales['Order_Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    fig_sales = px.bar(weekday_sales, x='Weekday_Name', y='Avg_Sales',
                       title="Average Sales per Weekday",
                       labels={'Weekday_Name': 'Weekday', 'Avg_Sales': 'Average Sales'},
                       color='Weekday_Name')
    return fig_sales

def create_weekday_orders_graph(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    daily_orders = filtered_sales.groupby('Order_Date')['Order_ID'].count().reset_index()
    daily_orders = daily_orders.merge(filtered_sales[['Order_Date', 'Order_Weekday']].drop_duplicates(), on='Order_Date',
                                      how='left')
    weekday_orders = daily_orders.groupby('Order_Weekday')['Order_ID'].sum().reset_index()
    weekday_count = daily_orders['Order_Weekday'].value_counts().sort_index()
    weekday_orders['Avg_Orders'] = weekday_orders['Order_ID'] / weekday_count
    weekday_orders['Weekday_Name'] = weekday_orders['Order_Weekday'].map({
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    })

    fig_orders = px.bar(weekday_orders, x='Weekday_Name', y='Avg_Orders',
                        title="Average Orders per Weekday",
                        labels={'Weekday_Name': 'Weekday', 'Avg_Orders': 'Average Orders'},
                        color='Weekday_Name')
    return fig_orders


def generate_default_dates(data):
    min_date = data['Order_Date'].min()
    max_date = data['Order_Date'].max()
    start_date = min_date.strftime('%Y-%m-%d')
    end_date = max_date.strftime('%Y-%m-%d')

    return start_date, end_date

def total_revenue(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    # Calculate the total sales within the date range
    total_r = filtered_sales['Sales'].sum()
    total_r = "${:,.2f}".format(total_r)
    return total_r

def average_growth(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").replace(day=1)
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    end_date_obj = (end_date_obj.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    date_diff = end_date_obj - start_date_obj
    if date_diff.days > 365:
        # Calculate average growth Q over Q
        quarterly_sales = filtered_sales.groupby(['Order_Year', 'Quarter'])['Sales'].sum().reset_index().sort_values(
            by=['Order_Year', 'Quarter']).reset_index(drop=True)
        quarterly_sales['QoQ_Growth'] = (quarterly_sales['Sales'].pct_change() * 100).dropna()
        average = f"{quarterly_sales['QoQ_Growth'].mean():.2f}%"
        message = "Quarter over Quarter"
    else:
        # Calculate average growth M over M
        monthly_sales = filtered_sales.groupby(['Order_Year', 'Order_Month'])['Sales'].sum().reset_index().sort_values(
            by=['Order_Year', 'Order_Month']).reset_index(drop=True)
        monthly_sales['MoM_Growth'] = (monthly_sales['Sales'].pct_change() * 100).dropna()
        average = f"{monthly_sales['MoM_Growth'].mean():.2f}%"
        message = "Month over Month"
    return average, message

def customer_cohorts(data):
    # Candata lists customers and Year_Quarter periods in which they placed at least one order
    candata = (data[['Customer_ID', 'Order_Date']]
               .drop_duplicates()
               .assign(Year_Quarter=data.Order_Date.dt.to_period(freq='Q'))
               .drop('Order_Date', axis=1)
               .drop_duplicates()
               )
    # Define which period a customer belongs to by the earliest quarter they made a purchase
    cohorts = candata.groupby('Customer_ID').min().rename(columns={'Year_Quarter': 'Time_Cohort'})

    # Determine the size of each cohort (the number of customer in each cohort)
    cohorts_size = cohorts.reset_index().groupby('Time_Cohort').size().sort_index().rename('Number_of_Customers')
    cohorts_size_df = cohorts_size.reset_index()
    cohorts_size_df.columns = ['Time_Cohort', 'Number_of_Customers']

    cohorts_size_df['Time_Cohort'] = cohorts_size_df['Time_Cohort'].astype(str)

    cohorts_size_df['Year'] = cohorts_size_df['Time_Cohort'].str[:4]
    yearly_totals = cohorts_size_df.groupby('Year')['Number_of_Customers'].sum().reset_index()
    yearly_totals['Cumulative_Pos'] = yearly_totals['Number_of_Customers'].cumsum()

    fig = px.bar(
        cohorts_size_df,
        x='Time_Cohort',
        y='Number_of_Customers',
        title='Customer Cohorts by Quarters',
        labels={'Time_Cohort': 'Quarter', 'Number_of_Customers': 'Number of Customers'},
        text='Number_of_Customers',  # Display the number of customers on each bar
        color='Time_Cohort'  # Optional: Add color to distinguish bars by quarter
    )

    # Update the layout to improve appearance
    fig.update_layout(
        xaxis_title='Quarter',
        yaxis_title='Number of Customers',
        showlegend=False  # Hide the legend, as the color is redundant
    )

    base = candata.merge(cohorts, how='outer', indicator='join_type', validate='m:1', on= 'Customer_ID')
    base['Year_Quarter'] = base['Year_Quarter'].astype(str)
    base['Time_Cohort'] = base['Time_Cohort'].astype(str)
    base.pop('join_type')
    base.reset_index()

    crosstab = pd.crosstab(
        index=base['Time_Cohort'],
        columns=base['Year_Quarter']
    )

    # Normalize the values by dividing each value by the first value of the row, then multiply by 100 to get percentages
    crosstab_normalized = crosstab.apply(lambda s: 100 * s / s[s.name], axis=1)

    # Set the float format to display percentages with two decimal points
    pd.set_option('display.float_format', lambda x: '%.2f' % x)

    crosstab_normalized = crosstab_normalized.applymap(lambda x: f"{x:.2f}%" if x != 0 else "")
    crosstab_normalized = crosstab_normalized.reset_index()

    crosstab_conv = crosstab_normalized.to_dict('records')  # Rows of the table
    columns = [{'name': col, 'id': col} for col in crosstab.columns] # Column headers
    table = dash_table.DataTable(
        data=crosstab_conv,
        columns=columns,
        style_table={'overflowX': 'auto', 'width': '80%', 'margin': 'auto'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'center', 'padding': '2px', 'fontSize': '10px', 'maxWidth': '70px', 'lineHeight': '10px'},
    )

    return fig, table

def customer_segments(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    segment_sizes = filtered_sales.groupby('Segment')['Customer_ID'].nunique().reset_index()
    segment_sizes.columns = ['Segment', 'Customer_Count']

    segment_mapping = {0: 'Consumer', 1: 'Corporate', 2: 'Home Office'}
    segment_sizes['Segment'] = segment_sizes['Segment'].map(segment_mapping)

    fig = px.pie(
        segment_sizes,
        names='Segment',
        values='Customer_Count',
        color='Customer_Count',  # Color the bubbles based on the customer count
        hover_name='Segment',  # Show segment name when hovering over a bubble
        title="Customer Distribution by Segment",
        labels={'Customer_Count': 'Number of Customers'},
    )
    return fig







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






