import pandas as pd
import pyodbc
import plotly.graph_objects as go
import os
import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=Warning)

def query_access_db(file_path, query):
    """
    Connects to an Access database, executes a query, and returns the results as a DataFrame.

    Parameters:
        file_path (str): Full path to the Access database file (*.mdb or *.accdb).
        query (str): SQL query to execute.

    Returns:
        pandas.DataFrame: Query results as a DataFrame.
    """
    try:
        # Ensure the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        # Define the connection string
        conn_str = (
            rf'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};'
            rf'DBQ={file_path};'
        )
        
        # Establish the connection
        conn = pyodbc.connect(conn_str)
        
        # Execute the query and fetch results into a DataFrame
        df = pd.read_sql_query(query, conn)
        # Close the connection
        conn.close()
        
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def filter_by_date_n_table(df, date, table):
    # Filter DataFrame for the given date and table
    filter_cols = ["LockScrewTime", "SN", "LockScrewTable", "PointNumber", "LockScrewResult"]
    filtered_df = df[(df["LockScrewTime"].dt.date == pd.to_datetime(date).date()) & (df["LockScrewTable"] == table)][filter_cols]
    return filtered_df

def process_data(df, table_side):
    """Filter and process data for left or right lock screw table."""
    df["LockScrewTime"] = pd.to_datetime(df["LockScrewTime"])
    filter_df = df[['LockScrewTime', 'SN', 'PointNumber', 'LockScrewTable', 'LockScrewResult']]
    filter_df["Hour"] = filter_df["LockScrewTime"].dt.floor("H")

    return filter_df[filter_df['LockScrewTable'] == table_side]

def identify_sequences(df):
    """Identify sequence groups within each SN."""
    df["Prev_PointNumber"] = df.groupby("SN")["PointNumber"].shift(1)
    df["New_Sequence_Flag"] = (df["PointNumber"] == 2) | (df["PointNumber"] != df["Prev_PointNumber"] + 1)
    df["Sequence_Group"] = df.groupby("SN")["New_Sequence_Flag"].cumsum()
    df.drop(columns=["Prev_PointNumber", "New_Sequence_Flag"], inplace=True)
    return df

def adjust_hour_per_sequence(df):
    """Assign the correct Hour_Adjusted for each sequence group."""
    # --- Step 2: Identify First & Last PointNumber Per Sequence ---
    seq_group = df.groupby(["SN", "Sequence_Group"])["PointNumber"].agg(["min", "max"]).reset_index()
    df = df.merge(seq_group, on=["SN", "Sequence_Group"], how="left")

    # --- Step 3: Determine the Correct Hour for Each Sequence_Group ---
    df["Hour"] = df["LockScrewTime"].dt.floor("H")

    # Find the minimum and maximum hour for each sequence group
    seq_time_group = df.groupby(["SN", "Sequence_Group"])["Hour"].agg(["min", "max"]).reset_index()
    seq_time_group.rename(columns={"min": "Start_Hour", "max": "End_Hour"}, inplace=True)
    df = df.merge(seq_time_group, on=["SN", "Sequence_Group"], how="left")

    # Step 4: Assign Hour_Adjusted Properly Per Sequence Group
    # Case 1: If the sequence group is fully within the same hour, it stays there
    mask_same_hour = df["Start_Hour"] == df["End_Hour"]
    df.loc[mask_same_hour, "Hour_Adjusted"] = df["Start_Hour"]

    # Case 2: If the sequence spans multiple hours, adjust accordingly
    mask_split_hour = df["Start_Hour"] < df["End_Hour"]
    df.loc[mask_split_hour, "Hour_Adjusted"] = df["LockScrewTime"].dt.floor("H")

    # --- Step 5: Adjust for Incomplete Sequences ---
    # Adjust hour per sequence group, considering only its own records
    for (sn, seq_group), group in df.groupby(["SN", "Sequence_Group"]):
        start_hour = group["Hour"].min()
        end_hour = group["Hour"].max()

        # If the sequence is fully within the same hour, keep it unchanged
        if start_hour == end_hour:
            df.loc[group.index, "Hour_Adjusted"] = start_hour
        else:
            # If the sequence is incomplete (not reaching 26), shift it forward by 1 hour
            if group["min"].iloc[0] == 2 and group["max"].iloc[0] < 26:
                df.loc[group.index, "Hour_Adjusted"] = start_hour + pd.Timedelta(hours=1)
            else:
                df.loc[group.index, "Hour_Adjusted"] = group["Hour"]


    # Ensure completed sequences remain in their original hour
    mask_complete = (df["min"] == 2) & (df["max"] == 26)
    df.loc[mask_complete, "Hour_Adjusted"] = df["Start_Hour"]

    # Handle cases where an incomplete sequence starts at 23:00 and should move to the next day
    mask_next_day = (df["Start_Hour"].dt.hour == 23) & (df["min"] == 2) & (df["max"] < 26)
    df.loc[mask_next_day, "Hour_Adjusted"] = df["Start_Hour"] + pd.Timedelta(hours=1)

    # Ensure alignment to full-hour values
    df["Hour_Adjusted"] = df["Hour_Adjusted"].dt.floor("H")

    # Drop unnecessary columns
    df.drop(columns=["min", "max", "Start_Hour", "End_Hour"], inplace=True)
    return df

