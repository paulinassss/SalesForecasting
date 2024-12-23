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
from utils import preprocess_data, generate_monthly_sales, train_model, forecast_sales

# Load your pre-trained model
# ??

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
                html.H3("Dashboard will be displayed here")
                # dashboard content here later
            ])
        ]),
    ]),
])
#----------------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------- FUNCTIONS -----------------------------------------------------------------
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

    return html.Div([
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            page_size=10
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])
#----------------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------- CALLBACKS -----------------------------------------------------------------
@callback(
    [Output('output-data-upload', 'children'),
     Output('output-filename', 'children')],
     Input('upload-data', 'contents'),
     State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is not None:
        return parse_contents(contents, filename), f"File Uploaded: {filename}"
    return html.Div("No file uploaded yet."), ""
#----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run_server(debug=True)
