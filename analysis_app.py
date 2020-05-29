import glob, os, pickle, dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from collections import Counter

import dash_table
from pathlib import Path
import base64
import datetime
import io




# begin layout app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Analysis simulation results'

server = app.server

app.layout = dbc.Container(
    [   
        html.H1("Analysis simulation results"),
        html.Hr(),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Click and Select Files', href="#")
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
   
    html.Br(),
    html.Div(id ='alert_div'),
    html.Div(id='output-data-upload'),
    html.H2("Uploaded file List"),
    html.Ul(id="file-list"),
    html.Br(),
    html.Div(id='table_parameters'),
    html.Br(),
    html.Div(id='table_parameters2'),
    html.Br(),
    html.Div(id='table_parameters3'),
    html.Br(),
    dbc.Row(children = [
        dbc.Col(dbc.Spinner(dcc.Graph(id="heatMap", style= {'display': 'block'}), color="primary"), width = 12)
    ]),
    html.Br(),
    dbc.Row(children = [
        dbc.Col(dbc.Spinner(dcc.Graph(id="graph_comparison_inf", style= {'display': 'block'}), color="primary"), width = 6),
        dbc.Col(dbc.Spinner(dcc.Graph(id="graph_comparison_dead", style= {'display': 'block'}), color="primary"), width = 6),
    ]),
    html.Br(),
    dbc.Row(children = [
        dbc.Col(dbc.Spinner(dcc.Graph(id="graph_comparison_total_inf", style= {'display': 'block'}), color="primary"), md=6),
        dbc.Col(dbc.Spinner(dcc.Graph(id="graph_simulation_len", style= {'display': 'block'}), color="primary"), md=6),

    ]),
    html.Br(),
    dbc.Row(children = [
        dbc.Col(dbc.Spinner(dcc.Graph(id="scatter_dead", style= {'display': 'block'}), color="primary"), width = 6),
        dbc.Col(dbc.Spinner(dcc.Graph(id="stack_bar", style= {'display': 'block'}), color="primary"), width = 6)
    ]),
    ],

    #fluid=True,
)

def compute_network_history_from_full_dump(full_dump):
    """
    Compute the dayly counter of Susceptibile, Exposed, Infectedm, Recovered, Dead, Quarantine, Tested, Positive.
    Return dictionary with keys S, E, I, R, D, Q, tot, tested, positive and values list of dayly counter according to
    the keys.
    
    Parameters
    ----------
    nets: list of ig.Graph()
        List of dayly igraph objects

    Return
    ------
    network_history: dictionary of agent status and tests
        Dictionary keys:    S, E, I, R, D, Q, tot, tested, positive 
                   values:  list of dayly counter of key
    """
    nets = full_dump['nets']
    network_history = {}
    network_history['S'] = list()
    network_history['E'] = list()
    network_history['I'] = list()
    network_history['R'] = list()
    network_history['D'] = list()
    network_history['quarantined'] = list()
    network_history['positive'] = list()
    network_history['tested'] = list()
    network_history['total'] = list()

    for day in range(len(nets)):
        G = nets[day]

        network_report = Counter(G.vs["agent_status"])

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

        tot = sum(network_report.values())
        network_report['quarantined'] = quarantined
        network_report['positive'] = positive
        network_report['tested'] = tested


        network_history['S'].append(network_report['S'])
        network_history['E'].append(network_report['E'])
        network_history['I'].append(network_report['I'])
        network_history['R'].append(network_report['R'])
        network_history['D'].append(network_report['D'])
        network_history['quarantined'].append(network_report['Q'])
        network_history['positive'].append(network_report['positive'])
        network_history['tested'].append(network_report['tested'])
        network_history['total'].append(tot)
        network_history['parameters'] = full_dump['parameters']

    return network_history

# read only pickle file
def parse_contents(name, content):

    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        # read pickle

        file_content = pickle.loads(decoded)
        #print("Parameters", file_content['parameters'])
        if isinstance(file_content, dict):
            for key in file_content.keys():
                if not isinstance(file_content[key] , (list, dict)):
                    return "Error"
            return file_content
        else:
            return "Error"
        
    except Exception as e:
        print(e)
        return "Error"

