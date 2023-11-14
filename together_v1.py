import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash import dash_table
import fastf1

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
    )
])

# Callback to update the selected Grand Prix and trigger next step
@app.callback(
    [Output('selected-gp', 'data'),
     Output('lap-time-graph', 'figure'),
     Output('datatable', 'data')],
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

    return {'selected_gp_name': selected_gp_name}, lap_time_figure, datatable_data

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
