import glob
import os
import pickle
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from collections import Counter
import igraph as ig
import statistics as stat

from pathlib import Path


# used to run simulation
from ctns.contact_network_simulator import run_simulation


# statistic to plot
age_range = ["0-9", "10-19", "20-29", "30-39",
             "40-49", "50-59", "60-69", "70-79", "80-89", "90+"]
age_prob = [0.084, 0.096, 0.102, 0.117,
            0.153, 0.155, 0.122, 0.099, 0.059, 0.013]
age_fat_rate = [0.002,  0.001, 0.001, 0.004,
                0.009, 0.026, 0.10, 0.249, 0.308, 0.261]


age_prob = [prob * 100 for prob in age_prob]
age_fat_rate = [prob*100 for prob in age_fat_rate]

avg_fat = stat.mean(age_fat_rate)


# begin layout app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Covid-19 contact simulator'


server = app.server

# form layout
form = dbc.Card(
    [
        html.H3("Initial simulation parameters "),
        html.Br(),
        dbc.FormGroup(
            [
                dbc.Label("Number of families: "),
                dbc.Input(id="n_of_families", type="number",
                          value=500, min=100),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Number of initial exposed people:"),
                dbc.Input(id="n_initial_infected_nodes",
                          type="number", value=5, min=1),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Simulation days:"),
                dbc.Input(id="number_of_steps",
                          type="number", value=150, min=10),
            ]
        ),

        html.Br(),
        html.H3("Epidemic parameters"),
        html.Br(),
        dbc.FormGroup(
            [
                dbc.Label("Incubation days: "),
                dbc.Input(id="incubation_days", type="number", value=5, min=1),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Desease duration:"),
                dbc.Input(id="infection_duration",
                          type="number", value=21, min=1),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("R_0:"),
                dbc.Input(id="R_0", type="number", value=2.9,
                          min=0, max=10, step=0.1),
            ]
        ),

        html.Br(),
        html.H3("Social restriction parameters"),
        html.Br(),
        dbc.FormGroup(
            [

                dbc.Label("Intial day restriction:"),
                dbc.Input(id="initial_day_restriction",
                          type="number", value=35, min=1),
            ]
        ),

        dbc.FormGroup(
            [

                dbc.Label("Duration of restriction:"),
                dbc.Input(id="restriction_duration",
                          type="number", value=28, min=0),
            ]
        ),



        dbc.FormGroup(
            [

                dbc.Label("Social distance strictness:"),
                html.Div(dcc.Slider(id="social_distance_strictness",
                                    value=2, min=0, max=4,
                                    # step=None,
                                    marks={
                                        0: {'label': '0%', 'style': {'color': '#f50'}},
                                        1: {'label': '25%'},
                                        2: {'label': '50%'},
                                        3: {'label': '75%'},
                                        4: {'label': '100%', 'style': {'color': '#77b0b1'}}
                                    },
                                    vertical=False,
                                    ),
                         style={'width': '100%', 'display': 'block'},
                         )
            ]
        ),

        dbc.FormGroup(
            [

                dbc.Label("Decreasing restrionction:"),
                dbc.Checklist(
                    options=[
                        {"label": "", "value": 1},
                    ],
                    value=[],
                    id="restriction_decreasing",
                    switch=True,
                ),
            ]
        ),


        html.Br(),
        html.H3("Quarantine parameters"),
        html.Br(),

        dbc.FormGroup(
            [

                dbc.Label("Daily number of test:"),
                dbc.Input(id="n_test", type="number", value=0, min=0),
            ]
        ),


        dbc.FormGroup(
            [

                dbc.Label("Policy test:"),
                dcc.Dropdown(
                    id="policy_test",
                    options=[
                        {"label": col, "value": col} for col in ['Random', 'Degree Centrality', 'Betweenness Centrality']
                    ],
                    value="Random",
                    clearable=False
                ), ]
        ),

        dbc.FormGroup(
            [

                dbc.Label("Contact tracing efficiency:"),
                html.Div(dcc.Slider(id="contact_tracking_efficiency",
                                    value=80, min=0, max=100, step=10,
                                    # step=None,
                                    marks={
                                        0: {'label': '0%', 'style': {'color': '#f50'}},
                                        50: {'label': '50%'},
                                        100: {'label': '100%', 'style': {'color': '#77b0b1'}}
                                    },
                                    vertical=False,
                                    ),
                         style={'width': '100%', 'display': 'block'},
                         )
            ]
        ),

        html.Br(),
        dbc.FormGroup(
            [

                dbc.Button("Run simulation", id="run_sim",
                           color="primary", className="mr-1", block=True),
                html.Br(),
                dbc.Alert("Check the value of parameters",
                          id='alert_id', color="danger", is_open=False),
            ]
        ),
    ],
    body=True,
    style={'background-color': '#f2f2f2', 'border-radius': '4px',
           'box-shadow': '2px 2px 2px lightgrey'},
)


