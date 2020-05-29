import glob, os, pickle, dash
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
age_range = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90+"]
age_prob = [0.084, 0.096, 0.102, 0.117, 0.153, 0.155, 0.122, 0.099, 0.059, 0.013]
age_fat_rate = [0.002,  0.001, 0.001, 0.004, 0.009, 0.026, 0.10, 0.249, 0.308, 0.261]


age_prob = [prob *100 for prob in age_prob]
age_fat_rate =[prob*100 for prob in age_fat_rate]

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
                dbc.Input(id="n_of_families", type="number", value=500, min = 10),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Number of initial exposed people:"),
                dbc.Input(id="n_initial_infected_nodes", type="number", value=5, min = 1),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Simulation days:"),
                dbc.Input(id="number_of_steps", type="number", value=150, min = 10),
            ]
        ),

        html.Br(),
        html.H3("Epidemic parameters"),
        html.Br(),
        dbc.FormGroup(
            [
                dbc.Label("Incubation days: "),
                dbc.Input(id="incubation_days", type="number", value=5, min = 1),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label("Disease duration:"),
                dbc.Input(id="infection_duration", type="number", value=21, min = 1),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("R_0:"),
                dbc.Input(id="R_0", type="number", value=2.9, min = 0, max = 10, step = 0.1),
            ]
        ),
        
        html.Br(),
        html.H3("Social restriction parameters"),
        html.Br(),
        dbc.FormGroup(
            [   
                
                dbc.Label("Intial day restriction:"),
                dbc.Input(id="initial_day_restriction", type="number", value=35, min = 1),
            ]
        ),
        
        dbc.FormGroup(
            [   
                
                dbc.Label("Duration of restriction:"),
                dbc.Input(id="restriction_duration", type="number", value=28, min = 0),
            ]
        ),
        
        

        dbc.FormGroup(
            [   
                
                dbc.Label("Social distance strictness:"),
                html.Div(dcc.Slider(id="social_distance_strictness", 
                    value=2, min =0, max = 4,
                    #step=None,
                    marks={
                            0: {'label': '0%', 'style': {'color': '#f50'}},
                            1: {'label': '25%'},
                            2: {'label': '50%'},
                            3: {'label': '75%'},
                            4: {'label': '100%', 'style': {'color': '#77b0b1'}}
                        },
                    vertical = False,
                    ),
                    style={'width': '100%','display': 'block'},
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
                dbc.Input(id="n_test", type="number", value=0, min =0),
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
                ),            ]
        ),

        dbc.FormGroup(
            [   
                
                dbc.Label("Contact tracing efficiency:"),
                html.Div(dcc.Slider(id="contact_tracing_efficiency", 
                    value=80, min =0, max = 100, step = 10,
                    #step=None,
                    marks={
                            0: {'label': '0%', 'style': {'color': '#f50'}},
                            50: {'label': '50%'},
                            100: {'label': '100%', 'style': {'color': '#77b0b1'}}
                       },
                    vertical = False,
                    ),
                    style={'width': '100%','display': 'block'},
                )
            ]
        ),

        dbc.FormGroup(
            [   
                
                dbc.Label("Contact tracing duration:"),
                dbc.Input(id="contact_tracing_duration", type="number", value=14, min =0),
            ]
        ),
        
        html.Br(),
        html.H3("Saving parameters"),
        html.Br(),

        dbc.FormGroup(
            [   
            
            dbc.Label("Type of dump:"),
            dcc.RadioItems(id="dump_type",
                options=[
                    {'label': 'full', 'value': 'full'},
                    {'label': 'light', 'value': 'light'},
                ],
                value='light',
                labelStyle={'display': 'block'}
            ), 

            html.Br(),
            dbc.Label("Name of file:"),
            dbc.Input(id="name_file", placeholder='Enter a name...', type='text', value='sim_dump')    
            
            ],
        ),



        html.Br(),
        dbc.FormGroup(
            [   
            
            dbc.Button("Run simulation", id="run_sim",  color="primary", className="mr-1", block=True),
            html.Br(),
            dbc.Alert("Check the value of parameters or the name of results file!", id = 'alert_id', color="danger", is_open=False),
            ]   
            ),
    ],
    body=True,
    style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'},
)


