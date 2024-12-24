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

from utils import create_graph, total_sales, generate_default_dates, parse_contents, preprocess_data, generate_monthly_sales, train_model, forecast_sales

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
                        html.H4("Total Sales", style={'marginTop': '20px'}),
                        html.Div(id='total-sales', style={'fontSize': '20px', 'marginBottom': '20px'}),

                        html.H4("Growth Rate", style={'marginTop': '20px'}),
                        html.Div(id='growth-rate', style={'fontSize': '20px', 'marginBottom': '20px'}),
                    ], width=4),

                    # Right column - a graph
                    dbc.Col([
                        dcc.Graph(id='sales-graph')
                    ], width=8)
                ]),
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
     Output('total-sales', 'children'),
     #Output('growth-rate', 'children'),
     Output('sales-graph', 'figure'),
     Output('date-range-picker', 'start_date'),
     Output('date-range-picker', 'end_date')],
     [Input('upload-data', 'contents'),
      Input('forecast-period', 'value'),
      Input('date-range-picker', 'start_date'),
      Input('date-range-picker', 'end_date')],
     State('upload-data', 'filename')
)
def update_output(contents, forecast_period, start_date, end_date, filename):
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

            sales_graph = create_graph(sales)
            if not start_date and not end_date:
                start_date, end_date = generate_default_dates(sales)

            total = total_sales(sales, start_date, end_date)

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
            return data_table, f"File Uploaded: {filename}", forecast_table, total, sales_graph, start_date, end_date

    return html.Div("No file uploaded yet."), "", html.Div("No forecast available."), "N/A", {},"",""
#----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=True)


