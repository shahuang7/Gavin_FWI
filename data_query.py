from env import credentials
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict
import json

def db_connect(query):
    db = credentials["primary_db"]
    conn = psycopg2.connect(
        dbname=db["db_name"],
        user=db["db_user"],
        password=db["db_password"],
        host=db["db_host"],
        port=db["db_port"]
    )
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    # Convert to DataFrame
    df = pd.DataFrame(result, columns=columns)
    return df

def check_duplicate(df, col):
    duplicates_df = df.groupby(col).size().reset_index(name='count')
    duplicates_df = duplicates_df[duplicates_df['count'] > 1]
    return duplicates_df

# Define a function to filter tables based on model_name, build_type, or skuno
def filter_model_tables(model_tables, model_name=None, build_type=None, skuno=None):
    """
    Filters model_tables based on model_name, build_type, or skuno.
    
    Args:
    - model_name (str, optional): The model name to filter.
    - build_type (str, optional): The build type to filter.
    - skuno (str, optional): The skuno to filter.
    
    Returns:
    - dict: A dictionary of filtered tables.
    """
    filtered_tables = {}
    
    for key, df in model_tables.items():
        key_parts = key.split("_")  # Extract model_name, build_type, and skuno from key
        
        # Ensure the key has enough parts to match
        if len(key_parts) < 3:
            continue
        
        model, build, sku = key_parts[:3]

        # Check conditions
        if (model_name and model_name not in model) or \
           (build_type and build_type not in build) or \
           (skuno and skuno not in sku):
            continue

        filtered_tables[key] = df

    # **Combine all filtered DataFrames into one**
    if filtered_tables:
        combined_df = pd.concat(filtered_tables.values(), ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no match found

# query for sn generated after 2024
test_query = '''
            WITH unique_sn AS (
                -- Ensure we only pick distinct serial_numbers
                SELECT DISTINCT sn.serial_number, wo.model_name, wo.build_type, wo.skuno
                FROM public.manufacturing_serialnumber sn
                INNER JOIN public.manufacturing_workorder wo ON wo.workorder_id = sn.workorder_id
                WHERE wo.sap_release_date >= '2024-01-01' AND sn.completed = '1'
            )
            SELECT 
                sn.model_name, sn.build_type, sn.skuno, mtr.serial_number, mtr.station, 
                mtr.result AS test_result
            FROM public.manufacturing_testingresult mtr
            INNER JOIN unique_sn sn ON sn.serial_number = mtr.serial_number; 
'''

# For boards that released after 2024, plot the one-time all-pass rate 
def plot_allpass_percentage(result_df):
    result_df_sorted = result_df.sort_values(by=['model_name', 'pass_percentage'], ascending=[True, False]).reset_index(drop=True)

    # Define model name groups for subplots
    plot_groups = {
        "ASTORIA": ["ASTORIA"],
        "GULP & ATHENA": ["GULP", "ATHENA"],
        "Others": ["FLATBACK", "RACKBACK", "Bondi Beach", "XENA", "Pebble Bea", "Pebble Beach", "CONAN"]
    }

    # Recompute x_labels for better visualization
    result_df_sorted["x_labels"] = result_df_sorted["model_name"] + "_" + result_df_sorted["build_type"] + "_" + result_df_sorted["skuno"]

    # Create subplots
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(14, 14), sharex=False)

    # Iterate over the plot groups
    for ax, (title, models) in zip(axes, plot_groups.items()):
        # Filter data for the models in this group
        plot_data = result_df_sorted[result_df_sorted["model_name"].isin(models)]

        # Sort data for better visualization
        plot_data = plot_data.sort_values(by="pass_percentage", ascending=False)

        # Plot bar chart
        bars = ax.bar(plot_data["x_labels"], plot_data["pass_percentage"], color='skyblue', edgecolor='black')

        # Annotate percentage values on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height, f'{height:.1f}', ha='center', va='bottom', fontsize=8)

        # Customize subplot
        ax.set_title(f"Pass Percentage for {title}")
        ax.set_ylabel("Pass Percentage (%)")
        ax.set_xticklabels(plot_data["x_labels"], rotation=45, ha="right", fontsize=8)

    # Set common labels
    plt.xlabel("Model_Name_Build_Type_SKU")
    plt.tight_layout()
    plt.show()

