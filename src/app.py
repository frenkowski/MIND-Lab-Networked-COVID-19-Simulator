import dash_bootstrap_components as dbc
import dash
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Covid-19 contact simulator'

server = app.server