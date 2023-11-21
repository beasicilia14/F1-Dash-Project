import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash import dash_table
import fastf1
import plotly.express as px

compound_colors = {
    'SOFT': 'red',
    'MEDIUM': 'yellow',
    'HARD': 'black',
    'INTERMEDIATE': 'green',
    'WET': 'blue',
}

# Get unique Grand Prix names
season_events = fastf1.get_event_schedule(2023)["EventName"]

# Dash app setup
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(children=[
    html.H1(children='Formula 1 Race Analysis'),

    # Step 1: Choose Grand Prix
    dcc.Dropdown(
        id='grand-prix-dropdown',
        options=[{'label': i, 'value': i} for i in list(season_events)],
        value=list(season_events)[0],  # Default selection is the first Grand Prix
        style={'width': '50%'}
    ),

    # Store to hold selected Grand Prix
    dcc.Store(id='selected-gp'),

    # Button to trigger the next step
    html.Button('Next Step', id='next-button'),

    # Step 2: Display lap time analysis graph
    dcc.Graph(id='lap-time-graph'),

    # Step 3: Display results data table
    dash_table.DataTable(
        id='datatable',
        columns=[
            {'name': 'Abbreviation', 'id': 'Abbreviation'},
            {'name': 'Classified Position', 'id': 'Position'},
            {'name': 'Position Change', 'id': 'PositionChange'},
        ],
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{PositionChange} < 0',
                    'column_id': 'PositionChange'
                },
                'color': 'tomato',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{PositionChange} > 0',
                    'column_id': 'PositionChange'
                },
                'color': 'green',
                'fontWeight': 'bold'
            }
        ],
        style_table={'height': '300px', 'overflowY': 'auto'},
    ),

    # Step 4: Compound Usage Visualization
    html.Hr(),  # Add a horizontal line for separation
    html.H2("Compound Usage Visualization"),
    html.Label("Select a driver:"),
    dcc.Dropdown(
        id='driver-dropdown',
        style={'width': '50%'}
    ),
    dcc.Graph(id='compound-usage-plot'),

])

# Callback to update the selected Grand Prix and trigger next step
@app.callback(
    [Output('selected-gp', 'data'),
     Output('lap-time-graph', 'figure'),
     Output('datatable', 'data'),
     Output('driver-dropdown', 'options')],
    [Input('next-button', 'n_clicks')],
    [State('grand-prix-dropdown', 'value')]
)
def update_selected_gp_and_graph(n_clicks, selected_gp_name):
    # Load session data for the selected Grand Prix
    selected_gp_session = fastf1.get_session(2023, selected_gp_name, "Race")
    selected_gp_session.load()
    selected_gp_df = selected_gp_session.laps

    # Get unique drivers for the selected Grand Prix
    unique_drivers = selected_gp_df['Driver'].unique()

    lap_time_traces = []
    for driver in unique_drivers:
        driver_data = selected_gp_df[selected_gp_df['Driver'] == driver]
        trace = {'x': driver_data['LapNumber'], 'y': driver_data['LapTime'], 'type': 'bar', 'name': driver}
        lap_time_traces.append(trace)

    lap_time_figure = {
        'data': lap_time_traces,
        'layout': {
            'title': f'Lap Time Analysis - {selected_gp_name}',
            'xaxis': {'title': 'Lap Number'},
            'yaxis': {'title': 'Lap Time'},
        }
    }

    # Load results data for the selected Grand Prix
    selected_gp_results = selected_gp_session.results
    selected_gp_results['GridPosition'] = pd.to_numeric(selected_gp_results['GridPosition'], errors='coerce').fillna(0).astype(int)
    selected_gp_results['Position'] = pd.to_numeric(selected_gp_results['Position'], errors='coerce').fillna(0).astype(int)
    selected_gp_results['PositionChange'] = selected_gp_results['GridPosition'] - selected_gp_results['Position']

    # Prepare data for the datatable
    datatable_data = selected_gp_results.to_dict('records')

    # Options for the driver dropdown
    driver_dropdown_options = [{'label': driver, 'value': driver} for driver in unique_drivers]

    return {'selected_gp_name': selected_gp_name}, lap_time_figure, datatable_data, driver_dropdown_options
# Callback to update the compound usage plot based on the selected driver
@app.callback(
    Output('compound-usage-plot', 'figure'),
    [Input('driver-dropdown', 'value')],
    [State('selected-gp', 'data')]
)
def update_compound_plot(selected_driver, selected_gp_data):
    if selected_gp_data is None:
        # If selected_gp_data is None, return an empty figure or handle it appropriately
        return px.line()

    selected_gp_name = selected_gp_data.get('selected_gp_name', '')
    if not selected_gp_name:
        # If selected_gp_name is empty, return an empty figure or handle it appropriately
        return px.line()

    session = fastf1.get_session(2023, selected_gp_name, "Race")
    session.load()
    driver_data = session.laps[session.laps['Driver'] == selected_driver]

    fig = px.line(
        driver_data,
        x='LapNumber',
        y=[1] * len(driver_data),
        color=driver_data['Compound'],
        line_dash_map={compound: 'solid' for compound in compound_colors.keys()},
        markers=True,
        color_discrete_map=compound_colors,
    )

    fig.update_layout(
        title=f'Compound Usage for {selected_driver} - {selected_gp_name}',
        xaxis_title='Lap',
        yaxis_title='',
        legend_title='Compound',
    )

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)