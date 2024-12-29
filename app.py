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
                            dcc.RadioItems(
                                id='graph-selector',
                                options=[
                                    {'label': 'Total Segment Sales', 'value': 'total'},
                                    {'label': 'Mean Segment Sales', 'value': 'mean'}
                                ],
                                value='total',  # Default value
                                labelStyle={'display': 'block'}
                            ),
                        ]),
                        dbc.Row([
                            dcc.Graph(id='segment-sales-graph')
                        ])
                    ], width=6)
                ]),

                dbc.Row([
                    dbc.Col([
                        html.H4(id='top-customers'),
                    ], width=6),

                    dbc.Col([
                        dcc.Graph(id='abc-analysis-customers')
                    ], width=6)
                ]),

                html.H4("Product insights"),

                dbc.Row([
                    html.Div([
                        html.Label("Select Date Range:"),
                        dcc.DatePickerRange(
                            id='date-range-picker-products',
                            start_date='2017-01-01',  # Default start date
                            end_date='2023-12-31',    # Default end date
                            display_format='YYYY-MM-DD',
                            style={'width': '50%', 'marginTop': '10px'}
                        ),
                    ]),
                    dcc.Graph(id='pareto-graph')
                ]),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='categories-performance-graph')
                    ], width=10)
                ]),

                dbc.Row([
                    dcc.Graph(id='long-tail-bubble-graph')
                ]),

                html.H4("Regional insights"),
                html.Div([
                    html.Label("Select Date Range:"),
                    dcc.DatePickerRange(
                        id='date-range-picker-regions',
                        start_date='2017-01-01',  # Default start date
                        end_date='2023-12-31',    # Default end date
                        display_format='YYYY-MM-DD',
                        style={'width': '50%', 'marginTop': '10px'}
                    ),
                ]),
                dbc.Row([
                    dcc.Dropdown(
                        id='region-selector',
                        options=[{'label': 'West', 'value': 'West'},
                                 {'label': 'East', 'value': 'East'},
                                 {'label': 'Central', 'value': 'Central'},
                                 {'label': 'South', 'value': 'South'},
                                 {'label': 'All', 'value': 'All'}],
                        value= 'All',  # Default value
                        style={'width': '50%'}
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Row([
                            dcc.Graph(id='map-graph')
                        ]),
                        dbc.Row([
                            dcc.Graph(id='regional-sales-graph')
                        ])

                    ], width=6),
                    dbc.Col([
                        dbc.Row([
                            dcc.Graph(id='top-states-graph')
                        ]),
                        dbc.Row([
                            dcc.Graph(id='top-cities-graph')
                        ]),
                    ]),
                ]),

                html.H4('Operational insights'),

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
     Output('segment-sales-graph', 'figure'),
     Output('repeat-customer-rate', 'children'),
     Output('top-customers', 'children'),
     Output('abc-analysis-customers', 'figure'),
     Output('pareto-graph', 'figure'),
     Output('date-range-picker-products', 'start_date'),
     Output('date-range-picker-products', 'end_date'),
     Output('categories-performance-graph', 'figure'),
     Output('long-tail-bubble-graph', 'figure'),
     Output('date-range-picker-regions', 'start_date'),
     Output('date-range-picker-regions', 'end_date'),
     Output('top-states-graph', 'figure'),
     Output('top-cities-graph', 'figure'),
     Output('map-graph', 'figure'),
     Output('regional-sales-graph', 'figure')],
     [Input('upload-data', 'contents'),
      Input('forecast-period', 'value'),
      Input('date-range-picker', 'start_date'),
      Input('date-range-picker', 'end_date'),
      Input('date-range-picker-customer', 'start_date'),
      Input('date-range-picker-customer', 'end_date'),
      Input('graph-selector', 'value'),
      Input('date-range-picker-products', 'start_date'),
      Input('date-range-picker-products', 'end_date'),
      Input('date-range-picker-regions', 'start_date'),
      Input('date-range-picker-regions', 'end_date'),
      Input('region-selector', 'value')],
     State('upload-data', 'filename')
)
def update_output(contents, forecast_period, start_date, end_date, start_date_c, end_date_c, selected_graph, start_date_p, end_date_p, start_date_r, end_date_r, selected_region, filename):
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

            if not start_date_p and not end_date_p:
                start_date_p, end_date_p = generate_default_dates(sales)

            if not start_date_r and not end_date_r:
                start_date_r, end_date_r = generate_default_dates(sales)

            # Create a graph based on the date picker
            sales_graph = create_graph(sales, start_date, end_date)

            # Calculate total sales based on the date picker
            total_r = total_revenue(sales, start_date, end_date)

            av_growth, av_growth_message = average_growth(sales, start_date, end_date)
            sales_weekday_fig, orders_weekday_fig = create_weekday_sales_graph(sales, start_date, end_date), create_weekday_orders_graph(sales, start_date, end_date)
            customer_cohorts_fig, cohort_triangle_table = customer_cohorts(sales)
            customer_segments_graph = customer_segments(sales, start_date_c, end_date_c)
            segment_sales_fig = sales_per_segments(sales, start_date_c, end_date_c, selected_graph)
            rpr = repeat_customer_rate(sales, start_date_c, end_date_c)
            top_10 = top_clients(sales, start_date_c, end_date_c)
            abc_cust = abc_customers(sales, start_date_c, end_date_c)
            pareto_fig = pareto_products(sales, start_date_p, end_date_p)
            cat_performance = category_perfomance(sales, start_date_p, end_date_p)
            lt_bubble = long_tail_analysis(sales, start_date_p, end_date_p)
            fig_states, fig_cities = top_states_and_cities(sales, start_date_r, end_date_r, selected_region)
            map_fig = regional_top_states(sales, start_date_r, end_date_r, selected_region)
            regional_sales_fig = regional_sales_graph(sales, start_date_r, end_date_r, selected_region)
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
                    start_date_c, end_date_c, segment_sales_fig, rpr, top_10, abc_cust, pareto_fig, start_date_p, end_date_p, cat_performance, lt_bubble,
                    start_date_r, end_date_r, fig_states, fig_cities, map_fig, regional_sales_fig)

    return html.Div("No file uploaded yet."), "", html.Div("No forecast available."), "N/A", "N/A", "", {}, {}, {}, "", "", {}, "", {}, "", "", {}, "", "", {}, {}, "", "", {}, {}, "", "", {}, {}, {}, {}



#----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=True)