tab1_content = dbc.Card(
    dbc.CardBody(
        [

            dbc.Row(
                [
                    dbc.Col(form, md=4),
                    dbc.Col([
                        dbc.Container([
                            html.Br(),
                            html.H3("Simulation results"),
                            html.Hr(),
                            dbc.Spinner(dcc.Graph(id="graph_sim", style={
                                'display': 'block'}), color="primary"),
                            html.Br(),
                            dbc.Spinner(dcc.Graph(id="graph_sim_without_restr", style={
                                'display': 'block'}), color="primary"),
                            html.Br(),
                        ], fluid=True),
                    ], style={'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'},
                        md=7),

                ],
                align="center",
            ),

            html.Div(style={'margin-top': '60px'}),
            dbc.Container(id="div", children=[

                dbc.Row(

                    [
                        dbc.Col([
                            html.Br(),
                            html.H3("Comparison Results"),
                            html.Hr(),
                        ], md=12),
                    ]
                ),

                dbc.Row(
                    [
                        html.Br(),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_infected", style={
                            'display': 'block'}), color="primary"), html.Br()], md=6),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_dead", style={
                            'display': 'block'}), color="primary"), html.Br()], md=6),

                    ],
                    align="center"),

            ], fluid=True, style={'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}),

            html.Div(style={'margin-top': '60px'}),

            dbc.Container(id="div_2", children=[

                dbc.Row(

                    [
                        dbc.Col([
                            html.Br(),
                            html.H3(
                                "Daily results with and without restriction"),
                            html.Hr(),
                        ], md=12),
                    ]
                ),

                dbc.Row(
                    [
                        html.Br(),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_Inf_daily", style={
                                'display': 'block'}), color="primary"), html.Br()], width=6),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_dead_daily", style={
                                'display': 'block'}), color="primary"), html.Br()], width=6),

                    ],
                    align="center",
                ),

            ], style={'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}, fluid=True),

            html.Div(style={'margin-top': '60px'}),

            dbc.Container(id="div_comparison", children=[

                dbc.Row(

                    [
                        dbc.Col([
                            html.Br(),
                            html.H3(
                                "Total infected with and without restriction"),
                            html.Hr(),
                        ], md=12),
                    ]
                ),

                dbc.Row(
                    [
                        html.Br(),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_total_infected", style={
                                'display': 'block'}), color="primary"), html.Br()], width=12),
                    ],
                    align="center",
                ),

            ], style={'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}),

            html.Div(style={'margin-top': '60px'}),
            dbc.Container(id="div_tamponi", children=[

                dbc.Row(

                    [
                        dbc.Col([
                            html.Br(),
                            html.H3("Tests and Quarantine results"),
                            html.Hr(),
                        ], md=12),
                    ]
                ),

                dbc.Row(
                    [
                        html.Br(),
                        dbc.Col([dbc.Spinner(dcc.Graph(id="graph_test", style={
                                'display': 'block'}), color="primary"), html.Br()], width=12),
                    ],
                    align="center",
                ),

            ], style={'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}, fluid=True),

            html.Div(style={'margin-top': '60px'}),
        ]
    ),
    className="mt-3",
)


