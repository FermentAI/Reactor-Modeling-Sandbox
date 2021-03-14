import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash_apps.apps.myapp import app
from dash_apps.apps import app4, app2
import dash_apps.shared_callbacks
from dash_apps.shared_components import navbar, sidebar, sidebar_btn

# visit http://127.0.0.1:8050/ in your web browser.

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    sidebar,
    sidebar_btn,
    html.Div(id='page')
])

@app.callback(Output('page', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return app4.layout
    elif pathname == '/app2':
         return app2.layout
    else:
        return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognized..."),
        ]
    )

if __name__ == '__main__':
    app.run_server(debug = True)