# simulator tab
tab1_content = dbc.Card(
    dbc.CardBody(
        [

            dbc.Row(
                [
                dbc.Col([
                    html.Br(),
                    html.H3("Simulator tab"),
                    html.Br(),
                    html.P('In this tab you can start the Covid-19 contact simulator. There are different initial parameters that you can set. furthermore, different results are shown in output. We now provide a brief presentation of these components:'),
                    html.Br(),
                    html.H3("Initial parameters"),
                    html.Ul(children=[
                        html.Li('Number of families - The number of families involved in the simulation. A family is a group of people that live together'),
                        html.Li('Number of initial exposed people - Usually called patient zero. This parameter represents the number of the people that are infected at the beginning of the simulation '),
                        html.Li('Simulation days - An integer number that represents the number of days of the simulation '),
                        html.Li('Incubation days - This is the first epidemic parameter and it represents a mean of the number of days of incubation '),
                        html.Li('Disease duration - the avarage duration of the Covid-19 disease'),
                        html.Li('R0 - It is a decimal parameter and it is a mathematical term that indicates how contagious an infectious disease is '),
                        html.Li('Intial day restriction - This is the first sociability restriction parameter and it represents the day the restriction begins '),
                        html.Li('Duration of restriction - It represents the number of days which the restriction is active'),
                        html.Li('sociability distance strictness - This parameter is a percentile that you can set through a slidebar. If this parameter is equal to 0%, it means that no sociability distance has been adopted, on the contrary, the strictness of the sociability distance is very high'),
                        html.Li('Decreasing restrionction - If enabled, the restriction decrease with the evolution of the simulation'),
                        html.Li('Daily number of test - This parameter represents the number of tests that are carried out daily '),
                        html.Li('Policy test - The policy under which the tests are carried out. You can choose 3 different options: random, throut a computation of degree centrality or with a computation of between centrality (it may require more time for huge simulations) '),
                        html.Li('Contact tracing efficiency - the efficiency of contract tracing. This is a percentile which can be set through a slidebar'),
                    ]),
                    html.H3("Output components"),
                    html.Ul(children=[
                        html.Li('Simulation results - This part consistes of two different lineplots which represents the evolution of SEIRD model in the case we have adopted restriction and we have not adopeted restriction. In both graphs we have the count of people involved in the simulation on the y-axis and the number of days in the x-axis '),
                        html.Li('Comparison Results - these lineplots compare the number of people infected with the total (first graph) and the number of dead with the total (second graph). The blue line represents the case which no restriction has been adopted. On the contraruy, orange line represents the case which restriction has been applied '),
                        html.Li('Daily results with and without restriction - These lineplots are similar to the previous but they consider a daily comparison of infected '),
                        html.Li('Total infected with and without restriction - This barplot links the total number of infected in case if or not rectriction has been adopted'),
                        html.Li('Tests and Quarantine results '),
                    ]),
                ], md=12),

                ],
            ),

            
        dbc.Row(
            [
                dbc.Col(form, md=4),
                dbc.Col([
                    dbc.Container([
                        html.Br(),
                        html.H3("Simulation results"),
                        html.Hr(),
                        dbc.Spinner(dcc.Graph(id="graph_sim", style= {'display': 'block'}), color="primary"),
                        html.Br(),
                        dbc.Spinner(dcc.Graph(id="graph_sim_without_restr", style= {'display': 'block'}), color="primary"),
                        html.Br(),
                    ], fluid = True),
                ], style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}, 
                md=7),
        
            ],
            align="center",
        ),

        html.Div(style = {'margin-top': '60px'}),
        dbc.Container(id ="div", children = [

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
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_infected", style= {'display': 'block'}), color="primary"), html.Br()], md=6),
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_dead", style= {'display': 'block'}), color="primary"), html.Br()], md=6),
            
                ],
                align="center"),
         
         ], fluid=True, style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}),

        html.Div(style = {'margin-top': '60px'}),

        dbc.Container(id ="div_2", children = [

            dbc.Row(

            [   
                dbc.Col([
                    html.Br(),
                    html.H3("Daily results with and without restriction"),
                    html.Hr(),
                    ], md=12),
            ]
            ),

            dbc.Row(
                [   
                    html.Br(),
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_Inf_daily", style= {'display': 'block'}), color="primary"), html.Br()], width = 6),
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_dead_daily", style= {'display': 'block'}), color="primary"), html.Br()], width = 6),
            
                ],
                align="center", 
            ),
         
         ], style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}, fluid=True),

        html.Div(style = {'margin-top': '60px'}),
        
        dbc.Container(id ="div_comparison", children = [

            dbc.Row(

            [   
                dbc.Col([
                    html.Br(),
                    html.H3("Total infected with and without restriction"),
                    html.Hr(),
                    ], md=12),
            ]
            ),

            dbc.Row(
                [   
                    html.Br(),
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_total_infected", style= {'display': 'block'}), color="primary"), html.Br()], width = 12),
                ],
                align="center", 
            ),
         
         ], style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}),

        html.Div(style = {'margin-top': '60px'}),
        dbc.Container(id ="div_tamponi", children = [

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
                    dbc.Col([dbc.Spinner(dcc.Graph(id="graph_test", style= {'display': 'block'}), color="primary"), html.Br()], width = 12),
                ],
                align="center", 
            ),
         
         ], style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}, fluid=True),

        html.Div(style = {'margin-top': '60px'}),
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
                                                'xaxis':{'title':'Age'},
                                                'yaxis':{'title':'Population percentage'},
                                    }
                            }
                    ),
                html.Br(),
                html.P("Source: ", style = {'display': 'inline '}),
                html.A('http://dati.istat.it/', href='http://dati.istat.it/', target="_blank"),
                ], md=6),

                dbc.Col([
                    dcc.Graph(
                            id='age_graph_death_rate',
                            figure={
                                    'data': [
                                                {'x': age_range, 'y': age_fat_rate, 'type': 'bar', 'marker' : {'color': '#f50'}, 'name': 'Fatality rate'},
                                                {'x': [age_range[0], age_range[len(age_range) -1]], 'y': [avg_fat, avg_fat] , 'type': 'scatter', 'line': dict(color='rgb(20, 53, 147)', dash='dot'), 'name': 'Average Fatality'}
                                            ],
                                    'layout': {
                                                'title': 'Fatality rate age distribution',
                                                'xaxis':{'title':'Age'},
                                                'yaxis':{'title':'Fatality rate'},
                                                 
                                    }
                            }
                    ),
                    html.Br(),
                        
                    html.P("Source: ", style = {'display': 'inline '}),
                    html.A('https://www.epicentro.iss.it', href='https://www.epicentro.iss.it/coronavirus/sars-cov-2-sorveglianza-dati', target="_blank"),
                        
                ], md=6),


                ],
            align="center"
            ),

            html.Div(style = {'margin-top': '60px'}),
            

            ],

    fluid = True,
    style = {'background-color': '#f2f2f2', 'border-radius': '4px', 'box-shadow': '2px 2px 2px lightgrey'}
    )


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
        