# statistics tab
tab2_content = dbc.Container(
    [


        html.Br(),
        html.H3("Italian population age and fatality rate distribution"),
        html.Hr(),
        dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id='age_graph',
                        figure={
                            'data': [
                                {'x': age_range, 'y': age_prob, 'type': 'bar'}
                            ],
                            'layout': {
                                'title': 'Italian population age distribution',
                                'xaxis': {'title': 'Age'},
                                'yaxis': {'title': 'Population percentage'},
                            }
                        }
                    ),
                    html.Br(),
                    html.P("Source: ", style={'display': 'inline '}),
                    html.A('http://dati.istat.it/',
                           href='http://dati.istat.it/', target="_blank"),
                ], md=6),

                dbc.Col([
                    dcc.Graph(
                        id='age_graph_death_rate',
                        figure={
                            'data': [
                                {'x': age_range, 'y': age_fat_rate, 'type': 'bar', 'marker': {
                                    'color': '#f50'}, 'name': 'Fatality rate'},
                                {'x': [age_range[0], age_range[len(age_range) - 1]], 'y': [avg_fat, avg_fat], 'type': 'scatter', 'line': dict(
                                    color='rgb(20, 53, 147)', dash='dot'), 'name': 'Average Fatality'}
                            ],
                            'layout': {
                                'title': 'Fatality rate age distribution',
                                'xaxis': {'title': 'Age'},
                                'yaxis': {'title': 'Fatality rate'},

                            }
                        }
                    ),
                    html.Br(),

                    html.P("Source: ", style={'display': 'inline '}),
                    html.A('https://www.epicentro.iss.it',
                           href='https://www.epicentro.iss.it/coronavirus/sars-cov-2-sorveglianza-dati', target="_blank"),

                ], md=6),


                ],
                align="center"
                ),

        html.Div(style={'margin-top': '60px'}),


    ],

    fluid=True,
    style={'background-color': '#f2f2f2', 'border-radius': '4px',
           'box-shadow': '2px 2px 2px lightgrey'}
)


app.layout = dbc.Container(
    [
        html.H1("Covid-19 contact simulator"),
        html.Hr(),
        dcc.Tabs(
            [
                dcc.Tab(tab1_content, id="tab-1", label="Simulator"),
                dcc.Tab(tab2_content, id="tab-2", label="Statistics"),
            ],

            id="tabs"),

    ],

    fluid=True,
)