def compute_pass_rate(df):
    """Compute the board pass rate per hour."""
    df["Board_ID"] = df.groupby(["SN", "Sequence_Group"]).ngroup()
    
    board_status = df.groupby("Board_ID").agg(
        min_point=("PointNumber", "min"),
        max_point=("PointNumber", "max"),
        all_ok=("LockScrewResult", lambda x: (x == "OK").all()),
        hour=("Hour_Adjusted", "first")
    ).reset_index()

    board_status["Pass"] = (board_status["min_point"] == 2) & (board_status["max_point"] == 26) & (board_status["all_ok"])

    pass_summary = board_status.groupby("hour").agg(
        Total_Boards=("Pass", "count"),
        Passed_Boards=("Pass", "sum")
    ).reset_index()

    pass_summary["Pass_Rate"] = (pass_summary["Passed_Boards"] / pass_summary["Total_Boards"]) * 100
    pass_summary["Pass_Rate"] = pass_summary["Pass_Rate"].map(lambda x: f"{x:.2f}%")
    pass_summary.rename(columns={"hour": "Hour_Adjusted"}, inplace=True)
    
    return pass_summary

def daily_yield(df, date):
    """Calculate the total number of unique boards processed in a day."""
    total_boards = df.loc[
        df['Hour_Adjusted'].dt.date == pd.to_datetime(date).date(), 
        "Total_Boards"
    ].sum().item()
    return total_boards

def plot_pass_summary(pass_summary_df, table, selected_date):
    """Plot pass rate (line) and stacked bar chart of pass/fail boards."""
    
    # Ensure Hour_Adjusted is datetime
    pass_summary_df["Hour_Adjusted"] = pd.to_datetime(pass_summary_df["Hour_Adjusted"])
    
    # Filter data by selected date
    filtered_df = pass_summary_df[pass_summary_df["Hour_Adjusted"].dt.date == selected_date.date()].copy()
    
    # Create full hourly range (00:00 - 23:00)
    full_hours = pd.date_range(start=selected_date, periods=24, freq="H")
    
    # Ensure all hours exist in the data, fill missing with 0
    hourly_df = pd.DataFrame({"Hour_Adjusted": full_hours})
    merged_df = hourly_df.merge(filtered_df, on="Hour_Adjusted", how="left").fillna(0)
    
    # Compute failed boards
    merged_df["Failed_Boards"] = merged_df["Total_Boards"] - merged_df["Passed_Boards"]
    
    # Convert pass rate back from string to float if necessary
    if isinstance(merged_df["Pass_Rate"].iloc[0], str):
        merged_df["Pass_Rate"] = merged_df["Pass_Rate"].str.rstrip('%').astype(float)

    # X-axis labels formatted as "HH:MM-HH:MM"
    tickvals = merged_df["Hour_Adjusted"]
    ticktext = [f"{t.strftime('%H:%M')}-{(t + pd.Timedelta(hours=1)).strftime('%H:%M')}" for t in tickvals]

    # Normalize bar height based on max total boards for the date
    max_total_boards = merged_df["Total_Boards"].max()
    merged_df["Normalized_Passed"] = (merged_df["Passed_Boards"] / max_total_boards) * 100 if max_total_boards > 0 else 0
    merged_df["Normalized_Failed"] = (merged_df["Failed_Boards"] / max_total_boards) * 100 if max_total_boards > 0 else 0

    # Create figure
    fig = go.Figure()

    # Stacked bar for passed and failed boards (Unified hovertemplate)
    hover_template = (
        "Time: %{x}<br>"
        "Total Boards: %{customdata[0]}<br>"
        "Pass Rate: %{customdata[1]:.2f}%<extra></extra>"
    )

    fig.add_trace(go.Bar(
        x=tickvals,
        y=merged_df["Normalized_Passed"],
        name="Passed Boards",
        marker_color="lightgreen",
        hovertemplate=hover_template,
        customdata=np.stack((merged_df["Total_Boards"], merged_df["Pass_Rate"]), axis=-1)
    ))

    fig.add_trace(go.Bar(
        x=tickvals,
        y=merged_df["Normalized_Failed"],
        name="Failed Boards",
        marker_color="lightcoral",
        hovertemplate=hover_template,
        customdata=np.stack((merged_df["Total_Boards"], merged_df["Pass_Rate"]), axis=-1)
    ))

    # Line for pass rate (Same hover info as bars)
    fig.add_trace(go.Scatter(
        x=tickvals,
        y=merged_df["Pass_Rate"],
        name="Pass Rate (%)",
        mode="lines+markers",
        line=dict(color="#4169E1", width=3),
        hovertemplate=hover_template,
        customdata=np.stack((merged_df["Total_Boards"], merged_df["Pass_Rate"]), axis=-1)
    ))

    # Add text labels on bars
    for i in range(len(merged_df)):
        if merged_df["Passed_Boards"].iloc[i] > 0:
            fig.add_annotation(
                x=tickvals[i],
                y=merged_df["Normalized_Passed"].iloc[i] / 2,  
                text=str(int(merged_df["Passed_Boards"].iloc[i])),
                showarrow=False,
                font=dict(color="black", size=12),
                xanchor="center",
                yanchor="middle"
            )
        if merged_df["Failed_Boards"].iloc[i] > 0:
            fig.add_annotation(
                x=tickvals[i],
                y=merged_df["Normalized_Passed"].iloc[i] + (merged_df["Normalized_Failed"].iloc[i] / 2),
                text=str(int(merged_df["Failed_Boards"].iloc[i])),
                showarrow=False,
                font=dict(color="black", size=12),
                xanchor="center",
                yanchor="middle"
            )

    # Update layout
    fig.update_layout(
        title={
            "text": f"{table} Table Hourly Pass Rate and Board Count",
            "x": 0.5,
            "xanchor": "center",
            "y": 0.98
        },
        
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",  # Keep it below the title
            y=1.02,  # Position relative to title
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10)  # Reduce font size if needed
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=45,
            showgrid=False
        ),
        yaxis=dict(title="Pass Rate (%)", range=[0, 100], showgrid=True),
        yaxis2=dict(overlaying="y", side="right", showticklabels=False),
        barmode="stack",
        showlegend=True,
        margin=dict(l=40, r=40, t=50, b=50)
    )

    return fig

