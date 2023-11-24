import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash import dash_table
import fastf1
import plotly.express as px
import plotly.graph_objects as go

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
app = dash.Dash(__name__, suppress_callback_exceptions=True)
# ...

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
    dcc.Dropdown(id='lap-dropdown', style={'width': '50%'}),  # Added Lap Dropdown
    dcc.Graph(id='compound-usage-plot'),

    # Added telemetry graph
    dcc.Graph(id='telemetry-graph'),

])

# ...

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

    # Store the selected Grand Prix data
    selected_gp_data = {'selected_gp_name': selected_gp_name, 'selected_gp_df': selected_gp_df.to_json()}
    
    return selected_gp_data, lap_time_figure, datatable_data, driver_dropdown_options

# Callback to update the lap dropdown based on the selected driver
@app.callback(
    [Output('lap-dropdown', 'options'),
     Output('lap-dropdown', 'value')],  # Added output to set default value for lap dropdown
    [Input('driver-dropdown', 'value')],
    [State('selected-gp', 'data')]
)
def update_lap_dropdown_options(selected_driver, selected_gp_data):
    if selected_gp_data is None or 'selected_gp_name' not in selected_gp_data:
        return [], None  # Return empty options and default value

    selected_gp_df = pd.read_json(selected_gp_data['selected_gp_df'])

    # Filter laps for the selected driver
    driver_laps = selected_gp_df[selected_gp_df['Driver'] == selected_driver]['LapNumber']

    # Options for the lap dropdown
    lap_dropdown_options = [{'label': f'Lap {lap}', 'value': lap} for lap in driver_laps]

    return lap_dropdown_options, driver_laps.min()  # Set default value to the minimum lap number

# Callback to update the compound usage plot based on the selected driver
@app.callback(
    Output('compound-usage-plot', 'figure'),
    [Input('driver-dropdown', 'value')],
    [State('selected-gp', 'data')]
)
def update_compound_plot(selected_driver, selected_gp_data):
    if selected_gp_data is None or 'selected_gp_name' not in selected_gp_data:
        # If selected_gp_data is None or incomplete, return an empty figure or handle it appropriately
        return px.line()

    selected_gp_name = selected_gp_data['selected_gp_name']
    selected_gp_df = pd.read_json(selected_gp_data['selected_gp_df'])

    driver_data = selected_gp_df[selected_gp_df['Driver'] == selected_driver]

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
# ...

# Callback to update graph based on selected lap
@app.callback(
    dash.dependencies.Output('telemetry-graph', 'figure'),
    [dash.dependencies.Input('lap-dropdown', 'value')],
    [dash.dependencies.State('driver-dropdown', 'value'),
     dash.dependencies.State('selected-gp', 'data')]
)
def update_graph(selected_lap, selected_driver, selected_gp_data):
    if selected_gp_data is None or 'selected_gp_name' not in selected_gp_data:
        # If selected_gp_data is None or incomplete, return an empty figure or handle it appropriately
        return go.Figure()


    selected_gp_name = selected_gp_data['selected_gp_name']
    selected_gp_df = pd.read_json(selected_gp_data['selected_gp_df'])
    selected_gp_session = fastf1.get_session(2023, selected_gp_name, "Race")
    selected_gp_session.load()
    selected_gp_df = selected_gp_session.laps

    # Filter data for the selected driver and lap
    driver_data = selected_gp_df[(selected_gp_df['Driver'] == selected_driver) & (selected_gp_df['LapNumber'] == selected_lap)]

    # Check if there is data for the selected lap
    if driver_data.empty:
        return px.line()

    # Get telemetry for the selected lap
   
    laps_df = selected_gp_df
    laps_df = laps_df[laps_df["Driver"]==selected_driver].copy()

    telem = driver_data.get_telemetry()
    telem['SessionTime'] = pd.to_timedelta(telem['SessionTime']).dt.total_seconds()

        
    # Get lap start times
    laps_df['LapStartTime'] = pd.to_timedelta(laps_df['LapStartTime']).dt.total_seconds()
    lap_start_times = laps_df["LapStartTime"].tolist()


    selected_lap_index = selected_lap - 1
    lap_time = lap_start_times[selected_lap_index]
    
    # Filter telemetry data for the selected lap using .loc to avoid the warning
    selected_lap_data = telem.loc[(telem['SessionTime'] >= lap_time) & (telem['SessionTime'] <= lap_start_times[selected_lap_index + 1])].copy()

    # Create an interactive line chart for the selected lap
    fig = px.line(selected_lap_data, x='SessionTime', y=['RPM', 'Speed', 'Throttle', 'nGear'],
                  labels={'value': 'Value', 'SessionTime': 'Time (seconds)'},
                  title=f'Telemetry Variables for Lap {selected_lap}')

    # Add vertical line for lap start
    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=lap_time,
            x1=lap_time,
            y0=0,
            y1=1,
            line=dict(color="red", width=2)
        )
    )

    return fig
# ...

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