def plot_failure_percentage_by_model(failure_df, model_names):
    """
    Plots a stacked bar chart for failure percentage by station for the given model(s).
    
    Parameters:
        failure_df (DataFrame): DataFrame containing failure percentage data.
        model_names (list or str): List of model names or a single model name to plot.
    """
    if isinstance(model_names, str):  # Convert single model to list
        model_names = [model_names]

    # Filter data for the given models
    model_data = failure_df[failure_df["model_name"].isin(model_names)]

    if model_data.empty:
        print(f"⚠️ No data found for models: {', '.join(model_names)}. Please check the dataset.")
        return

    # Prepare x-axis labels (Add model_name if multiple models are provided)
    if len(model_names) > 1:
        model_data["x_labels"] = model_data["model_name"] + "_" + model_data["build_type"] + "_" + model_data["skuno"]
    else:
        model_data["x_labels"] = model_data["build_type"] + "_" + model_data["skuno"]

    # Pivot data for stacking
    pivot_df = model_data.pivot(index="x_labels", columns="station", values="failure_percentage").fillna(0)
    # # Sort x_labels by total failure percentage (descending)
    # pivot_df["total_failure_percentage"] = pivot_df.sum(axis=1)  # Compute total percentage per SKU
    # pivot_df = pivot_df.sort_values(by="total_failure_percentage", ascending=False)
    # pivot_df.drop(columns=["total_failure_percentage"], inplace=True)  # Remove extra column after sorting

    # Create the stacked bar plot
    fig, ax = plt.subplots(figsize=(18, 6))

    bottom = np.zeros(len(pivot_df))  # Initialize bottom for stacking
    for station in pivot_df.columns:
        bars = ax.bar(pivot_df.index, pivot_df[station], bottom=bottom, label=station)
        bottom += pivot_df[station]

        # Annotate percentage values on bars
        for bar, value in zip(bars, pivot_df[station]):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                        f"{value:.1f}", ha='center', va='center', fontsize=8, color="black")

    # Customize plot
    ax.set_title(f"Failure Percentage by Station for {', '.join(model_names)}")
    ax.set_ylabel("Failure Percentage (%)")
    ax.set_xticklabels(pivot_df.index, rotation=45, ha="right")
    # Place legend below the title
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1), ncol=3, frameon=False)

    # Show the plot
    plt.xlabel("Build Type + SKU No.")
    plt.tight_layout()
    plt.show()

def create_repair_table(sn, station):
    final_query = f'''
                    WITH serial_info AS (
                        -- Step 1: Get model_name, build_type, skuno for the given serial_number
                        SELECT wo.model_name, wo.build_type, wo.skuno
                        FROM public.manufacturing_l10serialnumberlog msn
                        JOIN public.manufacturing_workorder wo ON msn.workorder_id = wo.workorder_id
                        WHERE msn.serial_number = {sn}
                        LIMIT 1  
                    ),

                    matching_serials AS (
                        -- Step 2: Get all serial numbers that match model_name, build_type, skuno
                        SELECT DISTINCT msn.serial_number
                        FROM public.manufacturing_l10serialnumberlog msn
                        JOIN public.manufacturing_workorder wo ON msn.workorder_id = wo.workorder_id
                        JOIN serial_info si ON wo.model_name = si.model_name AND wo.build_type = si.build_type AND wo.skuno = si.skuno
                    )
                    -- Step 4: Select required fields from manufacturing_testingresult
                    SELECT 
                        si.model_name, si.build_type, si.skuno, mtr.station, mtr.serial_number, 
                        SUBSTRING(CAST(rd.created_at AS TEXT) FROM 1 FOR 19) AS repair_detail_created_at,
                        rd.repair_code, 
                        mtr.result,
                        (SELECT STRING_AGG(value->>'symptom_label', ' | ') FROM jsonb_each(mtr.symptom_info::jsonb)) AS symptom_labels
                    FROM public.manufacturing_testingresult mtr
                    JOIN matching_serials ms ON mtr.serial_number = ms.serial_number
                    LEFT JOIN public.manufacturing_repairmain rm ON mtr.rowid = rm.testing_result_id
                    LEFT JOIN public.manufacturing_repairdetail rd ON rm.failure_sequence = rd.failure_sequence
                    JOIN serial_info si ON TRUE
                    WHERE mtr.station = {station};
                '''
    repair_table = db_connect(final_query)
    return repair_table

