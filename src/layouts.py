import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import statistics as stat


# statistic to plot   
age_range = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90+"]
age_prob = [0.084, 0.096, 0.102, 0.117, 0.153, 0.155, 0.122, 0.099, 0.059, 0.013]
age_fat_rate = [0.002,  0.001, 0.001, 0.004, 0.009, 0.026, 0.10, 0.249, 0.308, 0.261]

gitlink = "https://gitlab.com/migliouni/ctns_simulator"

age_prob = [prob *100 for prob in age_prob]
age_fat_rate =[prob*100 for prob in age_fat_rate]

avg_fat = stat.mean(age_fat_rate)

# form layout
form = dbc.Card(
    [   
        html.H3("Initial simulation parameters "),
        html.Br(),
        dbc.FormGroup(
            [
                dbc.Label("Number of families: "),
                dbc.Input(id="n_of_families", type="number", value=150, min = 10, max = 150),
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
                dbc.Input(id="number_of_steps", type="number", value=150, min = 10, max = 150),
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
                    dbc.Alert(
                        [
                            "This is a light version only for demo. In this version the number of family and step are limited at 150 for not exceeding heroku timeout. Full code without limitation is available at:  ",
                            html.A("here clikkabile", href=gitlink, className="alert-link"),
                        ],
                        color="warning",
                    ),
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