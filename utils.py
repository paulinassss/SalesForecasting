from pyexpat.errors import messages

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
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

def total_customers_orders(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    num_of_customers =  filtered_sales['Customer_ID'].nunique()
    num_of_orders = filtered_sales['Order_ID'].nunique()
    return num_of_customers, num_of_orders

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
        style_table={'overflow': 'auto', 'width': '80%', 'margin': 'auto'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'center', 'padding': '2px', 'fontSize': '10px', 'maxWidth': '70px', 'lineHeight': '10px'},
    )

    return fig, table

def customer_segments(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    segment_sizes = filtered_sales.groupby('Segment')['Customer_ID'].nunique().reset_index()
    segment_sizes.columns = ['Segment', 'Customer_Count']
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

def sales_per_segments(data, start_date, end_date, selected_graph):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    total_sales_per_segment = filtered_sales.groupby('Segment')['Sales'].sum().reset_index()

    unique_orders_per_segment = filtered_sales.groupby('Segment')['Order_ID'].nunique().reset_index()
    unique_orders_per_segment.columns = ['Segment', 'Unique_Order_Count']
    segment_sales = pd.merge(unique_orders_per_segment, total_sales_per_segment, on='Segment')
    segment_sales['Mean_Sales_Per_Order'] = segment_sales['Sales'] / segment_sales['Unique_Order_Count']

    if selected_graph == 'total':
        fig= px.bar(segment_sales,
                     x='Sales',
                     y='Segment',
                     orientation='h',
                     title="Total Sales by Segment",
                     labels={'Sales': 'Total Sales ($)', 'Segment': 'Segment'}
                    )
        fig.update_layout(
            height=300,  # Total height of the figure
            bargap=0.2,  # Space between bars (smaller = thicker bars)
        )
    elif selected_graph == 'mean':
        fig= px.bar(segment_sales,
                           x='Mean_Sales_Per_Order',
                           y='Segment',
                           orientation='h',
                           title="Mean Order Value by Segment",
                           labels={'Sales': 'Mean order value ($)', 'Segment': 'Segment'}
                           )
        fig.update_layout(
            height=300,  # Total height of the figure
            bargap=0.2,  # Space between bars (smaller = thicker bars)
        )

    return fig

def top_clients(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    clients = filtered_sales.groupby(['Customer_ID', 'Customer_Name', 'Segment']).agg(Sales=('Sales', 'sum'),
                                                                                Number_of_Orders=(
                                                                                 'Order_ID', 'nunique')).reset_index()
    top_10_clients = clients.sort_values(by='Sales', ascending=False).head(10)
    top_10_clients.reset_index(drop=True, inplace=True)
    top_10_clients.index += 1

    table = dash_table.DataTable(
        data=top_10_clients.to_dict('records'),  # Convert DataFrame to dictionary
        columns=[{'name': col, 'id': col} for col in top_10_clients.columns],  # Columns for the table
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_cell={'textAlign': 'center', 'padding': '5px', 'fontSize': '14px'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        page_size=10,  # Limit table to 10 rows per page
    )

    return table

def repeat_customer_rate(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    first_purchase_data = data[['Customer_ID', 'Order_Date']].drop_duplicates()
    first_purchase_data['First_Purchase_Date'] = first_purchase_data.groupby('Customer_ID')['Order_Date'].transform('min')
    valid_customers = first_purchase_data[
        (first_purchase_data['First_Purchase_Date'] >= start_date) &
        (first_purchase_data['First_Purchase_Date'] <= end_date)
        ]
    valid_customer_ids = valid_customers['Customer_ID'].unique()
    filtered_sales = filtered_sales[filtered_sales['Customer_ID'].isin(valid_customer_ids)]
    customer_purchase_count = filtered_sales.groupby('Customer_ID').agg(
        Total_Purchases=('Order_ID', 'nunique')
    ).reset_index()
    repeat_customers = customer_purchase_count[customer_purchase_count['Total_Purchases'] > 1]
    total_customers_in_range = len(valid_customer_ids)
    repeat_customer_count = len(repeat_customers)
    rcr = repeat_customer_count / total_customers_in_range if total_customers_in_range > 0 else 0

    rcr_percentage = f"{rcr * 100:.1f}%"

    return rcr_percentage

def abc_customers(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    customer_sales = filtered_sales.groupby(['Customer_ID', 'Customer_Name'])['Sales'].sum().reset_index()
    customer_sales = customer_sales.sort_values(by='Sales', ascending=False)
    customer_sales['%_Contribution'] = (customer_sales['Sales'] / customer_sales['Sales'].sum()) * 100
    customer_sales['Cumulative_%'] = customer_sales['%_Contribution'].cumsum()

    def classify_customer(cumulative_percentage):
        if cumulative_percentage <= 80:
            return 'A'
        elif cumulative_percentage <= 95:
            return 'B'
        else:
            return 'C'

    customer_sales['Customer_Category'] = customer_sales['Cumulative_%'].apply(classify_customer)
    category_totals = customer_sales.groupby('Customer_Category')['Sales'].sum().reset_index()
    overall_total = category_totals['Sales'].sum()
    category_totals['Percentage'] = (category_totals['Sales'] / overall_total) * 100

    # Calculate the percentage of customers in each category
    customer_count_by_category = customer_sales['Customer_Category'].value_counts()
    total_customers = len(customer_sales)
    customer_percentage_by_category = (customer_count_by_category / total_customers) * 100

    # Prepare the X-axis labels to include customer percentage
    category_totals['Category_Label'] = category_totals['Customer_Category'] + \
                                        '\n(' + category_totals['Customer_Category'].map(
        customer_percentage_by_category).round(2).astype(str) + '% of customers)'

    fig = px.bar(category_totals, x='Category_Label', y='Sales', text='Percentage',
                 title='ABC Analysis: Total Sales by Category',
                 labels={'Sales': 'Total Sales ($)', 'Customer_Category': 'Category'})
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')

    return fig

def pareto_products(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    product_sales = filtered_sales.groupby('Product_Name')['Sales'].sum().reset_index()
    product_sales = product_sales.sort_values(by='Sales', ascending=False)
    product_sales['%_Contribution'] = (product_sales['Sales'] / product_sales['Sales'].sum()) * 100
    product_sales['Cumulative_%'] = product_sales['%_Contribution'].cumsum()
    top_20_percent_products = product_sales[product_sales['Cumulative_%'] <= 80]

    # Create the Pareto chart using Plotly
    fig = go.Figure()

    # Bar chart for the values
    fig.add_trace(go.Bar(
        x=top_20_percent_products['Product_Name'],
        y=top_20_percent_products['Sales'],
        name='Sales',
    ))

    # Line chart for the cumulative percentage
    fig.add_trace(go.Scatter(
        x=top_20_percent_products['Product_Name'],
        y=top_20_percent_products['Cumulative_%'],
        name='Cumulative Percentage',
        mode='lines+markers',
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title="Pareto Chart",
        xaxis_title="Category",
        yaxis_title="Value",
        yaxis2=dict(
            title="Cumulative Percentage",
            overlaying='y',
            side='right',
            #tickformat="%"
        ),
        showlegend=False,
    )

    return fig

def category_perfomance(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    # Aggregate sales for categories and subcategories
    category_sales = filtered_sales.groupby('Category')['Sales'].sum().reset_index()
    category_sales['Type'] = 'Category'  # Add a type column to distinguish categories
    category_sales['Label'] = category_sales['Category']  # Create a label for plotting

    subcategory_sales = filtered_sales.groupby(['Category', 'Sub_Category'])['Sales'].sum().reset_index()
    subcategory_sales['Type'] = 'Sub_Category'  # Add a type column to distinguish subcategories
    subcategory_sales['Label'] = subcategory_sales['Sub_Category']  # Create a label for plotting

    # Sort categories by total sales in descending order
    category_sales = category_sales.sort_values(by='Sales', ascending=False)

    # Within each category, sort subcategories by sales in descending order
    subcategory_sales = subcategory_sales.sort_values(by=['Category', 'Sales'], ascending=[True, False])

    # Combine categories and subcategories into a single DataFrame
    combined_sales = pd.concat([
        category_sales[['Label', 'Sales', 'Type']],
        subcategory_sales[['Label', 'Sales', 'Type']]
    ])

    # Create a custom y-axis that groups categories with their subcategories
    y_labels = []
    sales_values = []
    colors = []
    formatted_sales = []  # To store formatted sales values

    for category in category_sales['Label']:
        # Add the category bar
        category_row = category_sales[category_sales['Label'] == category]
        y_labels.append(category)  # Category label
        sales = category_row['Sales'].values[0]
        sales_values.append(sales)
        colors.append('blue')  # Color for category bars
        formatted_sales.append(f"${sales:,.2f}")  # Custom currency formatting

        # Add subcategory bars for this category
        subcategories = subcategory_sales[subcategory_sales['Category'] == category]
        for _, row in subcategories.iterrows():
            y_labels.append(f"  {row['Label']}")  # Indent for subcategories
            sales = row['Sales']
            sales_values.append(sales)
            colors.append('orange')  # Color for subcategory bars
            formatted_sales.append(f"${sales:,.2f}")  # Custom currency formatting

    # Create the bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=y_labels,  # Custom y-axis labels
        x=sales_values,  # Corresponding sales values
        marker_color=colors,  # Custom colors for categories and subcategories
        text=formatted_sales,  # Use formatted sales values for display
        textposition='outside',  # Display text outside the bars
        orientation='h'  # Set orientation to horizontal
    ))

    # Update layout
    fig.update_layout(
        title="Category and Subcategory Performance (Grouped and Sorted)",
        xaxis_title="Sales",
        yaxis_title="Categories and Subcategories",
        xaxis=dict(tickformat='$,.2f'),  # Format x-axis as currency
        showlegend=False,
        bargap=0.2,  # Space between bars
    )

    return fig

def long_tail_analysis(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    product_customer_count = filtered_sales.groupby('Product_ID')['Customer_ID'].nunique().reset_index()
    customer_group_count = product_customer_count.groupby('Customer_ID')['Product_ID'].count().reset_index()
    customer_group_count.columns = ['Number_of_Customers', 'Number_of_Products']
    customer_group_count['Bubble_Size'] = customer_group_count['Number_of_Products']

    fig = px.scatter(
        customer_group_count,
        x='Number_of_Customers',  # X-axis: Number of customers who bought the product
        y='Number_of_Products',  # Y-axis: Number of products bought by X customers
        size='Bubble_Size',  # Size of the bubble: Number of products
        title="Bubble Plot of Products Bought by Number of Customers",
        labels={'Number_of_Customers': 'Number of Customers', 'Number_of_Products': 'Number of Products'},
        template='plotly',
        size_max=50
    )

    for i, row in customer_group_count.iterrows():
        # Horizontal line from Y-axis to the bubble
        fig.add_shape(
            go.layout.Shape(
                type="line",
                x0=0,  # Starting point on X-axis
                y0=row['Number_of_Products'],  # Y position of the bubble
                x1=row['Number_of_Customers'],  # X position of the bubble
                y1=row['Number_of_Products'],  # Y position of the bubble
                line=dict(color="blue", width=1, dash="dot")  # Customize line style
            )
        )
        # Vertical line from X-axis to the bubble
        fig.add_shape(
            go.layout.Shape(
                type="line",
                x0=row['Number_of_Customers'],  # X position of the bubble
                y0=0,  # Starting point on Y-axis
                x1=row['Number_of_Customers'],  # X position of the bubble
                y1=row['Number_of_Products'],  # Y position of the bubble
                line=dict(color="red", width=1, dash="dot")  # Customize line style
            )
        )

    return fig

def top_states_and_cities(data, start_date, end_date, selected_region):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    if selected_region != 'All':
        regional_sales = filtered_sales[filtered_sales['Region'] == selected_region]
    else:
        regional_sales = filtered_sales
    # States
    states_grouped = regional_sales.groupby('State')['Sales'].sum().reset_index()
    top_states = states_grouped.sort_values(by='Sales', ascending=False).head(5)
    # Cities
    cities_grouped = regional_sales.groupby('City')['Sales'].sum().reset_index()
    top_cities = cities_grouped.sort_values(by='Sales', ascending=False).head(5)

    fig_states = px.bar(top_states, x='State', y='Sales',
                        title='Top 5 Selling States',
                        labels={'State': 'State', 'Sales': 'Total Sales'})

    # Create Bar Chart for Top 5 Cities by Sales
    fig_cities = px.bar(top_cities, x='City', y='Sales',
                        title='Top 5 Selling Cities',
                        labels={'City': 'City', 'Sales': 'Total Sales'})
    return fig_states, fig_cities


def regional_top_states(data, start_date, end_date, selected_region):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    filtered_sales['State'] = filtered_sales['State'].astype(str)
    state_name_to_abbr = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
        'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND',
        'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
        'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
        'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
        'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    filtered_sales['State'] = filtered_sales['State'].map(state_name_to_abbr)
    if selected_region != 'All':
        regional_sales =filtered_sales[filtered_sales['Region'] == selected_region]
        state_sales = regional_sales.groupby('State')['Sales'].sum().reset_index()
    else:
        state_sales = filtered_sales.groupby('State')['Sales'].sum().reset_index()
    # Create a choropleth map
    fig = px.choropleth(
        state_sales,
        locations= 'State',  # Column with state names or abbreviations
        locationmode='USA-states',  # Use state-level mapping
        color='Sales',
        color_continuous_scale='Blues',
        scope='usa',  # Focus on the USA
    )
    return fig

def regional_sales_graph(data, start_date, end_date, selected_region):
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
        labels={'x': 'Month', 'y': 'Sales'}
    )
    return fig

def ship_mode_distribution(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    orders_grouped = filtered_sales.groupby('Order_ID').agg({'Ship_Mode' : 'first'})
    ship_mode_counts = orders_grouped['Ship_Mode'].value_counts().reset_index()
    ship_mode_counts.columns = ['Ship_Mode', 'Count']  # Rename columns
    fig = px.pie(ship_mode_counts, names='Ship_Mode', values='Count', title='Distribution of Ship Modes')
    return fig

def shipping_time_by_mode(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    fig = px.box(filtered_sales, x='Ship_Mode', y='Shipping_Time',
                 title='Shipping Time Distribution by Ship Mode',
                 labels={'Ship_Mode': 'Shipping Mode', 'Shipping_Time': 'Shipping Time (days)'})

    return fig

def ship_mode_by_segment(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    order_ship_mode = filtered_sales.groupby(['Order_ID', 'Segment'])['Ship_Mode'].agg(lambda x: x.mode()[0]).reset_index()
    ship_mode_preference = order_ship_mode.groupby(['Segment', 'Ship_Mode']).size().reset_index(name='Count')
    total_per_segment = ship_mode_preference.groupby('Segment')['Count'].transform('sum')
    ship_mode_preference['Percentage'] = (ship_mode_preference['Count'] / total_per_segment) * 100
    fig = px.bar(
        ship_mode_preference,
        x='Segment',
        y='Percentage',  # Use Percentage instead of Count for the y-axis
        color='Ship_Mode',
        title='Ship Mode Preferences by Segment (Percentage)',
        labels={'Segment': 'Client Segment', 'Percentage': 'Percentage (%)'},
        barmode='stack',  # Stacked bar chart to show percentage breakdown
        category_orders={'Segment': ['Corporate', 'Home Office', 'Consumer']}  # Optional: Control segment order
    )

    # Customize the layout (optional)
    fig.update_layout(
        yaxis_tickformat=".1f",  # Format the y-axis as percentages (e.g., 25.0%)
        yaxis_title="Percentage (%)",
        xaxis_title="Client Segment",
        legend_title="Ship Mode",
    )
    return fig




