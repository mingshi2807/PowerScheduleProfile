import numpy as np
import pandas as pd
import random
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

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


# Generate random power levels for each step
def generate_power_levels(num_steps):
    return [random.uniform(POWER_MIN, POWER_MAX) for _ in range(num_steps)]


# Create the step function using the random durations and power levels
def create_step_function():
    durations = generate_random_durations()
    power_levels = generate_power_levels(len(durations))

    time_points = [0]  # Start at 0 hours
    power_schedule = []

    for i, duration in enumerate(durations):
        time_points.append(time_points[-1] + duration)
        power_schedule.extend([power_levels[i]] * duration)

    # Fill the remaining time points with the last power value if necessary
    while len(power_schedule) < TIME_PERIOD:
        power_schedule.append(power_schedule[-1])

    return np.arange(0, TIME_PERIOD, 1), power_schedule


# Generate multiple charging profiles
def generate_multiple_profiles(num_profiles=3):
    profiles = {}
    for i in range(num_profiles):
        time_axis, power_schedule = create_step_function()
        profile_name = f"Profile {i+1}"
        profiles[profile_name] = pd.DataFrame(
            {
                "Time (Hours)": time_axis,
                "Power Schedule (kWh)": power_schedule,
                "Profile": profile_name,
            }
        )
    return profiles


# Create a dictionary of profiles
profiles = generate_multiple_profiles(num_profiles=3)

# Combine all profiles into a single DataFrame for easy plotting
all_profiles_data = pd.concat(profiles.values(), ignore_index=True)

# Define colors for each profile
color_map = {
    "Profile 1": "#1f77b4",  # Blue
    "Profile 2": "#ff7f0e",  # Orange
    "Profile 3": "#2ca02c",  # Green
    # Add more colors if more profiles are generated
}

# Dash Application
app = dash.Dash(__name__)

app.layout = html.Div(
    [html.H1("EV Charging Profiles"), dcc.Graph(id="charging-profile-chart")]
)


@app.callback(
    Output("charging-profile-chart", "figure"), Input("charging-profile-chart", "id")
)
def update_graph(_):
    fig = px.bar(
        all_profiles_data,
        x="Time (Hours)",
        y="Power Schedule (kWh)",
        color="Profile",
        color_discrete_map=color_map,
        title="EV Charging Profiles Over Time",
    )
    return fig


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