@app.callback(
    [Output('graph_sim', 'figure'),
        Output('graph_sim_without_restr', 'figure'),
        Output('graph_infected', 'figure'),
        Output('graph_dead', 'figure'),
        Output('graph_Inf_daily', 'figure'),
        Output('graph_dead_daily', 'figure'),
        Output('graph_total_infected', 'figure'),
        Output('graph_test', 'figure'),

        Output('graph_sim', 'style'),
        Output('graph_sim_without_restr', 'style'),
        Output('graph_infected', 'style'),
        Output('graph_dead', 'style'),
        Output('graph_Inf_daily', 'style'),
        Output('graph_dead_daily', 'style'),
        Output('graph_total_infected', 'style'),
        Output('graph_test', 'style'),
     ],

    [Input("run_sim", "n_clicks")],

    [State('n_of_families', 'value'),
        State('number_of_steps', 'value'),
        State('n_initial_infected_nodes', 'value'),
        State('incubation_days', 'value'),
        State('infection_duration', 'value'),
        State('R_0', 'value'),
        State('initial_day_restriction', 'value'),
        State('restriction_duration', 'value'),
        State('social_distance_strictness', 'value'),
        State('restriction_decreasing', 'value'),
        State('n_test', 'value'),
        State('policy_test', 'value'),
        State('contact_tracking_efficiency', 'value')]
)
def updateSimulation(n_clicks, n_of_families, number_of_steps, n_initial_infected_nodes, incubation_days, infection_duration, R_0, initial_day_restriction, restriction_duration, social_distance_strictness, restriction_decreasing, n_test, policy_test, contact_tracking_efficiency):
    if n_clicks is not None:

        path = Path("network_dumps")

        '''
        
        print("--------parameters--------")
        print("n_of_families ", n_of_families,)
        print("number_of_steps ",  number_of_steps)
        print("incubation_days ", incubation_days)
        print("infection_duration ", infection_duration)
        print("initial_day_restriction ", initial_day_restriction)
        print("restriction_duration ", restriction_duration)
        print("social_distance_strictness", social_distance_strictness)
        print("restriction_decreasing", restriction_decreasing)
        print("n_initial_infected_nodes", n_initial_infected_nodes)
        print("R_0", R_0)
        print("n_test ", n_test)
        print("policy_test ", policy_test)
        print("contact_tracking_efficiency ", contact_tracking_efficiency/100)
        '''

        decrease = False
        if restriction_decreasing == [1]:
            decrease = True

        run_simulation(use_steps=True,
                       n_of_families=n_of_families,
                       number_of_steps=number_of_steps,
                       incubation_days=incubation_days,
                       infection_duration=infection_duration,
                       initial_day_restriction=initial_day_restriction,
                       restriction_duration=restriction_duration,
                       social_distance_strictness=social_distance_strictness,
                       restriction_decreasing=decrease,
                       n_initial_infected_nodes=n_initial_infected_nodes,
                       R_0=R_0,
                       n_test=n_test,
                       policy_test=policy_test,
                       contact_tracking_efficiency=contact_tracking_efficiency / 100,
                       path=str(path),
                       use_random_seed=True,
                       seed=0)

        fp_in = Path("network_dumps/nets.pickle")
        nets = list()
        with open(fp_in, "rb") as f:
            nets = pickle.load(f)

        S_rest = []
        I_rest = []
        E_rest = []
        R_rest = []
        D_rest = []
        tot_rest = []

        Q_rest = []
        T_rest = []
        T_pos = []

        for day in range(0, len(nets)):
            G = nets[day]
            report = Counter(G.vs["agent_status"])
            s = report["S"]
            e = report["E"]
            i = report["I"]
            r = report["R"]
            d = report["D"]
            tested = 0
            quarantined = 0
            positive = 0
            for node in G.vs:
                if node["test_result"] != -1:
                    tested += 1
                if node["test_result"] == 1:
                    positive += 1
                if node["quarantine"] != 0:
                    quarantined += 1

            S_rest.append(s)
            E_rest.append(e)
            I_rest.append(i)
            R_rest.append(r)
            D_rest.append(d)
            tot_rest.append(s + e + i + r + d)

            Q_rest.append(quarantined)
            T_rest.append(tested)
            T_pos.append(positive)

        outputs = []

        outputs.append({'data': [{'x': list(range(1, len(S_rest) + 1)), 'y': S_rest, 'type': 'line', 'name': 'S', 'marker': {'color': 'Blue'}},
                                 {'x': list(range(1, len(E_rest) + 1)), 'y': E_rest,
                                  'type': 'line', 'name': 'E', 'marker': {'color': 'Orange'}},
                                 {'x': list(range(1, len(I_rest) + 1)), 'y': I_rest,
                                  'type': 'line', 'name': 'I', 'marker': {'color': 'Red'}},
                                 {'x': list(range(1, len(R_rest) + 1)), 'y': R_rest,
                                  'type': 'line', 'name': 'R', 'marker': {'color': 'Green'}},
                                 {'x': list(range(1, len(D_rest) + 1)), 'y': D_rest, 'type': 'line',
                                  'name': 'deceduti', 'marker': {'color': 'Black'}},
                                 {'x': list(range(1, len(tot_rest) + 1)), 'y': tot_rest,
                                  'type': 'line', 'name': 'Total'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, tot_rest[0]], 'type': 'scatter',
                                  'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0,
                                                                                                                                              tot_rest[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                                 ],
                        'layout': {
            'title': 'Contacts network model with restriction',
            'xaxis': {'title': 'Day'},
            'yaxis': {'title': 'Count'}
        }
        })

        path_no_rest = Path("network_dumps_no_rest")

        run_simulation(use_steps=True,
                       n_of_families=n_of_families,
                       number_of_steps=number_of_steps,
                       incubation_days=incubation_days,
                       infection_duration=infection_duration,
                       initial_day_restriction=initial_day_restriction,
                       restriction_duration=restriction_duration,
                       social_distance_strictness=0,
                       restriction_decreasing=False,
                       n_initial_infected_nodes=n_initial_infected_nodes,
                       R_0=R_0,
                       n_test=0,
                       policy_test=policy_test,
                       contact_tracking_efficiency=0,
                       path=str(path_no_rest),
                       use_random_seed=True,
                       seed=0)

        fp_in = Path("network_dumps_no_rest/nets.pickle")
        nets = list()
        with open(fp_in, "rb") as f:
            nets = pickle.load(f)

        S = []
        I = []
        E = []
        R = []
        D = []
        tot = []

        for day in range(0, len(nets)):
            G = nets[day]
            report = Counter(G.vs["agent_status"])
            s = report["S"]
            e = report["E"]
            i = report["I"]
            r = report["R"]
            d = report["D"]

            S.append(s)
            E.append(e)
            I.append(i)
            R.append(r)
            D.append(d)
            tot.append(s + e + i + r + d)

        outputs.append({'data': [{'x': list(range(1, len(S) + 1)), 'y': S, 'type': 'line', 'name': 'S', 'marker': {'color': 'Blue'}},
                                 {'x': list(range(1, len(E) + 1)), 'y': E, 'type': 'line',
                                  'name': 'E', 'marker': {'color': 'Orange'}},
                                 {'x': list(range(1, len(I) + 1)), 'y': I, 'type': 'line',
                                  'name': 'I', 'marker': {'color': 'Red'}},
                                 {'x': list(range(1, len(R) + 1)), 'y': R, 'type': 'line',
                                  'name': 'R', 'marker': {'color': 'Green'}},
                                 {'x': list(range(1, len(D) + 1)), 'y': D, 'type': 'line',
                                  'name': 'deceduti', 'marker': {'color': 'Black'}},
                                 {'x': list(range(1, len(tot) + 1)), 'y': tot,
                                  'type': 'line', 'name': 'Total'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, tot[0]], 'type': 'scatter',
                                  'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0,
                                                                                                                                              tot[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                                 ],
                        'layout': {
            'title': 'Contacts network model with restriction',
            'xaxis': {'title': 'Day'},
            'yaxis': {'title': 'Count'}
        }
        })

        inf_rest = []
        inf = []
        for i in range(max(len(I_rest), len(I))):
            if i < len(I):
                inf.append(I[i] + E[i])
            else:
                inf.append(0)
            if i < len(I_rest):
                inf_rest.append(I_rest[i] + E_rest[i])
            else:
                inf_rest.append(0)

         # con e senza restrizioni
        outputs.append({'data': [{'x': list(range(1, len(I) + 1)), 'y': inf, 'type': 'line', 'name': 'Without restriction'},
                                 {'x': list(range(1, len(I) + 1)), 'y': inf_rest,
                                  'type': 'line', 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(
                                     inf + inf_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(
                                     inf + inf_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},

                                 ],
                        'layout': {'title': 'Comparison infected with and without restrictions',
                                   'xaxis': {'title': 'Day'},
                                   'yaxis': {'title': 'Number of incfected'}
                                   }
                        })

        if len(D) > len(D_rest):
            while(len(D) > len(D_rest)):
                D_rest.append(D_rest[-1])
        else:
            while(len(D_rest) > len(D)):
                D.append(D[-1])

        outputs.append({'data': [{'x': list(range(1, len(D) + 1)), 'y': D, 'type': 'line', 'name': 'Without restriction'},
                                 {'x': list(range(1, len(D) + 1)), 'y': D_rest,
                                  'type': 'line', 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(
                                     D + D_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(
                                     D + D_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},

                                 ],
                        'layout': {'title': 'Comparison dead with and without restrictions',
                                   'xaxis': {'title': 'Day'},
                                   'yaxis': {'title': 'Number of dead'}
                                   }
                        })

        inf_giorn_rest = [E_rest[0]]
        dead_giorn_rest = [D_rest[0]]

        inf_giorn = [E[0]]
        dead_giorn = [D[0]]

        for i in range(1, max(len(S), len(S_rest))):
            if i < len(S):
                inf_giorn.append(S[i-1] - S[i])
                dead_giorn.append(D[i] - D[i-1])
            else:
                inf_giorn.append(0)
                dead_giorn.append(0)
            if i < len(S_rest):
                inf_giorn_rest.append(S_rest[i-1] - S_rest[i])
                dead_giorn_rest.append(D_rest[i] - D_rest[i-1])
            else:
                inf_giorn_rest.append(0)
                dead_giorn_rest.append(0)

        # incrementi giornalieri
        outputs.append({'data': [{'x': list(range(1, len(I) + 1)), 'y': inf_giorn, 'type': 'line', 'name': 'Without restriction'},
                                 {'x': list(range(1, len(I) + 1)), 'y': inf_giorn_rest,
                                  'type': 'line', 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(
                                     inf_giorn + inf_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(
                                     inf_giorn + inf_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},

                                 ],
                        'layout': {'title': 'Comparison daily infected with and without restrictions',
                                   'xaxis': {'title': 'Day'},
                                   'yaxis': {'title': 'Number of infected'}
                                   }
                        })

        outputs.append({'data': [{'x': list(range(1, len(D) + 1)), 'y': dead_giorn, 'type': 'line', 'name': 'Without restriction'},
                                 {'x': list(range(1, len(D) + 1)), 'y': dead_giorn_rest,
                                  'type': 'line', 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(
                                     dead_giorn + dead_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Inizio restrizione'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(
                                     dead_giorn + dead_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},

                                 ],
                        'layout': {'title': 'Comparison daily dead with and without restrictions',
                                   'xaxis': {'title': 'Day'},
                                   'yaxis': {'title': 'Number of dead'}
                                   }
                        })

        x = ["Confronto"]
        last_day = len(I) - 1
        last_day_rest = len(I_rest) - 1
        y = [tot[last_day] - S[last_day]]
        y_rest = [tot_rest[last_day_rest] - S_rest[last_day_rest]]

        outputs.append({'data': [{'x': x, 'y': y, 'type': 'bar', 'name': 'Without restriction'},
                                 {'x': x, 'y': y_rest, 'type': 'bar',
                                     'name': 'With restriction'},

                                 ],
                        'layout': {'title': 'Total number of infected people with and without restriction',
                                   'yaxis': {'title': 'Count'}
                                   }
                        })

        fig = {'data': [{'x': list(range(1, len(T_rest) + 1)), 'y': T_rest, 'type': 'bar', 'name': 'Test made'},
                        {'x': list(range(1, len(T_rest) + 1)), 'y': T_pos,
                         'type': 'bar', 'name': 'Positive test'},
                        {'x': list(range(1, len(T_rest) + 1)), 'y': Q_rest,
                         'type': 'line', 'name': 'Quarantine'},

                        ],
               'layout': {'title': 'Comparison quarantine test made and positive test',
                          'yaxis': {'title': 'Count (log axis)', 'type': "log"},
                          }
               }

        outputs.append(fig)
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})
        outputs.append({'display': 'block'})

        return outputs

    else:
        return [{}, {}, {}, {}, {}, {}, {}, {}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}]

# check input


@app.callback(
    [
        Output('run_sim', 'disabled'),
        Output('alert_id', 'is_open')
    ],

    [
        Input("n_of_families", "value"),
        Input('number_of_steps', 'value'),
        Input('n_initial_infected_nodes', 'value'),
        Input('incubation_days', 'value'),
        Input('infection_duration', 'value'),
        Input('R_0', 'value'),
        Input('initial_day_restriction', 'value'),
        Input('n_test', 'value'),
        Input('restriction_duration', 'value')
    ],


)
def enable_button(n_of_families, number_of_steps, n_initial_infected_nodes, incubation_days, infection_duration, R_0, initial_day_restriction, n_test, restriction_duration):

    #dbc.Input(placeholder="Invalid input...", invalid=True),

    if n_of_families is not None and number_of_steps is not None and n_initial_infected_nodes is not None \
            and incubation_days is not None and infection_duration is not None and R_0 is not None \
            and initial_day_restriction is not None and n_test is not None \
            and restriction_duration is not None:

        return [False, False]
    else:
        return [True, True]


# run app
if __name__ == "__main__":
    app.run_server(debug=True, port=8000)
