import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table

# Warnings
import warnings
warnings.filterwarnings('ignore')

custom_colors = ['#A6AEBF', '#C5D3E8', '#D0E8C5', '#A7C5EB', '#9ecbd0', '#cde8e2', '#d7f5e7', '#A6AEBF', '#C5D3E8', '#D0E8C5', '#A7C5EB', '#9ecbd0', '#cde8e2', '#d7f5e7', '#A6AEBF', '#C5D3E8', '#D0E8C5', '#A7C5EB', '#9ecbd0', '#cde8e2', '#d7f5e7']
# def check_integrity(data)

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
        labels={'Month_Year': 'Month', 'Sales': 'Sales'},
    ).update_layout(
        paper_bgcolor='rgb(233, 240, 255)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=25, r=25, t=25, b=25),
        font_family='Inconsolata',
        title=dict(text="Sales over time", font=dict(size=15), automargin=False, yref='paper')
    ).update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
    ).update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
    ).update_traces(
        line=dict(color='#5470a5', width=1))
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
                       labels={'Weekday_Name': 'Weekday', 'Avg_Sales': 'Average Sales ($)'},
                       color='Weekday_Name',
                       color_discrete_sequence=custom_colors).update_layout(
        paper_bgcolor='rgb(233, 240, 255)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=25, r=25, t=25, b=25),
        font_family='Inconsolata',
        title=dict(text="Average sales per Weekday", font=dict(size=15), automargin=False, yref='paper'),
        bargap=0.4
    ).update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
    ).update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff', nticks=10,
        dtick=250,
    )
    fig_sales.update_layout(showlegend=False)
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
    fig_orders.update_layout(showlegend=False)
    return fig_orders

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
        y='Time_Cohort',
        x='Number_of_Customers',
        title='Customer Cohorts by Quarters',
        labels={'Time_Cohort': 'Quarter', 'Number_of_Customers': 'Number of Customers'},
        text='Number_of_Customers',  # Display the number of customers on each bar
        color='Time_Cohort',
        color_discrete_sequence=custom_colors,
        orientation='h'
    )

    # Update the layout to improve appearance
    fig.update_layout(
        xaxis_title='Quarter',
        yaxis_title='Number of Customers',
        showlegend=False,  # Hide the legend, as the color is redundant
        paper_bgcolor='rgb(233, 240, 255)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=25, r=25, t=25, b=25),
        font_family='Inconsolata',
        title=dict(text="Customer cohorts by quarters", font=dict(size=15), automargin=False, yref='paper'),
        bargap=0.4
    ).update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
    ).update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
    ).update_traces(
        textposition='outside',
        textangle=0
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
        style_table={'overflow': 'auto', 'margin': 'auto'},
        style_header={
            'backgroundColor': '#DEE4F3FF',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={'textAlign': 'left', 'fontSize': '0.5rem', 'color': '#0c315e'},
        css=[{'selector': '.dash-spreadsheet tr', 'rule': 'height: 10px;'}],
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
        color_discrete_sequence=custom_colors,
    ).update_layout(
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Customer Distribution by Segment", font=dict(size=15), automargin=False, yref='paper')
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
            labels={'Sales': 'Total Sales ($)', 'Segment': 'Segment'},
            color='Segment',
            color_discrete_sequence=custom_colors
            )
        fig.update_layout(
            paper_bgcolor='rgba(222, 228, 243, 0)',
            plot_bgcolor='rgb(249, 251, 255)',
            margin=dict(l=20, r=20, t=20, b=20),
            font_family='Inconsolata',
            title=dict(text="Total sales per segment", font=dict(size=15), automargin=False, yref='paper'),
            bargap=0.4,
            showlegend=False
        ).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        )
    elif selected_graph == 'mean':
        fig= px.bar(segment_sales,
           x='Mean_Sales_Per_Order',
           y='Segment',
           orientation='h',
           labels={'Mean_Sales_Per_Order': 'Mean order value ($)', 'Segment': 'Segment'},
           color='Segment',
           color_discrete_sequence=custom_colors
        )
        fig.update_layout(
            paper_bgcolor='rgba(222, 228, 243, 0)',
            plot_bgcolor='rgb(249, 251, 255)',
            margin=dict(l=20, r=20, t=20, b=20),
            font_family='Inconsolata',
            title=dict(text="Mean order value per segment", font=dict(size=15), automargin=False, yref='paper'),
            bargap=0.4,
            showlegend=False
        ).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
            dtick=50
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
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
    top_10_clients['Sales'] = top_10_clients['Sales'].apply(lambda x: f"${x:,.2f}")
    table = dash_table.DataTable(
        data=top_10_clients.to_dict('records'),  # Convert DataFrame to dictionary
        columns=[{'name': 'Customer ID', 'id': 'Customer_ID'},
            {'name': 'Name', 'id': 'Customer_Name'},
            {'name': 'Segment', 'id': 'Segment'},
            {'name': 'Sales', 'id': 'Sales'},
            {'name': 'Orders', 'id': 'Number_of_Orders'}],  # Columns for the table
        style_table={'overflow': 'auto', 'margin': 'auto', 'marginLeft': '15px'},
        style_header={
            'backgroundColor': '#DEE4F3FF',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={'textAlign': 'left', 'fontSize': '0.5rem', 'color': '#0c315e'},
        css=[{'selector': '.dash-spreadsheet tr', 'rule': 'height: 10px;'}],
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
            labels={'Sales': 'Total Sales ($)', 'Category_Label': 'Category'},
            color='Customer_Category',
            color_discrete_sequence=custom_colors).update_layout(
            paper_bgcolor='rgba(222, 228, 243, 0)',
            plot_bgcolor='rgb(249, 251, 255)',
            margin=dict(l=20, r=20, t=20, b=20),
            font_family='Inconsolata',
            title=dict(text="ABC Analysis: Total Sales by Category", font=dict(size=15), automargin=False, yref='paper'),
            bargap=0.4,
            showlegend=False
        ).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')

    return fig

def pareto_products(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    product_sales = filtered_sales.groupby('Product_Name')['Sales'].sum().reset_index()
    product_sales = product_sales.sort_values(by='Sales', ascending=False)
    product_sales['%_Contribution'] = (product_sales['Sales'] / product_sales['Sales'].sum()) * 100
    product_sales['Cumulative_%'] = product_sales['%_Contribution'].cumsum()
    top_20_percent_products = product_sales[product_sales['Cumulative_%'] <= 80]
    top_20_percent_products['Short_Product_Name'] = top_20_percent_products['Product_Name'].apply(
        lambda x: f"{x[:10]}..." if len(x) > 20 else x)
    # Create the Pareto chart using Plotly
    fig = go.Figure()
    # Bar chart for the values
    fig.add_trace(go.Bar(
        x=top_20_percent_products['Product_Name'],
        y=top_20_percent_products['Sales'],
        name='Sales',
        hovertemplate='%{x}: %{y}$<br>' +
                      'Cumulative Percentage: %{customdata[0]}%',
        marker=dict(color=custom_colors)
    ))
    # Line chart for the cumulative percentage
    fig.add_trace(go.Scatter(
        x=top_20_percent_products['Product_Name'],
        y=top_20_percent_products['Cumulative_%'],
        name='Cumulative Percentage ($)',
        mode='lines+markers',
        yaxis='y2'
    ))
    # Update layout
    fig.update_layout(
        xaxis_title="Product name",
        yaxis_title="Generated income ($)",
        yaxis2=dict(
            title="Cumulative Percentage (%)",
            overlaying='y',
            side='right',
            #tickformat="%"
        ),
        showlegend=False,
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=22, r=22, t=22, b=22),
        font_family='Inconsolata',
        title=dict(text="Pareto Analysis", font=dict(size=15), automargin=False, yref='paper'),
        bargap=0.4
    ).update_xaxes(
            tickangle=45,
            tickmode='array',
            tickvals=top_20_percent_products['Product_Name'],
            ticktext=top_20_percent_products['Short_Product_Name'],
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
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
    category_sales = category_sales.sort_values(by='Sales', ascending=True)

    # Within each category, sort subcategories by sales in descending order
    subcategory_sales = subcategory_sales.sort_values(by=['Category', 'Sales'], ascending=[True, True])

    ## Combine categories and subcategories into a single DataFrame
    #combined_sales = pd.concat([
    #    category_sales[['Label', 'Sales', 'Type']],
     #   subcategory_sales[['Label', 'Sales', 'Type']]
    #])

    # Create a custom y-axis that groups categories with their subcategories
    y_labels = []
    sales_values = []
    colors = []
    formatted_sales = []  # To store formatted sales values

    for category in category_sales['Label']:

        subcategories = subcategory_sales[subcategory_sales['Category'] == category]
        for _, row in subcategories.iterrows():
            y_labels.append(f"  {row['Label']}")  # Indent for subcategories
            sales = row['Sales']
            sales_values.append(sales)
            colors.append('#9ecbd0')  # Color for subcategory bars
            formatted_sales.append(f"${sales:,.2f}")  # Custom currency formatting

        category_row = category_sales[category_sales['Label'] == category]
        y_labels.append(category)  # Category label
        sales = category_row['Sales'].values[0]
        sales_values.append(sales)
        colors.append('#A6AEBF')  # Color for category bars
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
        xaxis_title="Sales",
        yaxis_title="Categories and Subcategories",
        xaxis=dict(tickformat='$,.2f', range=[0, 950000]),  # Format x-axis as currency
        showlegend=False,
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Category and Subcategory Performance", font=dict(size=15), automargin=False, yref='paper'),
        bargap=0.4,
    ).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff'
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
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
        size_max=50,
        color_discrete_sequence=['#A7C5EB']
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

    fig.update_layout(
        showlegend=False,
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Long-tail Analysis (Number of products by number of customers)", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        ).update_xaxes(
            dtick=1,
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

    fig_states = px.bar(top_states, y='State', x='Sales',
                        title='Top 5 Selling States',
                        labels={'State': 'State', 'Sales': 'Total Sales'},
                        color='State',
                        color_discrete_sequence=custom_colors,
                        orientation='h').update_layout(
                                paper_bgcolor='rgba(222, 228, 243, 0)',
                                plot_bgcolor='rgb(249, 251, 255)',
                                margin=dict(l=25, r=25, t=25, b=25),
                                font_family='Inconsolata',
                                showlegend=False,
                                title=dict(text="Top 5 selling states", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
                                    showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                                ).update_yaxes(
                                    showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                                ).update_xaxes(
                                    dtick=50000
                                )
    # Create Bar Chart for Top 5 Cities by Sales
    fig_cities = px.bar(top_cities, y='City', x='Sales',
                        title='Top 5 Selling Cities',
                        labels={'City': 'City', 'Sales': 'Total Sales'},
                        color='City',
                        color_discrete_sequence=custom_colors,
                        orientation='h').update_layout(
                                paper_bgcolor='rgba(222, 228, 243, 0)',
                                plot_bgcolor='rgb(249, 251, 255)',
                                margin=dict(l=25, r=25, t=25, b=25),
                                font_family='Inconsolata',
                                showlegend=False,
                                title=dict(text="Top 5 selling cities", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
                                    showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                                ).update_yaxes(
                                    showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                                ).update_xaxes(
                                   dtick=50000
                                )
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
    ).update_layout(
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Top - selling states", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
        ).update_yaxes(
            showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
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

def ship_mode_distribution(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    orders_grouped = filtered_sales.groupby('Order_ID').agg({'Ship_Mode' : 'first'})
    ship_mode_counts = orders_grouped['Ship_Mode'].value_counts().reset_index()
    ship_mode_counts.columns = ['Ship_Mode', 'Count']  # Rename columns
    fig = px.pie(ship_mode_counts, names='Ship_Mode', values='Count', color_discrete_sequence = custom_colors, color='Ship_Mode').update_layout(
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Ship modes distribution", font=dict(size=15), automargin=False, yref='paper'),
    )
    return fig

def shipping_time_by_mode(data, start_date, end_date):
    filtered_sales = data[(data['Order_Date'] >= start_date) & (data['Order_Date'] <= end_date)]
    fig = px.box(filtered_sales, x='Ship_Mode', y='Shipping_Time',
                 title='Shipping Time Distribution by Ship Mode',
                 labels={'Ship_Mode': 'Shipping Mode', 'Shipping_Time': 'Shipping Time (days)'},
                 color_discrete_sequence=['#0c315e']).update_layout(
                    paper_bgcolor='rgba(222, 228, 243, 0)',
                    plot_bgcolor='rgb(249, 251, 255)',
                    margin=dict(l=20, r=20, t=20, b=20),
                    font_family='Inconsolata',
                    title=dict(text="Shipping time distribution by ship mode", font=dict(size=15), automargin=False, yref='paper')).update_xaxes(
                        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                    ).update_yaxes(
                        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
                    ).update_traces(
                        whiskerwidth=0.5,
                        line_width=1
                    )
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
        color_discrete_sequence=custom_colors,
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
        paper_bgcolor='rgba(222, 228, 243, 0)',
        plot_bgcolor='rgb(249, 251, 255)',
        margin=dict(l=20, r=20, t=20, b=20),
        font_family='Inconsolata',
        title=dict(text="Ship mode preferencies by segment", font=dict(size=15), automargin=False,
                   yref='paper')).update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
    ).update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='#e9f0ff',
    )
    return fig




