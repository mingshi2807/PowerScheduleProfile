import numpy as np
import pandas as pd
import random
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from scipy.stats import norm
from scipy.signal import savgol_filter

# Constants
TIME_PERIOD = 24  # 24 hours for a full day
POWER_MAX = 50  # Maximum power in kWh for any step
POWER_MIN = 5  # Minimum power in kWh for any step
STEP_MIN_DURATION = 1  # Minimum duration for a step (in hours)
STEP_MAX_DURATION = 6  # Maximum duration for a step (in hours)


# Generate random step durations that sum up to 24 hours
def generate_random_durations():
    durations = []
    total_duration = 0
    while total_duration < TIME_PERIOD:
        remaining_time = TIME_PERIOD - total_duration
        duration = min(
            random.randint(STEP_MIN_DURATION, STEP_MAX_DURATION), remaining_time
        )
        durations.append(duration)
        total_duration += duration
    return durations


# Create the step function using the random durations and prioritized power levels
def create_step_function_with_priority(profile_name):
    durations = generate_random_durations()
    time_points = [0]  # Start at 0 hours
    power_schedule = []

    for duration in durations:
        time_points.append(time_points[-1] + duration)

    time_period = np.arange(0, TIME_PERIOD, 1)

    # Apply different priority based on profile_name
    if profile_name == "Grid Energy":
        power_levels = [
            random.uniform(POWER_MAX * 0.7, POWER_MAX)
            if (18 <= hour < 24 or 0 <= hour < 6)
            else random.uniform(POWER_MIN, POWER_MAX * 0.3)
            for hour in time_period
        ]
    elif profile_name == "Solar Power":
        power_levels = [
            random.uniform(POWER_MAX * 0.6, POWER_MAX)
            if 10 <= hour < 16
            else random.uniform(POWER_MIN, POWER_MAX * 0.3)
            for hour in time_period
        ]
    elif profile_name == "Surplus Solar":
        power_levels = [
            random.uniform(POWER_MAX * 0.8, POWER_MAX)
            if 12 <= hour < 14
            else random.uniform(POWER_MIN, POWER_MAX * 0.3)
            for hour in time_period
        ]
    else:
        power_levels = [
            random.uniform(POWER_MIN, POWER_MAX * 0.3) for _ in time_period
        ]  # Default case

    for i, duration in enumerate(durations):
        power_schedule.extend([power_levels[time_points[i]]] * duration)

    # Fill the remaining time points with the last power value if necessary
    while len(power_schedule) < TIME_PERIOD:
        power_schedule.append(power_schedule[-1])

    df = pd.DataFrame(
        {
            "Time (Hours)": time_period,
            "Power Schedule (kWh)": power_schedule,
            "Profile": profile_name,
        }
    )

    return df


# Generate a custom user's mobility needs profile using Bayesian statistics
def generate_mobility_needs_profile():
    time_period = np.arange(0, TIME_PERIOD, 1)
    mobility_needs = []

    for hour in time_period:
        if (
            7 <= hour < 9 or 17 <= hour < 19
        ):  # Higher mobility needs during morning and evening
            mobility_needs.append(norm.rvs(loc=POWER_MAX * 0.8, scale=POWER_MAX * 0.1))
        elif 0 <= hour < 6:  # Lower mobility needs during night
            mobility_needs.append(norm.rvs(loc=POWER_MIN, scale=POWER_MIN * 0.5))
        else:  # Moderate mobility needs during the rest of the day
            mobility_needs.append(norm.rvs(loc=POWER_MAX * 0.4, scale=POWER_MAX * 0.2))

    mobility_needs = np.clip(
        mobility_needs, POWER_MIN, POWER_MAX
    )  # Ensure values are within range

    # Apply Savitzky-Golay filter to smooth the mobility needs curve
    smoothed_mobility_needs = savgol_filter(
        mobility_needs, window_length=5, polyorder=3
    )

    df = pd.DataFrame(
        {
            "Time (Hours)": time_period,
            "Power Schedule (kWh)": smoothed_mobility_needs,
            "Profile": "Mobility Needs",
        }
    )

    return df


# Generate multiple charging profiles with priority logic
def generate_multiple_profiles():
    profile_names = ["Grid Energy", "Solar Power", "Surplus Solar"]
    profiles = {}
    for name in profile_names:
        profiles[name] = create_step_function_with_priority(name)

    # Add the mobility needs profile to the profiles dictionary
    profiles["Mobility Needs"] = generate_mobility_needs_profile()

    return profiles


# Create a dictionary of profiles
profiles = generate_multiple_profiles()

# Separate the mobility needs profile from the others
mobility_needs_df = profiles.pop("Mobility Needs")
all_profiles_data = pd.concat(profiles.values(), ignore_index=True)

# Dash Application
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("EV Charging and Mobility Needs Profiles"),
        dcc.Graph(id="charging-profile-chart"),
    ]
)


@app.callback(
    Output("charging-profile-chart", "figure"), Input("charging-profile-chart", "id")
)
def update_graph(_):
    # Create stacked bar chart traces for Grid Energy, Solar Power, and Surplus Solar
    traces = []
    for profile in all_profiles_data["Profile"].unique():
        df = all_profiles_data[all_profiles_data["Profile"] == profile]
        traces.append(
            go.Bar(x=df["Time (Hours)"], y=df["Power Schedule (kWh)"], name=profile)
        )

    # Add a line trace for Mobility Needs
    traces.append(
        go.Scatter(
            x=mobility_needs_df["Time (Hours)"],
            y=mobility_needs_df["Power Schedule (kWh)"],
            mode="lines",
            line=dict(color="red", dash="dot"),
            name="Mobility Needs",
        )
    )

    # Combine traces in a single figure
    fig = go.Figure(traces)
    fig.update_layout(
        barmode="stack",  # Stack the bars in one column per time period
        title="EV Charging and Mobility Needs Profiles Over Time",
        xaxis_title="Time (Hours)",
        yaxis_title="Power Schedule (kWh)",
    )

    return fig


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
