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


# Define the debug decorator
def debug_decorator(debug=False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if debug:
                if isinstance(result, pd.DataFrame):
                    print("Debug Mode: DataFrame contents:")
                    print(result)
                else:
                    print(f"Debug Mode: Function {func.__name__} returned:")
                    print(result)
            return result

        return wrapper

    return decorator


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
@debug_decorator(debug=True)  # Enable debug mode
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
    #
    # debug test :
    # df = pd.DataFrame(
    #     {
    #         "Time (Hours)": time_period,
    #         "Power Schedule (kWh)": power_schedule,
    #         "Profile": profile_name,
    #     }
    # )
    # return df
    #
    return time_period, power_schedule


# Generate multiple charging profiles with priority logic
def generate_multiple_profiles():
    profile_names = ["Grid Energy", "Solar Power", "Surplus Solar"]
    profiles = {}
    for name in profile_names:
        time_axis, power_schedule = create_step_function_with_priority(name)
        profiles[name] = pd.DataFrame(
            {
                "Time (Hours)": time_axis,
                "Power Schedule (kWh)": power_schedule,
                "Profile": name,
            }
        )
    return profiles


# Create a dictionary of profiles
profiles = generate_multiple_profiles()

# Combine all profiles into a single DataFrame for easy plotting
all_profiles_data = pd.concat(profiles.values(), ignore_index=True)

# Define colors for each profile
color_map = {
    "Grid Energy": "#1f77b4",  # Blue
    "Solar Power": "#ff7f0e",  # Orange
    "Surplus Solar": "#2ca02c",  # Green
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