# on the click event of run_sim button get all parameter value and run simultion then return all graphics
@app.callback(
    [Output('graph_sim', 'figure'),
        Output('graph_sim_without_restr', 'figure'),
        Output('graph_infected', 'figure'),
        Output('graph_dead', 'figure'),
        Output('graph_Inf_daily', 'figure'),
        Output('graph_dead_daily', 'figure'),
        Output('graph_total_infected', 'figure'),
        Output('graph_test', 'figure'),

        # show or hide the componentt
        Output('graph_sim', 'style'),
        Output('graph_sim_without_restr', 'style'),
        Output('graph_infected', 'style'),
        Output('graph_dead', 'style'),
        Output('graph_Inf_daily', 'style'),
        Output('graph_dead_daily', 'style'),
        Output('graph_total_infected', 'style'),
        Output('graph_test', 'style'),
        ],
    
    # input event
    [Input("run_sim", "n_clicks")], 
    
    # current value of parameters
    [State('n_of_families','value'),        
        State('number_of_steps','value'),
        State('n_initial_infected_nodes','value'),
        State('incubation_days','value'),
        State('infection_duration','value'),
        State('R_0','value'),
        State('initial_day_restriction','value'),
        State('restriction_duration','value'),
        State('social_distance_strictness','value'),
        State('restriction_decreasing', 'value'),
        State('n_test','value'),
        State('policy_test','value'),
        State('contact_tracing_efficiency', 'value'),
        State('contact_tracing_duration', 'value'),
        State('dump_type', 'value'),
        State('name_file', 'value')]
)