def find_matching_repairs(repair_df, repair_sn):
    """
    Finds matching serial numbers based on symptom labels and retrieves repair data,
    excluding rows where all results are 0.
    
    Parameters:
        repair_df (DataFrame): The repair dataset containing serial_number, symptom_labels, and result.
        repair_sn (str): The target serial number for finding symptom label matches.
    
    Returns:
        DataFrame: Filtered repair dataset containing matching serial numbers with relevant repair history.
    """
    # Step 1: Remove rows where result = 1
    filtered_df = repair_df[repair_df["result"] != 1]

    # Step 2: Get symptom labels for the given serial number (excluding NaN values)
    filtered_labels = filtered_df.loc[
        filtered_df['serial_number'] == repair_sn.replace("'", ""), 'symptom_labels'
    ].dropna()

    # Step 3: Extract unique symptom labels (cleaned & lowercased)
    symptom_set = {
        label.strip().lower()
        for labels in filtered_labels if isinstance(labels, str)  # Ensure labels are strings
        for label in labels.split('|')
    }

    # Step 4: Find serial numbers where symptom_labels contain any of the extracted symptoms
    matching_sn = filtered_df.loc[
        filtered_df['symptom_labels'].notna() & filtered_df['symptom_labels'].apply(
            lambda x: any(label in {l.strip().lower() for l in x.split('|')} if isinstance(x, str) else False
        for label in symptom_set)
        ), 'serial_number'
    ].unique()

    # Step 5: Exclude `repair_sn` from matching SNs
    matching_sn = [sn for sn in matching_sn if sn != repair_sn.replace("'", "")]

    # Step 6: Retrieve all rows for the matching serial numbers from the **original dataset**
    match_df = repair_df[repair_df['serial_number'].isin(matching_sn)]

    # Step 7: Remove serial numbers where all result values are 0 (never repaired successfully)
    valid_sn = match_df.groupby("serial_number")["result"].apply(lambda x: (x != 0).any())
    match_df = match_df[match_df["serial_number"].isin(valid_sn[valid_sn].index)]

    # Step 8: Clean symptom_labels in match_df (lowercase, strip, remove duplicates)
    match_df["symptom_labels"] = match_df["symptom_labels"].apply(
        lambda x: "|".join(sorted(set(l.strip().lower() for l in x.split('|')))) if isinstance(x, str) else x
    )

    return symptom_set, match_df

def symptom_result(repair_sn):
    query = f'''
            SELECT 
                mtr.serial_number,
                mtr.station,
                mtr.test_start_time,
                mtr.test_end_time,
                mtr.symptom_info,
                rd.repair_code,
                rd.repaired_description 
            FROM manufacturing_testingresult mtr
            LEFT JOIN public.manufacturing_repairmain rm ON mtr.rowid = rm.testing_result_id
            LEFT JOIN public.manufacturing_repairdetail rd ON rm.failure_sequence = rd.failure_sequence
            WHERE mtr.serial_number = {repair_sn} 
            AND mtr.result = 0  -- Filtering failed tests only
            ORDER BY mtr.test_end_time ASC;
            '''
    symptom_table = db_connect(query)
    return symptom_table

