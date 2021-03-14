import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_apps.shared_components import *
from dash_apps.apps.myapp import app
import dash

from engine import Model, Simulator
import os
import plotly.express as px


path = os.getcwd()
# get all models in the models directory, skip penicilin
model_names = [o for o in sorted(os.listdir(os.path.join('rms','models'))) if os.path.isdir(os.path.join('rms','models',o))]
model_names.remove('penicillin_goldrick_2017')
model_path = lambda model_name: os.path.join(path,'rms','models', model_name) 

# make a Dropdown Menu to select a models
dropdown_models = lambda pick: [dbc.DropdownMenuItem(m, id = m, active = True) if i is pick else dbc.DropdownMenuItem(m, id = m,  active = False) for i,m in enumerate(model_names)]

def sim(model_name):
    """
    Generates simulator object based on model name

    Arguments
    ---------
        model_name
    """ 
    simuluator = Simulator(model = Model(model_path(model_name)))
    variables = simuluator.model.mvars.default
    return simuluator, variables

def mvars(vars_df):
    """
    Generates sliders based on the variables in a DataFrame

    Arguments
    ---------
        vars_df: Pandas DataFrame containing variables
    """ 
    sliders = []
    for var in vars_df.index:
        if vars_df.loc[var,'Min'] is not False:
            minval = vars_df.loc[var,'Min']
        else:
            minval = vars_df.loc[var,'Value']*0.1

        if vars_df.loc[var,'Max'] is not False:
            maxval = vars_df.loc[var,'Max']
        else:
            maxval = vars_df.loc[var,'Value']*1.9

        slider = NamedSlider(
                    name= vars_df.loc[var,'Label'],
                    id="slider-"+var,
                    min=minval,
                    max=maxval,
                    step=(maxval-minval)/100,
                    value = vars_df.loc[var,'Value'],
                    other = {'units':vars_df.loc[var,'Units']}
                )
        sliders.append(slider)
    return sliders

# default to the first model 
mysim, myvars = sim(model_names[0])

# make a button to run the simulator
run_btn = dbc.Button(children = "Run Simulation", outline=True, size = "lg", color="primary", className="mr-1", id="btn_run")

# make a plot for output 
#sim_plot = dcc.Graph(id = 'sim_plot4')

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(children=[
        html.Button('Add Chart', id='add-chart',n_clicks=0),
    ]),
    html.Div(id='container', children=[])
])

@app.callback(
    Output('container','children'),
    [Input('add-chart','n_clicks')],
    [State('container','children')]
)

def display_graphs(n_click, div_children):
    new_child = html.Div(
        style={'width'='45%','display':'inline-block','outline':'thin lightgrey solid'},
        children=[
            dcc.Graph(
                id={
                    'type':'dynamic-graph',
                    'index':n_clicks
                },
                figure={}
            ),
            dcc.RadioItems(
                id={'type':'dynamic-choice',
                    'index':n_clicks
                },
                options=[{'label':'Bar Chart', 'value': 'bar'},
                         {'label': 'Line Chart', 'value': 'line'},
                         {'label': 'Pie Chart', 'value':'pie'}],
                value='line',
            ),
            dcc.Dropdown(
                id={
                    'type': 'dynamic-dpn-var1',
                    'index': n_clicks
                },
                options=[{'label': var, 'value': var} for var in np.sort(mysim.model.mvars.current.loc['Label']).unique()],
                multi=True,
                value=["F","V0"],
                clearable=False
            ),
            dcc.Dropdown(
                id={
                    'type': 'dynamic-dpn-var2',
                    'index': n_clicks
                },
                options=[{'label': var, 'value': var} for var in np.sort(mysim.model.mvars.current.loc['Label']).unique()],
                multi=True,
                value=["V0","F"],
                clearable=False
            )
        ]
    )
    div_children.append(new_child)
    return div_children

@app.callback(
    Output({'type': 'dynamic-graph', 'index':MATCH}, 'figure'),
    [Input(component_id={'type': 'dynamic-dpn-var1', 'index': MATCH}, component_property='value'),
     Input(component_id={'type': 'dynamic-dpn-var2', 'index': MATCH}, component_property='value'),
     Input(component_id={'type': 'dynamic-choice', 'index': MATCH}, component_property='value')]
)

'''def update_graph(var_1, var_2, chart_choice):
    print(var_1)
    new_df = mysim.model.mvars.current.loc[mysim.model.mvars.current.loc['Label'].isin(var_1)]
    
    if chart_choice == 'bar':
        new_df = new_df.groupby(['''





'''
# layout all the components to be displayed
content = html.Div(
    [
        dbc.Row([
            dbc.Col(
                dbc.DropdownMenu(
                    label = "Select a model",
                    children = dropdown_models(0),
                    right=False,
                    id = 'dd_models'
                ),
            )
        ]),
        dbc.Row(),
        dbc.Row([
            dbc.Col(id = 'sliders', children = mvars(myvars), width = 2),
            dbc.Col(sim_plot, width = 9)
        ]),
        dbc.Row(run_btn),
        dbc.Row(id = 'mvars4')
    ],
    id="page-content",
    style = CONTENT_STYLE
)

layout = html.Div(
    [
        content,
        html.Div(id='dummy-output4')
    ],
)

# callback to update the simulator with the selected model
@app.callback(
    [Output("dd_models", "children"),
    Output("sliders", "children")],
    [Input(m, "n_clicks") for m in model_names],
)
def update_label(*args):
    ctx = dash.callback_context
    # this gets the id of the button that triggered the callback
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        new_pick = model_names.index(button_id)
    except:
        new_pick = 0
        
    global mysim, myvars
    mysim, myvars = sim(model_names[new_pick])
    return dropdown_models(new_pick), mvars(myvars)


# callback to update the model variables with the sliders / input box
@app.callback(
    [Output('slider-'+var+'-input', 'value') for var in myvars.index],
    [Output('slider-'+var, 'value') for var in myvars.index],
    [Input('slider-'+var+'-input', 'value') for var in myvars.index],
    [Input('slider-'+var, 'value') for var in myvars.index])

def update_mvars_slider(*args):
    sliders = list(args[int(len(args)/2):])
    inputs = list(args[:int(len(args)/2)])

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    for i,var in enumerate(myvars.index):
        if 'input' in button_id:
            sliders[i] = inputs[i]
        else:
            inputs[i] = sliders[i]
        mysim.model.mvars.current.loc[var, 'Value'] = sliders[i]

    return (*inputs, *sliders)

# callback to run the simulator and display data when the button is clicked
@app.callback(
    [
        Output('sim_plot4', 'figure'),
        Output('mvars4','children')
    ],
    Input('btn_run', 'n_clicks'))
def update_figure(n_clicks):
    data = mysim.run()
    table = generate_table(mysim.model.mvars.current)
    fig = px.scatter(data)
    mysim.model.reset()
    return fig, table
'''