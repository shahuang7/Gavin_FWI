import dash
from dash import dcc, html
import os
import screw_utils as su
from dash.dependencies import Input, Output
import datetime
import pandas as pd
import sys
# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Screw Machine"

# Ensure cwd is set to the EXE's directory
if getattr(sys, 'frozen', False):
    cwd = os.path.dirname(sys.executable)  # If running as an EXE
else:
    cwd = os.path.dirname(os.path.abspath(__file__))  # If running as a script
    print(cwd)
# App Layout
app.layout = html.Div([
    # Header with Title, Date Picker, and Numbers
    html.Div(
        [
            # Left Number
            html.Div(
                [
                    html.Label("Left Table Daily Yield:", className="header-left-label"),
                    html.Div(id="left-yield-number", className="header-left-number")
                ],
                className="header-left"
            ),
            # Title and Date Picker
            html.Div(
                [
                    html.H2(
                        "Lock Screw Machine",
                        className="header-title"
                    ),
                    html.Div(
                        [
                            html.Label("Select Date:", className="date-picker-label"),
                            dcc.DatePickerSingle(
                                id='date-picker',
                                date=datetime.date.today().strftime('%Y-%m-%d'),  # Default to today
                                display_format='YYYY-MM-DD',
                                className="date-picker"
                            ),
                            html.Label("Select Station:", className="date-picker-label"),  # Match Date Picker label
                            dcc.Dropdown(
                                id='station-dropdown',
                                options=[
                                    {'label': 'Station 1', 'value': 'station1'},
                                    {'label': 'Station 2', 'value': 'station2'},
                                    {'label': 'Station 3', 'value': 'station3'}
                                ],
                                value='station1',  # Default selection
                                clearable=False,
                                className="station-dropdown"
                            ),
                        ],
                        className="date-picker-container"  # Keep everything aligned
                    ),
                ],
                className="header-center"
            ),
            # Right Number
            html.Div(
                [
                    html.Label("Right Table Daily Yield:", className="header-right-label"),
                    html.Div(id="right-yield-number", className="header-right-number")
                ],
                className="header-right"
            ),
        ],
        className="header"
    ),
    # Graphs Wrapper
    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(
                        id='bar-line-plot-left',
                        className='dcc-graph',
                        config={'displayModeBar': False}
                    )
                ],
                className='graph-container'
            ),
            html.Div(
                [
                    dcc.Graph(
                        id='bar-line-plot-right',
                        className='dcc-graph',
                        config={'displayModeBar': False}
                    )
                ],
                className='graph-container'
            ),
            html.Div(
                [
                    dcc.Graph(
                        id='bar-line-plot-bottom-left',
                        className='dcc-graph',
                        config={'displayModeBar': False}
                    )
                ],
                className='graph-container'
            ),
            html.Div(
                [
                    dcc.Graph(
                        id='bar-line-plot-bottom-right',
                        className='dcc-graph',
                        config={'displayModeBar': False}
                    )
                ],
                className='graph-container'
            )
        ],
        className='graph-wrapper'
    ),
    # Interval for periodic updates
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Refresh every minute (in milliseconds)
        n_intervals=0  # Number of times the interval has been activated
    )
])

# Callback to refresh data every minute
@app.callback(
    Output('date-picker', 'date'),
    [Input('interval-component', 'n_intervals'),
    Input('station-dropdown', 'value')]  # Add station input
)
def refresh_data(n_intervals, selected_station):
    global station_df
    selected_date = datetime.date.today()
    
    # Determine the database file path
    station_file = os.path.join(cwd, f"{selected_station}.accdb")
    query = "SELECT * FROM LockScrewData"
    
    # Refresh the data
    station_df = su.query_access_db(station_file, query)

    return selected_date.strftime('%Y-%m-%d')  # Keep the current date as default

@app.callback(
    [Output("left-yield-number", "children"),
     Output("right-yield-number", "children"),
     Output('bar-line-plot-left', 'figure'),
     Output('bar-line-plot-right', 'figure'),
     Output('bar-line-plot-bottom-left', 'figure'),
     Output('bar-line-plot-bottom-right', 'figure')],
    [Input('date-picker', 'date'),
     Input('station-dropdown', 'value')]
)
def update_plots(selected_date, selected_station):
    selected_date = pd.to_datetime(selected_date)
    current_month = datetime.datetime.now().strftime("%Y-%m")
    selected_month = selected_date.strftime("%Y-%m")

    # Determine the correct database file path
    if selected_month == current_month:
        station_file = os.path.join(cwd, f"{selected_station}.accdb")  # Current month
    else:
        year_month = selected_date.strftime("%Y%m")
        station_file = os.path.join(cwd, "DatabaseBackup", f"{selected_station}-{year_month}.accdb")  # Historical data

    # Query the database
    query = "SELECT * FROM LockScrewData"
    df = su.query_access_db(station_file, query)
    print(df)
    # Process data
    left_df = su.process_data(df, "Left")
    right_df = su.process_data(df, "Right")
    left_df = su.identify_sequences(left_df)
    right_df = su.identify_sequences(right_df)
    left_df = su.adjust_hour_per_sequence(left_df)
    right_df = su.adjust_hour_per_sequence(right_df)
    left_pass_summary = su.compute_pass_rate(left_df)
    right_pass_summary = su.compute_pass_rate(right_df)
    # Compute daily yield
    left_yield = su.daily_yield(left_pass_summary, selected_date)
    right_yield = su.daily_yield(right_pass_summary, selected_date)
    # Generate plots
    left_pass_plot = su.plot_pass_summary(left_pass_summary, "Left", selected_date)
    right_pass_plot = su.plot_pass_summary(right_pass_summary, "Right", selected_date)

    # Filter data for left and right tables
    left_defect_df = su.filter_by_date_n_table(df, selected_date, "Left")
    right_defect_df = su.filter_by_date_n_table(df, selected_date, "Right")
    left_defect_plot = su.create_stacked_bar_chart(left_defect_df, "Left")
    right_defect_plot = su.create_stacked_bar_chart(right_defect_df, "Right")

    return left_yield, right_yield, left_pass_plot, right_pass_plot, left_defect_plot, right_defect_plot

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