def count_symptom_occurrences_with_repairs(result_df):
    """
    Extracts and counts unique (symptom_msg, symptom_label) combinations from symptom_info,
    and associates them with their respective repair details and repair codes.

    Parameters:
        result_df (DataFrame): The dataframe containing symptom_info, repair_code, and repaired_description.

    Returns:
        DataFrame: Aggregated count of unique symptom_msg and symptom_label combinations, along with repair details.
    """
    # Dictionary to count occurrences and collect repair details
    symptom_data_dict = {}

    for _, row in result_df.iterrows():
        # Parse symptom_info JSON (handle cases where it's not a valid JSON string)
        try:
            symptom_data = json.loads(row["symptom_info"]) if isinstance(row["symptom_info"], str) else row["symptom_info"]
        except json.JSONDecodeError:
            symptom_data = {}

        if isinstance(symptom_data, dict):
            unique_symptoms = set()
            for _, symptom in symptom_data.items():
                symptom_msg = symptom.get("symptom_msg", "N/A").strip()
                symptom_label = symptom.get("symptom_label", "N/A").strip()
                unique_symptoms.add((symptom_msg, symptom_label))

            # Store repair details
            for symptom_pair in unique_symptoms:
                if symptom_pair not in symptom_data_dict:
                    symptom_data_dict[symptom_pair] = {
                        "occurrence_count": 0,
                        "repair_codes": set(),
                        "repair_descriptions": set()
                    }

                symptom_data_dict[symptom_pair]["occurrence_count"] += 1
                if pd.notna(row["repair_code"]):
                    symptom_data_dict[symptom_pair]["repair_codes"].add(row["repair_code"])
                if pd.notna(row["repaired_description"]):
                    symptom_data_dict[symptom_pair]["repair_descriptions"].add(row["repaired_description"])

    # Convert to DataFrame
    symptom_count_df = pd.DataFrame(
        [{
            "symptom_msg": msg,
            "symptom_label": label,
            "occurrence_count": data["occurrence_count"],
            "repair_codes": "|".join(sorted(data["repair_codes"])) if data["repair_codes"] else "N/A",
            "repair_descriptions": "|".join(sorted(data["repair_descriptions"])) if data["repair_descriptions"] else "N/A"
        } for (msg, label), data in symptom_data_dict.items()]
    )

    # Sort by occurrence count in descending order
    symptom_count_df = symptom_count_df.sort_values(by="occurrence_count", ascending=False).reset_index(drop=True)

    return symptom_count_df

def create_intel_table(sn):
    query = f'''
        SELECT mtr.serial_number, wo.model_name, wo.build_type, wo.skuno, mtr.station, mtr.result,
                SUBSTRING(CAST(mtr.test_start_time AS TEXT) FROM 1 FOR 19) test_start_time,
                SUBSTRING(CAST(mtr.test_end_time AS TEXT) FROM 1 FOR 19) test_end_time,
                SUBSTRING(CAST(rm.repaired_date AS TEXT) FROM 1 FOR 19) repaired_date,
                mtr.symptom_info, rd.repair_code,rd.repaired_description 
        FROM manufacturing_testingresult mtr
        LEFT JOIN public.manufacturing_repairmain rm ON mtr.rowid = rm.testing_result_id
        LEFT JOIN public.manufacturing_repairdetail rd ON rm.failure_sequence = rd.failure_sequence
        LEFT JOIN public.manufacturing_serialnumber msn ON mtr.serial_number = msn.serial_number
        LEFT JOIN public.manufacturing_workorder wo ON msn.workorder_id = wo.workorder_id
        WHERE mtr.serial_number = {sn} 
        ORDER BY mtr.test_end_time, rm.repaired_date;
        '''
    idt_df = db_connect(query)
    return idt_df

def extract_symptom_info(result_df):
    result_df_copy = result_df.copy()
    symptom_count_dicts = []

    for _, row in result_df_copy.iterrows():
        # Parse symptom_info JSON (handle cases where it's None, empty, or not a valid JSON)
        try:
            symptom_data = json.loads(row["symptom_info"]) if isinstance(row["symptom_info"], str) else row["symptom_info"]
        except json.JSONDecodeError:
            symptom_data = {}

        symptom_counter = Counter()  # Dictionary to store counts of label: message pairs

        if isinstance(symptom_data, dict) and symptom_data:
            for _, symptom in symptom_data.items():
                msg = symptom.get("symptom_msg", "N/A").strip().lower()
                label = symptom.get("symptom_label", "N/A").strip().lower()
                symptom_counter[(label, msg)] += 1  # Increment count for each (label, msg) pair

        symptom_count_dicts.append(dict(symptom_counter) if symptom_counter else "N/A")

    # Add extracted dictionary as a new column
    result_df_copy["symptom_count_dict"] = symptom_count_dicts

    # Drop the original symptom_info column
    result_df_copy = result_df_copy.drop(columns=["symptom_info"])

    return result_df_copy