def create_stacked_bar_chart(df, table):
    # Group by PointNumber and LockScrewResult to get counts
    grouped_data = df.groupby(["PointNumber", "LockScrewResult"]).size().reset_index(name="Count")

    # Pivot data to create columns for each LockScrewResult value
    pivot_data = grouped_data.pivot(index="PointNumber", columns="LockScrewResult", values="Count").fillna(0)

    # Ensure all values are numeric for calculations
    pivot_data = pivot_data.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Add 'Others' column by summing all results except 'Sliding', 'Floating', and 'OK'
    pivot_data['Others'] = pivot_data.drop(columns=['Sliding', 'Floating', 'OK'], errors='ignore').sum(axis=1)

    # Ensure that 'Sliding', 'Floating', and 'Others' always exist as columns
    for col in ['Sliding', 'Floating', 'Others']:
        if col not in pivot_data.columns:
            pivot_data[col] = 0  # Add the column with default value 0

    # Calculate total defect count per PointNumber
    pivot_data['Total'] = pivot_data[['Sliding', 'Floating', 'Others']].sum(axis=1)

    # Normalize defect counts based on the max total defects
    max_total_defects = pivot_data["Total"].max()
    if max_total_defects > 0:
        percentage_data = pivot_data[['Sliding', 'Floating', 'Others']].div(max_total_defects) * 100
    else:
        percentage_data = pivot_data[['Sliding', 'Floating', 'Others']].copy()  # Prevent division by zero

    percentage_data = percentage_data.fillna(0)  # Handle cases where Total is 0



    pivot_data['Hover'] = pivot_data.index.to_series().apply(
        lambda point: (
            f"Position {point}<br>"
            f"Total Error: {int(pivot_data.loc[point, 'Total'])} times<br>"
            + "<br>".join(
                f"{result}: {int(pivot_data.loc[point, result])} times ({(pivot_data.loc[point, result] / pivot_data.loc[point, 'Total']) * 100:.2f}%)"
                for result in ['Sliding', 'Floating', 'Others']
                if pivot_data.loc[point, result] > 0 and pivot_data.loc[point, 'Total'] > 0  # Avoid division by zero
            )
        )
    )

    # Create a stacked bar chart
    fig = go.Figure()
    for result in ['Sliding', 'Floating', 'Others']:  # Plot only these columns
        fig.add_trace(
            go.Bar(
                x=pivot_data.index,
                y=pivot_data[result],  # Use raw defect count for each category
                name=result,  # Label for the bar
                hoverinfo="text",  # Use custom hover info
                hovertext=pivot_data['Hover'],  # Use the Hover column for hover text
                text=[f"{int(pivot_data.loc[idx, result])}" for idx in pivot_data.index],  # Display raw counts as text
                textposition="inside"  # Position the text inside the bars
            )
        )


    # Update layout
    fig.update_layout(
        barmode="stack",  # Stacked bar mode
        title={
            "text": f"{table} Table Daily Defect Position",
            "x": 0.5,
            "xanchor": "center"
        },
        legend=dict(
            orientation="h",  # Horizontal legend
            y=1,            # Position above the plot
            x=0.5,            # Center the legend
            xanchor="center",  # Align legend center with title
            yanchor="bottom"   # Align bottom of legend with title
        ),
        xaxis=dict(title="Position", tickmode="linear"),
        yaxis=dict(
            title="Defect Count",  # Show raw count instead of percentage
            showgrid=True
        ),
        legend_title=None,
        margin=dict(l=20, r=20, t=70, b=50)  # Adjust margins to fit legend
    )

    return fig