# TO-DO
def normalize_data_to_plot(dict_upload_files):
    norm_dict_upload_files ={}

    for file in dict_upload_files.keys():
        print("file", file)
        # full dump
        if len(dict_upload_files[file].keys()) == 2:
            norm_dict_upload_files[file] = compute_network_history_from_full_dump(dict_upload_files[file])

        
        # light dump
        elif isinstance(dict_upload_files[file], dict):
            norm_dict_upload_files[file] = dict_upload_files[file]
            #print(dict_upload_files[file])

    return norm_dict_upload_files


def create_all_graphs(dict_upload_files, save_pdf = True):

        # normalize light e full dumps
        norm_dict_upload_files = normalize_data_to_plot(dict_upload_files)


        # comparison simulation results
        graph_infected = dict({'data': [],
                'layout': {'title': 'Comparison infected',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of infected'}
                          }
               })

        for filename in norm_dict_upload_files.keys():
            infected = [norm_dict_upload_files[filename]['I'][i] + norm_dict_upload_files[filename]['E'][i] for i in range(len(norm_dict_upload_files[filename]['I']))]
            graph_infected['data'].append({"type": "scatter", 'x': list(range(len(infected))), "y":  infected, 'name': filename.split('.')[0]})
        

        # comparison dead all simulation
        graph_dead = dict({'data': [],
                'layout': {'title': 'Comparison dead',
                           'xaxis':{'title':'Day'},
                           'yaxis':{'title':'Number of dead'}
                          }
               })
        
        for filename in norm_dict_upload_files.keys():
            dead = norm_dict_upload_files[filename]['D']
            graph_dead['data'].append({'x': list(range(len(dead))), 'y':  dead, 'type': 'scatter', 'name': filename.split('.')[0]}) 



        # grpah total infected all simualation
        graph_tot_inf = dict({'data': [],
                'layout': {'title': 'Comparison total infected at the end of simulation',
                           'yaxis':{'title':'Number of infected'}
                          }
               })
        for filename in norm_dict_upload_files.keys():
            last_day = len(norm_dict_upload_files[filename]['total']) - 1
            total_infeted = norm_dict_upload_files[filename]['total'][last_day] - norm_dict_upload_files[filename]['S'][last_day]
            graph_tot_inf['data'].append({'x': [1], 'y': [total_infeted], 'type': 'bar', 'name': filename.split('.')[0]}) 



        # graph len simulation
        graph_simulation_len = dict({'data': [],
                'layout': {'title': 'Comparison lenght simulation',
                           'xaxis':{'title':'Day'},
                          }
               })

        heatMap_values = []
        heatMap_name = []
        for filename in norm_dict_upload_files.keys():

            sim_len = len(norm_dict_upload_files[filename]['I'])
            infected = [norm_dict_upload_files[filename]['I'][i] + norm_dict_upload_files[filename]['E'][i] for i in range(len(norm_dict_upload_files[filename]['I']))]
            for i in range(len(infected)):
                if infected[i] == 0:
                    sim_len = i
                    break
            graph_simulation_len['data'].append({'y': [filename.split('.')[0]], 'x':  [sim_len], 'type': 'bar', 'name': filename.split('.')[0], 'orientation': 'h'}) 

            #used for heatmap graph
            heatMap_name.append(filename.split('.')[0])
            heatMap_values.append(infected)

        #graph_simulation_len['data'].reverse()
        # reverse to get smae order of other graphics
        heatMap_values.reverse()
        heatMap_name.reverse()

        hovertemplate = "<b> Simulation %{y} Day %{x} <br><br> %{z} Infected"
        heatMap = go.Figure(data=go.Heatmap(
                   z=heatMap_values,
                   y=heatMap_name,
                   hoverongaps = True,
                   name="",
                   hovertemplate = hovertemplate,
                   colorscale = 'YlOrRd'),#'Viridis'),
                   )

        heatMap.update_layout(
            title='Infeted day by day',
            )

        # scatter dead plot
        x_scatter = list()
        y_scatter = list()
        z_scatter = list()
        for filename in norm_dict_upload_files.keys():
            local_x_scatter = []
            local_y_scatter = []
            local_z_scatter = []
            name = filename.split('.')[0]
            last_dead = 0
            count = 0
            for dead in norm_dict_upload_files[filename]['D']:
                if dead != 0 and dead > last_dead:
                    local_x_scatter.append(dead)
                    local_y_scatter.append(name)
                    local_z_scatter.append("Day: " + str(count))
                    last_dead = dead
                count+=1
            
            x_scatter.extend(local_x_scatter)
            y_scatter.extend(local_y_scatter)
            z_scatter.extend(local_z_scatter)

        

        #hovertemplate = "<b> Simulation %{y} Dead %{x} <br><br> %{z} Day"
        scatter_dead = go.Figure()

        scatter_dead.add_trace(go.Scatter(
            x=x_scatter,
            y=y_scatter,
            text=z_scatter,
            name='',
            marker=dict(
                color='#2c82ff',
                line_color='#2c82ff',
            ),
            #hovertemplate = hovertemplate,
        ))

        n_tick = int(max(x_scatter)/10)

        scatter_dead.update_traces(mode='markers', marker=dict(line_width=1, symbol='circle', size=16))

        scatter_dead.update_layout(
            title="Comparison dead ",
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='rgb(102, 102, 102)',
                tickfont_color='rgb(102, 102, 102)',
                showticklabels=True,
                dtick=n_tick,
                ticks='outside',
                tickcolor='rgb(102, 102, 102)',
                title ='Dead',
            ),
            margin=dict(l=140, r=40, b=50, t=80),
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='closest',
        )

        y_stack_bar = [filename.split('.')[0] for filename in norm_dict_upload_files.keys()]

        S = []
        E = []
        I = []
        R = []
        D = []

        for file in norm_dict_upload_files.keys():
            last_day = len(norm_dict_upload_files[file]['S']) - 1
            
            S.append(norm_dict_upload_files[file]['S'][last_day])
            E.append(norm_dict_upload_files[file]['E'][last_day])
            I.append(norm_dict_upload_files[file]['I'][last_day])
            R.append(norm_dict_upload_files[file]['R'][last_day])
            D.append(norm_dict_upload_files[file]['D'][last_day])

        #stack_bar

        colors = {'S':'#0000ff', 'E':'#ffa300', 'I':'#ff0000', 'D':'#000000', 'R':'#00ff00'}
        stack_bar = go.Figure()
        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=S,
            name='S',
            orientation='h',
            marker=dict(
                color= colors['S'],
            )
        ))

        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=E,
            name='E',
            orientation='h',
            marker=dict(
                color=colors['E'],
            )
        ))

        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=I,
            name='I',
            orientation='h',
            marker=dict(
                color=colors['I'],
            )
        ))


        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=R,
            name='R',
            orientation='h',
            marker=dict(
                color=colors['R'],
            
            )
        ))



        stack_bar.add_trace(go.Bar(
            y=y_stack_bar,
            x=D,
            name='D',
            orientation='h',
            marker=dict(
                color=colors['D'],
                )
        ))

        stack_bar.update_layout(barmode='stack', title = 'Summary at the end of simulations')

        #print("stack_bar")
        #stack_bar.write_image("test.png")
        #stack_bar.write_image("test.pdf")
        #print("fine stack_bar")

        
        otuputs = [graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar]
        names = ['graph_infected.pdf', 'graph_dead.pdf', 'graph_tot_inf.pdf', 'graph_simulation_len.pdf', 'heatMap.pdf', 'scatter_dead.pdf', 'stack_bar.pdf']

        # to used need to install orca!
        if save_pdf == True:
            for index in range(len(otuputs)):
                if isinstance(otuputs[index], dict):
                    fig = go.Figure(otuputs[index])
                    fig.write_image(names[index])
                else:
                    otuputs[index].write_image(names[index])

        return otuputs