def process_symptom_info(df):
    """
    Processes the result DataFrame by:
    1. Extracting `symptom_dict` based on `symptom_info`, ensuring all messages for each label are collected.
    2. Handling cases where `failure_description` exists but does not match `symptom_label`.
       - Converts it to {failure_description: {label: message}}.
    3. Handling cases where `symptom_info` is an empty dictionary `{}` or NaN.
       - Converts it to {failure_description: ""}.
    4. Ensuring cases where `symptom_label` exists but `symptom_msg` is empty are included in `symptom_dict`.
       - Converts it to {label: ""}.
    5. Setting `isRepair`:
       - 1 if `result == 0` AND `failure_description` exists.
       - 0 if `result == 0` AND `failure_description` is None.
    6. Adding flags for specific conditions:
       - `no_match_flag`: True if `failure_description` exists but does not match any `symptom_label`.
       - `empty_symptom_flag`: True if `symptom_info` is an empty dictionary `{}` or NaN but `failure_description` exists.
       - `empty_message_flag`: True if `symptom_label` exists but has an empty `symptom_msg`.
    """

    symptom_dicts = []  # Store extracted symptom dictionaries
    no_match_flags = []  # Store flags for unmatched failure descriptions
    empty_symptom_flags = []  # Flag for empty symptom_info but with failure_description
    empty_message_flags = []  # Flag for cases where label exists but message is empty

    for _, row in df.iterrows():
        result = row["result"]
        failure_desc = row["failure_description"]  # Get failure_description
        symptom_info = row["symptom_info"]  # Get symptom_info JSON

        # Parse symptom_info safely
        if pd.isna(symptom_info):  # Handle NaN symptom_info
            symptom_data = None
        else:
            try:
                symptom_data = json.loads(symptom_info) if isinstance(symptom_info, str) else symptom_info
            except json.JSONDecodeError:
                symptom_data = {}

        symptom_dict = {}  # Dictionary to store {label: [messages]}
        matched = False  # Flag to check if failure_description matches any label
        empty_symptom = symptom_data is None or (isinstance(symptom_data, dict) and len(symptom_data) == 0)
        empty_message = False  # Flag for cases where label exists but message is empty

        # If symptom_info is NaN or empty but failure_description exists
        if empty_symptom and not pd.isna(failure_desc):
            symptom_dict[failure_desc.strip().lower()] = ""
            empty_symptom_flags.append(True)
        else:
            empty_symptom_flags.append(False)

        # If result == 0 and no failure_description -> Extract ALL symptom labels/messages
        if result == 0 and pd.isna(failure_desc) and isinstance(symptom_data, dict):
            for _, symptom in symptom_data.items():
                label = symptom.get("symptom_label", "").strip().lower()
                msg = symptom.get("symptom_msg", "").strip().lower()
                if label and msg:
                    symptom_dict.setdefault(label, []).append(msg)
                elif label and not msg:  # If label exists but message is empty
                    symptom_dict[label] = [""]
                    empty_message = True

        # If result == 0 and failure_description exists -> Match failure_description to symptom_label
        elif result == 0 and not pd.isna(failure_desc) and isinstance(symptom_data, dict):
            for _, symptom in symptom_data.items():
                label = symptom.get("symptom_label", "").strip().lower()
                msg = symptom.get("symptom_msg", "").strip().lower()

                if failure_desc.strip().lower() == label and msg:
                    symptom_dict.setdefault(label, []).append(msg)
                    matched = True
                elif failure_desc.strip().lower() == label and not msg:  # Label matches but message is empty
                    symptom_dict[label] = [""]
                    matched = True
                    empty_message = True

            # If no match was found, convert symptom_info to {failure_description: {label: message}}
            if not matched:
                converted_dict = {}
                for _, symptom in symptom_data.items():
                    label = symptom.get("symptom_label", "").strip().lower()
                    msg = symptom.get("symptom_msg", "").strip().lower()
                    if label and msg:
                        converted_dict[label] = msg
                    elif label and not msg:
                        converted_dict[label] = ""  # If message is empty, store empty string
                        empty_message = True
                symptom_dict[failure_desc.strip().lower()] = converted_dict

        # Convert list of messages to unique sorted messages
        symptom_dict = {label: sorted(set(messages)) if isinstance(messages, list) else messages 
                        for label, messages in symptom_dict.items()}
        
        symptom_dicts.append(symptom_dict if symptom_dict else "N/A")
        no_match_flags.append(not matched)  # True if no match found, False otherwise
        empty_message_flags.append(empty_message)  # True if label exists but message is empty

    # Add new columns to DataFrame
    df["symptom_dict"] = symptom_dicts
    df["no_match_flag"] = no_match_flags  # Add the no match flag
    df["empty_symptom_flag"] = empty_symptom_flags  # Add the empty symptom flag
    df["empty_message_flag"] = empty_message_flags  # Add the empty message flag
    df['isRepair'] = (df["result"] == 0) & df["failure_description"].notna()

    return df.drop(columns=['result'])