def updateSimulation(n_clicks, n_of_families, number_of_steps, n_initial_infected_nodes, incubation_days, infection_duration, R_0, initial_day_restriction, restriction_duration, social_distance_strictness, restriction_decreasing, n_test , policy_test, contact_tracing_efficiency, contact_tracing_duration, dump_type, name_file):
    """
    Execute the simulations (with and without restriction) and return graphics with comparison and statistics. Save simulation results and parameters in the folder "simulator_results/" in .pickle file format (overwrite if files already exist)

    Parameters
    ----------
    n_clicks int
        Number of click of the simulation button, use to avoid updating first auto-call e refresh in dash

    n_of_families: int
        Number of families in the network
    
    number_of_steps : int
        Number of simulation step to perform

    n_initial_infected_nodes: int
        Number of nodes that are initially infected

    incubation_days: int
        Number of days where the patient is not infective

    infection_duration: int
        Total duration of the disease per patient
    
    R_0: float
        The R0 facotr of the disease

    initial_day_restriction: int
        Day index from when sociability distancing measures are applied

    social_distance_strictness: int
        How strict from 0 to 4 the sociability distancing measures are. 
        Represent the portion of contact that are dropped in the network (0, 25%, 50%, 75%, 100%)
        Note that family contacts are not included in this reduction

    restriction_duration: int
        How many days the sociability distancing last. Use 0 to make the restriction last till the end of the simulation

    restriction_decreasing: bool
        If the sociability distancing will decrease the strictness during the restriction_duration period

    n_test: int
        Number of avaiable tests

    policy_test: string
        Strategy with which test are made. Can be Random, Degree Centrality, Betweenness Centrality

    contact_tracing_efficiency: float
        The percentage of contacts successfully traced back in the past 14 days


    Return
    ------

    outputs:list
        List of all updated grapahics.
        Save simulation (overwrite if files already exist) results and parameters in the folder "simulator_results/" in .pickle file format.

    """
   
    # check to avoid first running at the launch of the app and on refresh page
    if n_clicks is not None:


        decrease = False
        if restriction_decreasing == [1]:
            decrease = True

        # create dir
        if not os.path.exists("simulator_results"):
            os.mkdir("simulator_results")

        path = Path("simulator_results/" + str(name_file))
         
        run_simulation( use_steps = True,
                        n_of_families = n_of_families, 
                        number_of_steps = number_of_steps,
                        incubation_days = incubation_days,
                        infection_duration = infection_duration,
                        initial_day_restriction = initial_day_restriction,
                        restriction_duration = restriction_duration,
                        social_distance_strictness = social_distance_strictness,
                        restriction_decreasing = decrease,
                        n_initial_infected_nodes = n_initial_infected_nodes,
                        R_0 = R_0,
                        n_test = n_test,
                        policy_test = policy_test,
                        contact_tracing_efficiency = contact_tracing_efficiency / 100,
                        contact_tracing_duration = contact_tracing_duration,
                        path = str(path),
                        use_random_seed = True,
                        seed = 0,
                        dump_type = dump_type,
                        )
        
        # list of data to plot
        S_rest = []
        I_rest = []
        E_rest = []
        R_rest = []
        D_rest = []
        tot_rest = []
        Q_rest = []
        T_rest = []
        T_pos = []
        
        if dump_type == 'full':
            dump_full = dict()
            nets = list()
            with open(str(path)+'.pickle', "rb") as f:
                dump_full = pickle.load(f)
                nets = dump_full['nets']
            # get daily count of peple status
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
                tot_rest.append(s + e + i + r +d)
                
                Q_rest.append(quarantined)
                T_rest.append(tested)
                T_pos.append(positive)

        else:
            dump_light = dict()
            with open(str(path)+'.pickle', "rb") as f:
                dump_light = pickle.load(f)
            S_rest = dump_light['S']
            I_rest = dump_light['I']
            E_rest = dump_light['E']
            R_rest = dump_light['R']
            D_rest = dump_light['D']
            tot_rest = dump_light['total']
            Q_rest = dump_light['quarantined']
            T_rest = dump_light['tested']
            T_pos = dump_light['positive']

            
            

        
        # list of output to return
        outputs = []

        graph_sim = dict({'data': [],
                'layout': {
                   'title': 'Contacts network model with restriction',
                   'xaxis':{'title':'Day'},
                   'yaxis':{'title':'Count'}
               }
               })

        graph_sim['data'].append({'x': list(range(1, len(S_rest) +1)), 'y': S_rest,  'name': 'S', 'marker' : {'color': 'Blue'}})
        graph_sim['data'].append({'x': list(range(1,len(E_rest) +1)), 'y': E_rest,  'name': 'E', 'marker' : {'color': 'Orange'}})
        graph_sim['data'].append({'x': list(range(1,len(I_rest) +1)), 'y': I_rest,  'name': 'I', 'marker' : {'color': 'Red'}})
        graph_sim['data'].append({'x': list(range(1, len(R_rest) +1)), 'y': R_rest,  'name': 'R', 'marker' : {'color': 'Green'}})
        graph_sim['data'].append({'x': list(range(1, len(D_rest) +1)), 'y': D_rest,  'name': 'deceduti', 'marker' : {'color': 'Black'}})
        graph_sim['data'].append({'x': list(range(1, len(tot_rest) +1)), 'y': tot_rest, 'name': 'Total'})
        graph_sim['data'].append({'x': [initial_day_restriction, initial_day_restriction], 'y':[0, tot_rest[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'})
        graph_sim['data'].append({'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, tot_rest[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'})
                         
               
       
        
        path_no_rest = Path("simulator_results/" + str(name_file) + "no_restr")
           
        run_simulation( use_steps = True,
                        n_of_families = n_of_families, 
                        number_of_steps = number_of_steps,
                        incubation_days = incubation_days,
                        infection_duration = infection_duration,
                        initial_day_restriction = initial_day_restriction,
                        restriction_duration = restriction_duration,
                        social_distance_strictness = 0,
                        restriction_decreasing = False,
                        n_initial_infected_nodes = n_initial_infected_nodes,
                        R_0 = R_0,
                        n_test = 0,
                        policy_test = policy_test,
                        contact_tracing_efficiency = 0,
                        path = str(path_no_rest),
                        use_random_seed = True,
                        seed = 0,
                        dump_type = dump_type,
                        )
        
         # daily count
        S = []
        I = []
        E = []
        R = []
        D = []
        tot = []
        if dump_type == 'full':
            dump_full = dict()
            nets = list()
            with open(str(path_no_rest) +'.pickle', "rb") as f:
                dump_full = pickle.load(f)
                nets = dump_full['nets']
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
                tot.append(s + e + i + r +d)
        else:
            dump_light = dict()
            with open(str(path_no_rest) +'.pickle', "rb") as f:
                dump_light = pickle.load(f)
            S = dump_light['S']
            I = dump_light['I']
            E = dump_light['E']
            R = dump_light['R']
            D = dump_light['D']
            tot = dump_light['total']
            

            

        graph_sim_without_restr = {'data': [ {'x': list(range(1, len(S) +1)), 'y': S, 'name': 'S', 'marker' : {'color': 'Blue'}},
                         {'x': list(range(1,len(E) +1)), 'y': E, 'name': 'E', 'marker' : {'color': 'Orange'}},
                         {'x': list(range(1,len(I) +1)), 'y': I, 'name': 'I', 'marker' : {'color': 'Red'}},
                         {'x': list(range(1, len(R) +1)), 'y': R, 'name': 'R', 'marker' : {'color': 'Green'}},
                         {'x': list(range(1, len(D) +1)), 'y': D, 'name': 'deceduti', 'marker' : {'color': 'Black'}},
                         {'x': list(range(1, len(tot) +1)), 'y': tot, 'name': 'Total'},
                         {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, tot[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                         {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, tot[0]], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                         ],
               'layout': {
                   'title': 'Contacts network model without restriction',
                   'xaxis':{'title':'Day'},
                   'yaxis':{'title':'Count'}
               }
              }

        # get total infected people (infected + exposed)
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
        graph_infected = {'data': [{'x': list(range(1,len(I) +1)), 'y': inf, 'name': 'Without restriction'},
                                 {'x': list(range(1,len(I) +1)), 'y': inf_rest, 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(inf + inf_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(inf + inf_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                         
                                 ],
                'layout': {'title': 'Comparison infected with and without restrictions',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of incfected'}
                          }
               }

        # get all dead people 
        if len(D) > len(D_rest):
            while(len(D) > len(D_rest)):
                D_rest.append(D_rest[-1])
        else:
            while(len(D_rest) > len(D)):
                D.append(D[-1])
               
        graph_dead = {'data': [{'x': list(range(1,len(D) +1)), 'y': D, 'name': 'Without restriction'},
                                 {'x': list(range(1,len(D) +1)), 'y': D_rest, 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(D + D_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(D + D_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                         
                                 ],
                'layout': {'title': 'Comparison dead with and without restrictions',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of dead'}
                          }
               }

        # get daily increment of infected and dead people
        inf_giorn_rest = [E_rest[0]]
        dead_giorn_rest = [D_rest[0]]

        inf_giorn = [E[0]]
        dead_giorn = [D[0]]

        for i in range(1, max(len(S), len(S_rest))):
            if i < len(S):
                inf_giorn.append(S[i-1] - S[i] )
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

 
        graph_Inf_daily = {'data': [{'x': list(range(1,len(I) +1)), 'y': inf_giorn, 'name': 'Without restriction'},
                                 {'x': list(range(1,len(I) +1)), 'y': inf_giorn_rest, 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(inf_giorn + inf_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Begin restriction'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(inf_giorn + inf_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                         
                                 ],
                'layout': {'title': 'Comparison daily infected with and without restrictions',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of infected'}
                          }
               }
               
        graph_dead_daily = {'data': [{'x': list(range(1,len(D) +1)), 'y': dead_giorn, 'name': 'Without restriction'},
                                 {'x': list(range(1,len(D) +1)), 'y': dead_giorn_rest, 'name': 'With restriction'},
                                 {'x': [initial_day_restriction, initial_day_restriction], 'y':[0, max(dead_giorn + dead_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'Inizio restrizione'},
                                 {'x': [initial_day_restriction + restriction_duration, initial_day_restriction + restriction_duration], 'y':[0, max(dead_giorn + dead_giorn_rest)], 'type': 'scatter', 'line': dict(color='rgb(55, 83, 109)', dash='dot'), 'name': 'End restriction'},
                         
                                 ],
                'layout': {'title': 'Comparison daily dead with and without restrictions',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of dead'}
                          }
               }

        x = ["Results"]
        last_day = len(I) - 1
        last_day_rest = len(I_rest) - 1
        y = [tot[last_day] - S[last_day]]
        y_rest = [tot_rest[last_day_rest] - S_rest[last_day_rest]]

        graph_total_infected = {'data': [{'x': x, 'y': y, 'type': 'bar', 'name': 'Without restriction'},
                                 {'x': x, 'y': y_rest, 'type': 'bar', 'name': 'With restriction'},
    
                                 ],
                'layout': {'title': 'Total number of infected people with and without restriction',
                           'yaxis':{'title':'Count'}
                          }
               }

        
       # test made and quarantine people

        graph_test = {'data': [{'x': list(range(1,len(T_rest) +1)), 'y': T_rest, 'type': 'bar', 'name': 'Test made'},
                                 {'x': list(range(1,len(T_rest) +1)), 'y': T_pos, 'type': 'bar', 'name': 'Positive test'},
                                 {'x': list(range(1,len(T_rest) +1)), 'y': Q_rest, 'name': 'Quarantine'},
    
                                 ],
                'layout': {'title': 'Comparison quarantine test made and positive test',
                           'yaxis':{'title':'Count (log axis)', 'type':"log"},
                          }
               }
       

        outputs = [graph_sim, graph_sim_without_restr, graph_infected, graph_dead, graph_Inf_daily, graph_dead_daily, graph_total_infected, graph_test, {'display': 'block'}, {'display': 'block'}, {'display': 'block'},{'display': 'block'},{'display': 'block'},{'display': 'block'},{'display': 'block'},{'display': 'block'}]
        names = ['graph_sim.pdf', 'graph_sim_without_restr.pdf', 'graph_infected.pdf', 'graph_dead.pdf', 'graph_Inf_daily.pdf', 'graph_dead_daily.pdf', 'graph_total_infected.pdf', 'graph_test.pdf']
        save_pdf = False

        if save_pdf == True:
            for index in range(len(names)):
                if isinstance(outputs[index], dict):
                    print("dict", names[index])
                    fig = go.Figure(outputs[index])
                    fig.write_image(names[index])
                else:
                    outputs[index].write_image(names[index])
                    print("image", names[index])
        
        return outputs
        
    else:
        # first launch do not run the simulation and hide all graphics
        return [{}, {}, {}, {}, {}, {}, {}, {}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}]





# check input before enable button run simulation
@app.callback(
    [
        Output('run_sim', 'disabled'),
        Output('alert_id', 'is_open')
    ],
    
    [   
        Input("n_of_families", "value"),
        Input('number_of_steps','value'),
        Input('n_initial_infected_nodes','value'),
        Input('incubation_days','value'),
        Input('infection_duration','value'),
        Input('R_0','value'),
        Input('initial_day_restriction','value'),
        Input('n_test','value'),
        Input('restriction_duration','value'),
        Input('name_file', 'value'),
        Input('contact_tracing_duration', 'value')
    ],
)

def enable_disable_button(n_of_families, number_of_steps, n_initial_infected_nodes, incubation_days, infection_duration, R_0, initial_day_restriction, n_test, restriction_duration, name_file, contact_tracing_duration):
    """
    Check parameters value before enable button simulation. If any parameter of the simulation does not in (min, max) range this callback disable button and show alert message.

    Parameters
    ----------

    n_of_families: int
        Number of families in the network
    
    number_of_steps : int
        Number of simulation step to perform

    n_initial_infected_nodes: int
        Number of nodes that are initially infected

    incubation_days: int
        Number of days where the patient is not infective

    infection_duration: int
        Total duration of the disease per patient
    
    R_0: float
        The R0 facotr of the disease
    
    n_test: int
        Number of avaiable tests

    initial_day_restriction: int
        Day index from when sociability distancing measures are applied

    restriction_duration: int
        How many days the sociability distancing last. Use 0 to make the restriction last till the end of the simulation

    
    Return
    ------

    outputs:list of bool
        List of 2 bool if true value disable button and show alert messagge, else enable button for the click

    """
    
    #dbc.Input(placeholder="Invalid input...", invalid=True),


    # check if the value is in the limits (min, max) 
    if n_of_families is not None and number_of_steps is not None and n_initial_infected_nodes is not None \
        and incubation_days is not None and infection_duration is not None and R_0 is not None \
        and initial_day_restriction is not None and n_test is not None \
        and restriction_duration is not None \
        and name_file != "":
        
        return [False, False]
    else:
        # disable button and show error message
        return [True, True]


# run app 
if __name__ == "__main__":
    app.run_server(debug=True, port=8000)