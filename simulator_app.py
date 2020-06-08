import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from src.app import app, server
from src.layouts import tab1_content, tab2_content
import src.callbacks


# app layout 
app.layout = dbc.Container(
    [   
        html.H1("Covid-19 contact simulator"),
        html.Hr(),
        dcc.Tabs(
        [
            dcc.Tab(tab1_content, id ="tab-1", label="Simulator"),
            dcc.Tab(tab2_content, id ="tab-2", label="Statistics"),
        ],

        id="tabs"),
        
    ],

    fluid=True,
)

if __name__ == '__main__':
    app.run_server(debug=True, port=8000)