def compute_label_cycles(df):
    """
    Computes cycle counts for each label in `symptom_dict` for each serial_number.

    Adds:
    - `label_cycle`: Count of occurrences of each label per serial_number.
    - `label_message_cycle`: Count of occurrences of each (label, message) pair per serial_number.
    """

    # Sort the DataFrame by serial_number to ensure correct order
    df = df.sort_values(by=["serial_number"]).reset_index(drop=True)

    # Store label and label-message cycle counts per serial_number
    label_count_history = defaultdict(lambda: defaultdict(int))
    label_message_count_history = defaultdict(lambda: defaultdict(int))

    label_cycles = []
    label_message_cycles = []

    for _, row in df.iterrows():
        serial_number = row["serial_number"]
        symptom_dict = row["symptom_dict"]  # Expected to be {label: [messages]}

        label_cycle_dict = {}
        label_message_cycle_dict = {}

        if isinstance(symptom_dict, dict):
            for label, messages in symptom_dict.items():
                # Ensure messages are treated as a list
                if isinstance(messages, str):
                    messages = [messages]

                # Update label cycle count
                label_count_history[serial_number][label] += 1
                label_cycle_dict[label] = label_count_history[serial_number][label]

                for msg in messages:
                    label_msg_key = (label, msg)  # Use tuple instead of string concatenation
                    label_message_count_history[serial_number][label_msg_key] += 1
                    label_message_cycle_dict[label_msg_key] = label_message_count_history[serial_number][label_msg_key]

        # Store results
        label_cycles.append(label_cycle_dict)
        label_message_cycles.append(label_message_cycle_dict)

    # Add new columns to DataFrame
    df["label_cycle"] = label_cycles
    df["label_message_cycle"] = label_message_cycles
    df = df.drop(columns=['symptom_info', 'symptom_dict', 'failure_description', 'isRepair', 'no_match_flag', 'empty_symptom_flag', 'empty_message_flag'])
    return df

def search_label(df, keyword):
    filtered_df = df[df["label_cycle"].apply(lambda x: any(keyword in label for label in x.keys()))]
    return filtered_df








wo_cols = ['workorder_id', 'target_qty', 'finished_qty', 'skuno','build_type', 'production_version', 'model_name']
wo_prefixed_cols = [f"mw.{col}" for col in wo_cols]
wo_query = f'''
            SELECT 
                {', '.join(wo_prefixed_cols)},
                SUBSTRING(CAST(ml.date AS TEXT) FROM 1 FOR 19) AS action_date,
                ml.action
            FROM manufacturing_workorder mw
            JOIN (
                SELECT workorder_id, action, date 
                FROM manufacturing_l10workorderlog
                WHERE date::DATE >= TIMESTAMP '2024-07-01'
            ) ml ON mw.workorder_id = ml.workorder_id
        '''
wo_data = "wo_timeline.csv"

ms_cols = ['workorder_id', 'serial_number', 'generated_date', 'complete_date', 'pack_date', 'ship_date', 'update_date', 'station_id','failed', 'completed', 'shipped', 'printed']
ms_prefixed_cols = [
    f"SUBSTRING(CAST(ms.{col} AS TEXT) FROM 1 FOR 19) AS {col}" if col.endswith('date') else f"ms.{col}"
    for col in ms_cols
]
ms_query = f'''
            SELECT {', '.join(ms_prefixed_cols)}
            FROM manufacturing_serialnumber ms
            WHERE generated_date::DATE >= TIMESTAMP '2024-07-01'
            ORDER BY generated_date ASC
        '''
ms_data = "serial_number.csv"

