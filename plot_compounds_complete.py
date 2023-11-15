import dash 
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px


compound_colors = {
    'SOFT': 'red',
    'MEDIUM': 'yellow',
    'HARD': 'black',
    'INTERMEDIATE': 'green',
    'WET': 'blue',
}


session_austria= fastf1.get_session(2023, "Austria", "Race")
all_data = session_austria.load()
df = session_austria.laps 
print(df["Compound"].unique())


# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Compound Usage Visualization"),
    html.Label("Select a driver:"),
    dcc.Dropdown(
        id='driver-dropdown',
        options=[{'label': driver, 'value': driver} for driver in df['Driver'].unique()],
        value=df['Driver'].unique()[0],
    ),
    dcc.Graph(id='compound-usage-plot'),
])

# Define callback to update the plot based on the selected driver
@app.callback(
    Output('compound-usage-plot', 'figure'),
    [Input('driver-dropdown', 'value')]
)
def update_plot(selected_driver):
    driver_data = df[df['Driver'] == selected_driver]

    print(driver_data)
    fig = px.line(
        driver_data,
        x='LapNumber',
        y=[1] * len(driver_data),
        color=driver_data['Compound'],
        line_dash_map={compound: 'solid' for compound in compound_colors.keys()},
        markers=True, # Updated argument
        color_discrete_map=compound_colors,
    )

    fig.update_layout(
        title=f'Compound Usage for {selected_driver}',
        xaxis_title='Lap',
        yaxis_title='',
        legend_title='Compound',
    )

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
