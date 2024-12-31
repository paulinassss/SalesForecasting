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
app.layout = dbc.Container([
    html.H1("Sales Analysis and Forecast Application", style={'textAlign': 'center'}),
    dbc.Row([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select a file')
            ], className='regularText'),
            multiple=False,
            className = 'upload', style={'background-color': '#E9F0FFFF'}
        ),
    ], justify='center'),
    html.Div(id='output-filename', className='regularText centeredText', style={'margin': '5px'}),

    # Tabs - first one displays a table of data that user has sent, other displays the dashboard
        dcc.Tabs(
            parent_className='customTabs',
            style = {
                'height': '5vh',
            },
            children=[
            # Tab 1: Display uploaded data
            dcc.Tab(label='Uploaded Data', style = {
                'line-height': '5vh', 'padding': '0', 'background-color': '#DEE4F3FF', 'color': '#0c315e', 'border': 'none',
                }, selected_style= {
                'line-height': '5vh', 'padding': '0', 'background-color': '#E9F0FFFF', 'color': '#0c315e',
                },
                children=[
                html.Div(children=[
                    html.Div([
                        "Uploaded Data Table"
                    ], className='regularText centeredText'),
                    html.Div(id='output-data-upload', className='regularText', style={'margin-left': '5px'})  # The output for the uploaded data
                ])
            ], className='regularText centeredText'),

            # Tab 2: Dashboard (Placeholder for now)
            dcc.Tab(label='Dashboard', style = {
                'line-height': '5vh', 'padding': '0', 'background-color': '#DEE4F3FF', 'color': '#0c315e', 'border': 'none',
                }, selected_style= {
                'line-height': '5vh', 'padding': '0', 'background-color': '#E9F0FFFF', 'color': '#0c315e',
                },children=[
                html.Div(style={'marginLeft': '10px'}, children=[
                    html.H2(["Sales Forecast"], className='centeredText'),
                    # Dropdown for selecting forecast period
                    html.Div([
                        html.Label(["Select Forecast Period:"], className='regularText'),
                        dcc.Dropdown(
                            id='forecast-period',
                            style={
                                'backgroundColor': '#F0F4FFFF',
                                'color': '#0c315e',
                                'width': '150px'
                            },
                            options=[
                                {'label': '1 Month', 'value': 1},
                                {'label': '3 Months', 'value': 3},
                                {'label': '6 Months', 'value': 6},
                            ],
                            value=3,  # Default value
                            optionHeight=20,
                            className='regularText',
                            clearable=False
                        ),
                    ], className='inline-container'),
                    html.Div(id='output-forecast', className='regularText', style={
                        'width': '30%'
                    }),
                    html.H2(["General Sales Insights"], className='centeredText'),
                    # Date range selection for graph
                    html.Div([
                        html.Label(["Select Date Range:"], className='regularText'),
                        dcc.DatePickerRange(
                            id='date-range-picker',
                            start_date='2017-01-01',  # Default start date
                            end_date='2023-12-31',    # Default end date
                            display_format='YYYY-MM-DD',
                            className='regularText',
                            day_size=30,
                            clearable=False
                        ),
                    ], className='inline-container'),
                    # Dashboard layout
                    dbc.Row([
                        # Left column: total sales and growth rate
                        dbc.Col([
                            html.Div([
                                    html.Div("Total Revenue", className='regularText centeredText'),
                                    html.Div(id='total-revenue', className='boldText centeredText'),
                            ], className='cube'),

                            html.Div([
                                html.Div("Average Growth Rate", className='regularText'),
                                html.Div(id='growth-rate', className='boldText'),
                                html.Div(id='x-over-x', className='lowkeyText'),
                            ], className='cube'),

                            html.Div([
                                html.Div("Customers", className='regularText'),
                                html.Div(id='customers', className='boldText'),
                            ], className='cube'),

                            html.Div([
                                html.Div("Orders", className='regularText'),
                                html.Div(id='orders', className='boldText'),
                            ], className='cube')
                        ], width=2),
                        # Right column - a graph
                        dbc.Col([
                            dcc.Graph(id='sales-graph', style={
                                'margin': 'auto',
                                'padding': '0',
                                'height': '50vh',
                            }),
                            dbc.Row([
                                dbc.Col([
                                    # Graph for Most Selling Weekdays
                                    dcc.Graph(id='av-sales-weekday', className='regularText', style={
                                        'padding': '0',
                                        'width': '70vh',
                                        'height': '60vh',
                                    })
                                ], width=6),  # Half-width column for first graph

                                dbc.Col([
                                    # Graph for Most Orders Weekdays
                                    dcc.Graph(id='av-orders-weekday', style={
                                        'padding': '0',
                                        'width': '70vh',
                                        'height': '60vh',
                                    })
                                ], width=6),
                            ]),
                            # Create a row for Most Selling Weekdays and Most Orders Weekdays
                        ], width=10),
                    ]),

                    html.H2(["Customer Insights"], className='centeredText'),
                    dbc.Row([
                        dbc.Col([
                            dbc.Row([
                                html.Div([
                                    html.Label(["Select Date Range:"], className='regularText'),
                                    dcc.DatePickerRange(
                                        id='date-range-picker-customer',
                                        start_date='2017-01-01',  # Default start date
                                        end_date='2023-12-31',    # Default end date
                                        display_format='YYYY-MM-DD',
                                        className='regularText',
                                        day_size=30,
                                        clearable=False
                                    ),
                                ]),
                            ], style={'marginBottom': '10px'}),
                            dbc.Row([
                                dcc.Graph(id='customer-segments', style={
                                        'padding': '0',
                                        'width': '70vh',
                                        'height': '70vh',
                                })
                            ]),
                            dbc.Row([
                                html.Div([
                                    html.Div(["Repeat Customer Rate"], className='regularText centeredText'),
                                    html.Div(id='repeat-customer-rate', className='boldText')
                                ], className='cube')
                            ])
                        ], width=4),
                        dbc.Col([
                            dbc.Row([
                                html.Div([
                                    'Cohort Triangle'
                                ], className='regularText', style={'marginBottom': '5px', 'fontSize': '0.9rem'}),
                                html.Div(id='cohort-triangle')
                            ]),
                            dbc.Row([
                                dcc.Graph(id='customer-cohorts', style={
                                    'height': '70vh'
                                })
                            ])

                        ], width=8),


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
                                    labelStyle={'display': 'block'},
                                    className='regularText'
                                ),
                            ]),
                            dbc.Row([
                                dcc.Graph(id='segment-sales-graph', style={
                                    'height': '30vh'
                                })
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

                    html.H2(["Product insights"], className='centeredText'),

                    dbc.Row([
                        html.Div([
                            html.Label(["Select Date Range:"], className='regularText'),
                            dcc.DatePickerRange(
                                id='date-range-picker-products',
                                start_date='2017-01-01',  # Default start date
                                end_date='2023-12-31',    # Default end date
                                display_format='YYYY-MM-DD',
                                className='regularText',
                                day_size=30,
                                clearable=False
                            ),
                        ], className='inline-container'),
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

                    html.H2(["Regional insights"], className='centeredText'),
                    html.Div([
                        html.Label(["Select Date Range:"], className='regularText'),
                        dcc.DatePickerRange(
                            id='date-range-picker-regions',
                            start_date='2017-01-01',  # Default start date
                            end_date='2023-12-31',    # Default end date
                            display_format='YYYY-MM-DD',
                            className='regularText',
                            day_size=30,
                            clearable=False
                        ),
                    ],className='inline-container'),
                    dbc.Row([
                        dcc.Dropdown(
                            id='region-selector',
                            style={
                                'backgroundColor': '#F0F4FFFF',
                                'color': '#0c315e',
                                'width': '150px'
                            },
                            options=[{'label': 'West', 'value': 'West'},
                                     {'label': 'East', 'value': 'East'},
                                     {'label': 'Central', 'value': 'Central'},
                                     {'label': 'South', 'value': 'South'},
                                     {'label': 'All', 'value': 'All'}],
                            value= 'All',  # Default value
                            optionHeight=10,
                            className='regularText',
                            clearable=False,
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

                    html.H2(['Operational insights'], className='centeredText'),
                    html.Div([
                        html.Label(["Select Date Range:"], className='regularText'),
                        dcc.DatePickerRange(
                            id='date-range-picker-operations',
                            start_date='2017-01-01',  # Default start date
                            end_date='2023-12-31',    # Default end date
                            display_format='YYYY-MM-DD',
                            className='regularText',
                            day_size=30,
                            clearable=False
                        ),
                    ], className='inline-container'),
                    dbc.Row([
                        dbc.Col([
                            dbc.Row([
                                dcc.Graph(id='time-by-mode-boxplot')
                            ]),
                            dbc.Row([
                                dcc.Graph(id='mode-by-segment-barplot')
                            ]),
                        ], width=6),
                        dbc.Col([
                            dcc.Graph(id='mode-distribution-pie')
                        ], width=6)
                    ])
                ])
            ], className='regularText centeredText'),
        ]),
], fluid=True, className='px-0')
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
     Output('regional-sales-graph', 'figure'),
     Output('date-range-picker-operations', 'start_date'),
     Output('date-range-picker-operations', 'end_date'),
     Output('time-by-mode-boxplot', 'figure'),
     Output('mode-by-segment-barplot', 'figure'),
     Output('mode-distribution-pie', 'figure'),
     Output('customers', 'children'),
     Output('orders', 'children')],
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
      Input('region-selector', 'value'),
      Input('date-range-picker-operations', 'start_date'),
      Input('date-range-picker-operations', 'end_date')],
     State('upload-data', 'filename')
)
def update_output(contents, forecast_period, start_date, end_date, start_date_c, end_date_c, selected_graph, start_date_p, end_date_p, start_date_r, end_date_r, selected_region, start_date_o, end_date_o, filename):
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

            if not start_date_o and not end_date_o:
                start_date_o, end_date_o = generate_default_dates(sales)

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
            mode_distribution_fig = ship_mode_distribution(sales, start_date_o, end_date_o)
            time_by_mode_fig = shipping_time_by_mode(sales, start_date_o, end_date_o)
            mode_by_segment_fig = ship_mode_by_segment(sales, start_date_o, end_date_o)
            total_customers, total_orders = total_customers_orders(sales, start_date, end_date)
            # Create Dash table for 1 tab
            data_table = dash_table.DataTable(
                df.to_dict('records'),
                [{'name': i, 'id': i} for i in df.columns],
                page_size=20,
                style_header={
                    'backgroundColor': '#DEE4F3FF',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_cell={'textAlign': 'left', 'fontSize': '0.5rem', 'color': '#0c315e'},
                css=[{'selector': '.dash-spreadsheet tr', 'rule': 'height: 10px;'}],
            )

            # Create table with a forecast
            forecast_table = dash_table.DataTable(
                data=forecast.to_dict('records'),
                columns=[
                    {'name': 'Month', 'id': 'Month_Year'},  # Custom name for 'Month_Year' column
                    {'name': 'Forecasted Sales', 'id': 'Sales'}
                ],
                page_size=10,
                style_header={
                    'backgroundColor': '#DEE4F3FF',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_cell={'textAlign': 'left', 'fontSize': '0.5rem', 'color': '#0c315e'},
                css=[{'selector': '.dash-spreadsheet tr', 'rule': 'height: 10px;'}],
            )
            return (data_table, f"File Uploaded: {filename}", forecast_table, total_r, av_growth, av_growth_message, sales_graph, sales_weekday_fig, orders_weekday_fig,
                    start_date, end_date, customer_cohorts_fig, cohort_triangle_table, customer_segments_graph,
                    start_date_c, end_date_c, segment_sales_fig, rpr, top_10, abc_cust, pareto_fig, start_date_p, end_date_p, cat_performance, lt_bubble,
                    start_date_r, end_date_r, fig_states, fig_cities, map_fig, regional_sales_fig, start_date_o, end_date_o,
                    time_by_mode_fig, mode_by_segment_fig, mode_distribution_fig, total_customers, total_orders)

    return html.Div("No file uploaded yet."), "", html.Div("No forecast available."), "N/A", "N/A", "", {}, {}, {}, "", "", {}, "", {}, "", "", {}, "", "", {}, {}, "", "", {}, {}, "", "", {}, {}, {}, {}, "", "", {}, {}, {}, "N/A", "N/A"



#----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=True)