mtr_cols = ['rowid', 'result', 'serial_number', 'station', 'test_start_time', 'test_end_time']
mtr_prefixed_cols = [
    f"SUBSTRING(CAST(mtr.{col} AS TEXT) FROM 1 FOR 19) AS {col}" if col.endswith('date') or col.endswith('time') else f"mtr.{col}"
    for col in mtr_cols
]
mtr_query = f'''
                SELECT 
                    mtr.rowid,
                    mtr.result,
                    mtr.serial_number,
                    mtr.station,
                    SUBSTRING(CAST(mtr.test_start_time AS TEXT) FROM 1 FOR 19) AS test_start_time,
                    SUBSTRING(CAST(mtr.test_end_time AS TEXT) FROM 1 FOR 19) AS test_end_time,
                    -- Extract and store only symptom_label values
                    (
                        SELECT STRING_AGG(value->>'symptom_label', ' | ') 
                        FROM jsonb_each(mtr.symptom_info::jsonb)
                    ) AS symptom_labels
                FROM manufacturing_testingresult mtr
                WHERE testing_date::DATE >= TIMESTAMP '2024-07-01'
                AND result = 0;
        '''
mtr_data = "testing_result.csv"

rm_cols = ['failure_sequence', 'station', 'failure_description', 'result', 
           'repaired_date', 'serial_number', 'failure_code', 'testing_result_id', 'debug_start_time']
rm_prefixed_cols = [
    f"SUBSTRING(CAST(rm.{col} AS TEXT) FROM 1 FOR 19) AS {col}" if col.endswith('date') or col.endswith('time') else f"rm.{col}"
    for col in rm_cols
]
rm_query = f'''
            SELECT {', '.join(rm_prefixed_cols)}
            FROM manufacturing_repairmain rm
            WHERE create_date::DATE >= TIMESTAMP '2024-07-01'
        '''
rm_data = "repair_main.csv"

rd_cols = ['repaired_description', 'failure_sequence', 'repair_code']
rd_prefixed_cols = [
    f"SUBSTRING(CAST(rd.{col} AS TEXT) FROM 1 FOR 19) AS {col}" if col.endswith('at') else f"rd.{col}" for col in rd_cols
]
rd_query = f'''
            SELECT {', '.join(rd_prefixed_cols)}
            FROM manufacturing_repairdetail rd
            WHERE created_at::DATE >= TIMESTAMP '2024-07-01'
        '''
rd_data = "repair_detail.csv"

repair_data = "repair_data.csv"

test_repair_data = "test_repair.csv"


repair_sn = 'FWI2504-10513'
repair_station = 'BB Functional Test'
final_query = f'''
                WITH serial_info AS (
                    -- Step 1: Get model_name, build_type, skuno for the given serial_number
                    SELECT wo.model_name, wo.build_type, wo.skuno
                    FROM public.manufacturing_l10serialnumberlog msn
                    JOIN public.manufacturing_workorder wo ON msn.workorder_id = wo.workorder_id
                    WHERE msn.serial_number = {repair_sn}
                    LIMIT 1  
                ),

                matching_serials AS (
                    -- Step 2: Get all serial numbers that match model_name, build_type, skuno
                    SELECT DISTINCT msn.serial_number
                    FROM public.manufacturing_l10serialnumberlog msn
                    JOIN public.manufacturing_workorder wo ON msn.workorder_id = wo.workorder_id
                    JOIN serial_info si ON wo.model_name = si.model_name AND wo.build_type = si.build_type AND wo.skuno = si.skuno
                ),
                -- Step 4: Select required fields from manufacturing_testingresult
                SELECT 
                    si.model_name, si.build_type, si.skuno, mtr.station, mtr.serial_number, 
                    SUBSTRING(CAST(rd.created_at AS TEXT) FROM 1 FOR 19) AS repair_detail_created_at,
                    rd.repair_code, 
                    mtr.result,
                    (SELECT STRING_AGG(value->>'symptom_label', ' | ') FROM jsonb_each(mtr.symptom_info::jsonb)) AS symptom_labels
                FROM public.manufacturing_testingresult mtr
                JOIN matching_serials ms ON mtr.serial_number = ms.serial_number
                LEFT JOIN public.manufacturing_repairmain rm ON mtr.rowid = rm.testing_result_id
                LEFT JOIN public.manufacturing_repairdetail rd ON rm.failure_sequence = rd.failure_sequence
                JOIN serial_info si ON TRUE
                WHERE mtr.station = {repair_station};
            '''

