import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_apps.shared_components import *
from dash_apps.apps.myapp import app



from engine import Model, Simulator
import os
import plotly.express as px


path = os.getcwd()
models = [os.path.join(path,'rms','models', o) for o in sorted(os.listdir(os.path.join('rms','models'))) if os.path.isdir(os.path.join('rms','models',o))]

sim = Simulator(model = Model(models[0]))

lol = sim.model.mvars.default
mvars = [NamedSlider(
            name= lol.loc[var,'Label'],
            id="slider-"+var,
            min=0,
            max=500,
            step=100,
            value = lol.loc[var,'Value'],
            other = {'units':lol.loc[var,'Units']}
            )
     for var in lol.index]

run_btn = dbc.Button(children = "Run Simulation", outline=True, size = "lg", color="primary", className="mr-1", id="btn_run")
sim_plot = dcc.Graph(id = 'sim_plot')

dropdown_items = [
    dbc.DropdownMenuItem(models[0]),
    dbc.DropdownMenuItem(models[1]),
    dbc.DropdownMenuItem(models[2]),
]

content = html.Div(
    [
        dbc.Row([
            dbc.Col(
                dbc.DropdownMenu(
                    label = "Select a model",
                    children = dropdown_items,
                    right=False,
                ),
            )
        ]),
        dbc.Row(dbc.Label("Alo, This is a row", width=2)),
        dbc.Row([
            dbc.Col(id = 'sliders', children = mvars, width = 2),
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
        html.Div(id='dummy-output')
    ],
)

@app.callback(
    Output('dummy-output', 'children'),
    [Input('slider-'+var, 'value') for var in lol.index])

def update_mvars(*args):
    for var, new_value in zip(lol.index,args):
        sim.model.mvars.current.loc[var, 'Value'] = new_value
    return None

@app.callback(
    [
        Output('sim_plot', 'figure'),
        Output('mvars4','children')
    ],
    Input('btn_run', 'n_clicks'))
def update_figure(n_clicks):
    data = sim.run()
    table = generate_table(sim.model.mvars.current)
    fig = px.scatter(data)
    sim.model.reset()
    return fig, table

# this callback uses the current pathname to set the active state of the
# corresponding nav link to true, allowing users to tell see page they are on
# @app.callback(
#     [Output(f"page-{i}-link", "active") for i in range(1, 4)],
#     [Input("url", "pathname")],
# )
# def toggle_active_links(pathname):
#     if pathname == "/":
#         # Treat page 1 as the homepage / index
#         return True, False, False
#     return [pathname == f"/page-{i}" for i in range(1, 4)]


# @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
# def render_page_content(pathname):
#     if pathname in ["/", "/page-1"]:
#         return html.P("This is the content of page 1!")
#     elif pathname == "/page-2":
#         return html.P("This is the content of page 2. Yay!")
#     elif pathname == "/page-3":
#         return html.P("Oh cool, this is page 3!")
#     # If the user tries to reach a different page, return a 404 message
#     return dbc.Jumbotron(
#         [
#             html.H1("404: Not found", className="text-danger"),
#             html.Hr(),
#             html.P(f"The pathname {pathname} was not recognised..."),
#         ]