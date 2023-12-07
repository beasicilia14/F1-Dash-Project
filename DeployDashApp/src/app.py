import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from dash import dash_table
import fastf1
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import dcc, html

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import fastf1
from sklearn.preprocessing import LabelEncoder


# ... (existing imports)

app = dash.Dash(__name__, suppress_callback_exceptions=True)

compound_colors = {
    'SOFT': 'red',
    'MEDIUM': 'yellow',
    'HARD': 'black',
    'INTERMEDIATE': 'green',
    'WET': 'blue',
}

season_events = fastf1.get_event_schedule(2023)["EventName"]

app.layout = html.Div(children=[
    html.Img(
        src='https://cdn.motor1.com/images/mgl/O487B/s1/nuevo-logo-de-f1-2018.jpg',
        style={
            'width': '100px',
            'height': '100px',
            'margin': 'auto',
            'display': 'block',
        }), 
        
    html.H1(children='FORMULA 1 RACE ANALYSIS', style={'color':'white', 'textAlign':'center', 'background-color':'#ff1801'}),

    html.Div([
        dcc.Dropdown(
            id='grand-prix-dropdown',
            options=[{'label': i, 'value': i} for i in list(season_events)],
            value=list(season_events)[0],
        ),
        html.Button('Next Step', id='next-button', style={'textAlign': 'center'}),
        dcc.Store(id='selected-gp')
    ], style={'margin': '20px', 'textAlign': 'center'}),

    html.H2(children="Race Summary"),

    html.Div([
        dcc.Graph(id='lap-time-graph'),

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
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

    html.Hr(style={'border': '1px solid red'}),

    html.H2("Information per Driver"),

     html.Label("Select a driver:"),
        dcc.Dropdown(
            id='driver-dropdown',
            style={'width': '50%'}
        ),

    
    html.H3("Compound Strategy"),
    html.Div([
       
        dcc.Graph(id='compound-usage-plot'),

    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'}),

    html.H3("Telemetry data"),
    html.Div([
    
    html.Label("Select a lap:"),
    dcc.Dropdown(id='lap-dropdown', style={'width': '50%'}),
    dcc.Graph(id='telemetry-graph'),] ),

    html.Hr(style={'border': '1px solid red'}),

    html.Div([
        html.H2("ML Model"),
        dcc.Graph(id='feature-importances')
    ]),
    
    html.Footer(children="Author: Beatriz Sicilia   ", style={'color': 'white','textAlign': 'right','background-color':'#ff1801'})



] , style={'fontFamily': 'Helvetica, Arial, sans-serif'})


# Callback to update the lap-time-graph with the position evolution graph for all drivers
@app.callback(
    Output('lap-time-graph', 'figure'),
    [Input('next-button', 'n_clicks')],
    [State('grand-prix-dropdown', 'value')]
)
def update_position_evolution_graph_all_drivers(n_clicks, selected_gp_name):
    # Load session data for the selected Grand Prix
    selected_gp_session = fastf1.get_session(2023, selected_gp_name, "Race")
    selected_gp_session.load()
    selected_gp_df = selected_gp_session.laps

    # Get unique drivers for the selected Grand Prix
    unique_drivers = selected_gp_df['Driver'].unique()

    # Create a line chart with the position evolution for each driver
    fig = px.line(selected_gp_df, x='LapNumber', y='Position', color='Driver',
                  labels={'Position': 'Position', 'LapNumber': 'Lap Number'},
                  title=f'Driver Position Evolution - {selected_gp_name}')

    fig.update_layout(
        xaxis_title='Lap Number',
        yaxis_title='Position',
        plot_bgcolor ='white'
    )
 

    return fig

# Callback to update the selected Grand Prix and trigger next step
@app.callback(
    [Output('selected-gp', 'data'),
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
    
    return selected_gp_data, datatable_data, driver_dropdown_options


# Callback to do the ML model 
@app.callback(
    Output('feature-importances', 'figure'),
    [Input('next-button', 'n_clicks')],
    [State('grand-prix-dropdown', 'value')]
)
def create_model_and_visualization(n_clicks, selected_gp_name):
    selected_gp_session = fastf1.get_session(2023, selected_gp_name, "Race")
    selected_gp_session.load()
    selected_gp_df = selected_gp_session.laps
    df= selected_gp_df
    # Convert LapTime to seconds
    df['LapTime_seconds'] = df['LapTime'].dt.total_seconds()
    
    # Example: Features (X) and Target (y)
    feature_columns = ['LapNumber', 'Stint',
                        'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 
                        'Compound', 'TyreLife', 'FreshTyre', 'TrackStatus']

    X = df[feature_columns].copy()  # Create a copy of the DataFrame
    y = df['LapTime_seconds']  # Use the converted LapTime column

    # Label encode categorical columns
    le = LabelEncoder()
    X['Compound'] = le.fit_transform(X['Compound'])

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Impute missing values in features
    imputer = SimpleImputer(strategy='mean')
    X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns)

    # Impute missing values in the target variable
    imputer_y = SimpleImputer(strategy='mean')
    y_train_imputed = imputer_y.fit_transform(y_train.values.reshape(-1, 1))

    # Initialize the Gradient Boosting Regressor
    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)

    # Fit the model to the training data with imputed values
    gb_model.fit(X_train_imputed, y_train_imputed.ravel())

    # Get feature importances
    feature_importances = pd.Series(gb_model.feature_importances_, index=X.columns)

    # Sort feature importances in descending order
    sorted_feature_importances = feature_importances.sort_values(ascending=False)
    # Create an interactive bar chart for the feature importances
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sorted_feature_importances.index, y=sorted_feature_importances.values))

    fig.update_layout(
        title='Gradient Boosting Feature Importance for Lap Time Prediction',
        xaxis_title='Features',
        yaxis_title='Importance',
        height=500,
        width=800,
        plot_bgcolor ='white',
    )
    

    return fig

    







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
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[]))  # You can add an empty trace or customize as needed
        fig.update_layout(
            title="Please choose a Driver",
            xaxis_title="X Axis",
            yaxis_title="Y Axis",
            showlegend=False,  # You can customize legend visibility as needed
            plot_bgcolor="white"
        )
        return fig

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
        plot_bgcolor ='white',
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
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[]))  # You can add an empty trace or customize as needed
        fig.update_layout(
            title="Please choose a Lap",
            xaxis_title="X Axis",
            yaxis_title="Y Axis",
            showlegend=False,  # You can customize legend visibility as needed
            plot_bgcolor="white"
        )
        return fig


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
    selected_lap_data['RPM (X100)'] = selected_lap_data['RPM']/100 
    # Create an interactive line chart for the selected lap
    fig = px.line(selected_lap_data, x='SessionTime', y=[ 'RPM (X100)', 'Speed', 'Throttle', 'nGear'],
                  labels={'value': 'Value', 'SessionTime': 'Time (seconds)'},
                  title=f'Telemetry Variables for Lap {selected_lap}')

    
    fig.update_layout(
        plot_bgcolor ='white',
    )

    return fig
# ...




# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)