@app.callback([ Output('file-list', 'children'),
                Output('table_parameters', 'children'),
                Output('table_parameters2', 'children'),
                Output('table_parameters3', 'children'),
                Output('alert_div', 'children'),
                
                # graph to return
                Output('graph_comparison_inf', 'figure'),
                Output('graph_comparison_dead', 'figure'),
                Output('graph_comparison_total_inf','figure'),
                Output('graph_simulation_len', 'figure'),
                Output('heatMap', 'figure'),
                Output('scatter_dead', 'figure'),
                Output('stack_bar', 'figure'),

                # view or not view the graph
                Output('graph_comparison_inf', 'style'),
                Output('graph_comparison_dead', 'style'),
                Output('graph_comparison_total_inf', 'style'),
                Output('graph_simulation_len', 'style'),
                Output('heatMap', 'style'),
                Output('scatter_dead', 'style'),
                Output('stack_bar', 'style'),
                ],

              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])

# read all selected files and show comparison 
def update_output(list_of_contents, list_of_names):
    read_error = []
    dict_upload_files = {}
    print("list_of_names: ", list_of_names)
    
    if list_of_contents is not None:
        for name, data in zip(list_of_names, list_of_contents):
            file_content = parse_contents(name, data)
            if file_content == 'Error':
                print('There was an error processing this file: ' + name)
                read_error.append(name)
            else:
                dict_upload_files[name] = file_content
    
    # no file or only error file
    if len(dict_upload_files.keys()) == 0:
        if len(read_error) > 0:
            alert = dbc.Alert("Can't read this files: " + str(read_error), id = 'alert_id', color="danger",  duration=6000)
        else:
            alert = []
        return [html.Li("No files yet!"), [], [], [], alert, {}, {}, {}, {}, {}, {}, {}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display': 'None'}, {'display':'None'}, {'display':'None'},{'display':'None'}]
    
    else:

        graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar = create_all_graphs(dict_upload_files, save_pdf = False)
        
        # list updload files
        list_name = [html.Li(filename) for filename in dict_upload_files.keys()]
        
        if len(read_error) == 0:
            alert = dbc.Alert("Succesfully read all files" , id = 'alert_id', color="success",  duration=6000)
        else:
            alert = dbc.Alert("Can't read this files: " + str(read_error), id = 'alert_id', color="danger",  duration=6000)

        table_values = []
        for file in dict_upload_files.keys():
            dict_upload_files[file]['parameters']['sim_name'] = file.split('.')[0]
            table_values.append(dict_upload_files[file]['parameters'])
        
        table = [   
                    html.H4("Simulation parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name','R_0', 'n_of_families', 'number_of_steps', 'incubation_days', 'infection_duration', 'n_initial_infected_nodes']],
                        data= table_values,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                ]
        table2 = [  
                    html.H4("Restriction parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name', 'initial_day_restriction', 'restriction_duration', 'social_distance_strictness', 'restriction_decreasing']],
                        data=table_values,
                        #style_cell={'textAlign': 'left'},
                        #style_as_list_view=True,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                ] 
        table3 = [
                    html.H4("Testing and quaratine parameters"),
                    dash_table.DataTable(
                        columns=[{"name": i, "id": i} for i in ['sim_name', 'n_test', 'policy_test', 'contact_tracing_efficiency', 'contact_tracing_duration']],
                        data=table_values,
                        #style_cell={'textAlign': 'left'},
                        #style_as_list_view=True,
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                        {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        sort_action='native',
                        sort_mode="multi",
                    ),
                        

        ]  
        
        #returns
        return [list_name, table, table2, table3, alert, graph_infected, graph_dead, graph_tot_inf, graph_simulation_len, heatMap, scatter_dead, stack_bar, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}]


            
    

# run app 
if __name__ == "__main__":
    app.run_server(debug=True, port=8080)