import dash
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import joblib
import os
import datetime
import io
import base64

from jedi.api.refactoring import inline

from utils import *

# Initialize the dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#------------------------------------------------------- LAYOUT -----------------------------------------------------------------
app.layout = html.Div([
    html.H1("Sales Analysis and Forecast Application", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a file')
        ]),
        multiple=False,
        style={
            'width': '80%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }
    ),
    html.Div(id='output-filename', style={'margin': '10px', 'fontSize': '15px'}),

    # Tabs - first one displays a table of data that user has sent, other displays the dashboard
    dcc.Tabs(
        style={'width': '80%', 'marginLeft': '10px'},
        children=[
        # Tab 1: Display uploaded data
        dcc.Tab(label='Uploaded Data', children=[
            html.Div(style={'marginLeft': '10px'}, children=[
                html.H3("Uploaded Data Table"),
                html.Div(id='output-data-upload')  # The output for the uploaded data
            ])
        ]),

        # Tab 2: Dashboard (Placeholder for now)
        dcc.Tab(label='Dashboard', children=[
            html.Div(style={'marginLeft': '10px'}, children=[
                html.H3("Insights Dashboard"),
                html.H4("Sales Forecast"),
                # Dropdown for selecting forecast period
                html.Div([
                    html.Label("Select Forecast Period:"),
                    dcc.Dropdown(
                        id='forecast-period',
                        options=[
                            {'label': '1 Month', 'value': 1},
                            {'label': '3 Months', 'value': 3},
                            {'label': '6 Months', 'value': 6},
                        ],
                        value=3,  # Default value
                        style={'width': '50%', 'marginTop': '10px'}
                    ),
                ]),
                html.Div(id='output-forecast'),
                html.H4("General Sales Insights"),
                # Date range selection for graph
                html.Div([
                    html.Label("Select Date Range:"),
                    dcc.DatePickerRange(
                        id='date-range-picker',
                        start_date='2017-01-01',  # Default start date
                        end_date='2023-12-31',    # Default end date
                        display_format='YYYY-MM-DD',
                        style={'width': '50%', 'marginTop': '10px'}
                    ),
                ]),
                # Dashboard layout
                dbc.Row([
                    # Left column: total sales and growth rate
                    dbc.Col([
                        html.H4("Total Revenue", style={'marginTop': '20px'}),
                        html.Div(id='total-revenue', style={'fontSize': '20px', 'marginBottom': '20px'}),

                        html.H4("Average Growth Rate", style={'marginTop': '20px'}),
                        html.Div(id='growth-rate', style={'fontSize': '20px', 'marginBottom': '20px'}),
                        html.Div(id='x-over-x', style={'fontSize': '20px', 'marginBottom': '20px'})
                    ], width=2),

                    # Right column - a graph
                    dbc.Col([
                        dcc.Graph(id='sales-graph'),
                        # Create a row for Most Selling Weekdays and Most Orders Weekdays
                        dbc.Row([
                            dbc.Col([
                                # Graph for Most Selling Weekdays
                                dcc.Graph(id='av-sales-weekday')
                            ], width=6),  # Half-width column for first graph

                            dbc.Col([
                                # Graph for Most Orders Weekdays
                                dcc.Graph(id='av-orders-weekday')
                            ], width=6),  # Half-width column for second graph
                        ])
                    ], width=10)
                ]),
                html.H4("Customer Insights"),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='customer-cohorts')
                    ], width=4, style={'padding': '0px', 'margin': '0px'}),

                    dbc.Col([
                        html.Div(id='cohort-triangle')
                    ], width=8, style={'padding': '0px'})
                ]),
                dbc.Row([
                    html.Div([
                        html.Label("Select Date Range:"),
                        dcc.DatePickerRange(
                            id='date-range-picker-customer',
                            start_date='2017-01-01',  # Default start date
                            end_date='2023-12-31',    # Default end date
                            display_format='YYYY-MM-DD',
                            style={'width': '50%', 'marginTop': '10px'}
                        ),
                    ]),

                    # Pie plot
                    dbc.Col([
                        dbc.Row([
                            dcc.Graph(id='customer-segments')
                        ]),
                        dbc.Row([
                            html.Div("Repeat Customer Rate"),
                            html.Div(id='repeat-customer-rate')
                        ])
                    ], width=6),

                    # Horizontal bar plot
                    dbc.Col([
                        dbc.Row([
                            dcc.Graph(id='total-segment-sales')
                        ]),
                        dbc.Row([
                            dcc.Graph(id='mean-segment-sales')
                        ])
                    ])
                ]),

                dbc.Row([
                    html.H4(id='top-customers'),
                ]),

                html.H4("Product insights")

            ])
        ]),
    ]),
])
#----------------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------- CALLBACKS -----------------------------------------------------------------
@callback(
    [Output('output-data-upload', 'children'),
     Output('output-filename', 'children'),
     Output('output-forecast', 'children'),
     Output('total-revenue', 'children'),
     Output('growth-rate', 'children'),
     Output('x-over-x', 'children'),
     Output('sales-graph', 'figure'),
     Output('av-sales-weekday', 'figure'),
     Output('av-orders-weekday', 'figure'),
     Output('date-range-picker', 'start_date'),
     Output('date-range-picker', 'end_date'),
     Output('customer-cohorts', 'figure'),
     Output('cohort-triangle', 'children'),
     Output('customer-segments', 'figure'),
     Output('date-range-picker-customer', 'start_date'),
     Output('date-range-picker-customer', 'end_date'),
     Output('total-segment-sales', 'figure'),
     Output('mean-segment-sales', 'figure'),
     Output('repeat-customer-rate', 'children'),
     Output('top-customers', 'children')],
     [Input('upload-data', 'contents'),
      Input('forecast-period', 'value'),
      Input('date-range-picker', 'start_date'),
      Input('date-range-picker', 'end_date'),
      Input('date-range-picker-customer', 'start_date'),
      Input('date-range-picker-customer', 'end_date')],
     State('upload-data', 'filename')
)
def update_output(contents, forecast_period, start_date, end_date, start_date_c, end_date_c, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if isinstance(df, pd.DataFrame):
            # Preprocess data
            sales = preprocess_data(df)
            # Generate monthly_sales dataset
            monthly_sales = generate_monthly_sales(sales)
            # Train the model
            rf_model, mae, rmse, x_test = train_model(monthly_sales)

            # Generate the forecast
            forecast = forecast_sales(rf_model, monthly_sales, x_test, forecast_period)

            if not start_date_c and not end_date_c:
                start_date_c, end_date_c = generate_default_dates(sales)

            if not start_date and not end_date:
                start_date, end_date = generate_default_dates(sales)

            # Create a graph based on the date picker
            sales_graph = create_graph(sales, start_date, end_date)

            # Calculate total sales based on the date picker
            total_r = total_revenue(sales, start_date, end_date)

            av_growth, av_growth_message = average_growth(sales, start_date, end_date)
            sales_weekday_fig, orders_weekday_fig = create_weekday_sales_graph(sales, start_date, end_date), create_weekday_orders_graph(sales, start_date, end_date)
            customer_cohorts_fig, cohort_triangle_table = customer_cohorts(sales)
            customer_segments_graph = customer_segments(sales, start_date_c, end_date_c)
            total_segment_fig, mean_segment_fig = sales_per_segments(sales, start_date_c, end_date_c)
            rpr = repeat_customer_rate(sales, start_date_c, end_date_c)
            top_10 = top_clients(sales, start_date_c, end_date_c)


            # Create Dash table for 1 tab
            data_table = dash_table.DataTable(
                df.to_dict('records'),
                [{'name': i, 'id': i} for i in df.columns],
                page_size=10
            )

            # Create table with a forecast
            forecast_table = dash_table.DataTable(
                data=forecast.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in forecast.columns],
                page_size=10
            )
            return (data_table, f"File Uploaded: {filename}", forecast_table, total_r, av_growth, av_growth_message, sales_graph, sales_weekday_fig, orders_weekday_fig,
                    start_date, end_date, customer_cohorts_fig, cohort_triangle_table, customer_segments_graph,
                    start_date_c, end_date_c, total_segment_fig, mean_segment_fig, rpr, top_10)

    return html.Div("No file uploaded yet."), "", html.Div("No forecast available."), "N/A", "N/A", "", {}, {}, {}, "", "", {}, "", {}, "", "", {}, {}, "", ""



#----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=True)


