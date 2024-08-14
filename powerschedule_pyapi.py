# KO
#
#
import numpy as np
import pandas as pd
import random
from taipy.gui import Gui

# Constants
TIME_PERIOD = 24  # 24 hours for a full day
NUM_STEPS = 10  # Number of random steps to generate
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


# Generate the time axis and power schedule
time_axis, power_schedule = create_step_function()

# Prepare data for Taipy GUI
data = pd.DataFrame({"Time (Hours)": time_axis, "Power Schedule (kWh)": power_schedule})

# Instantiate the Gui object
gui = Gui()


# Define the page as a function
def ev_charging_profile_page():
    return gui.bar(
        data, x="Time (Hours)", y="Power Schedule (kWh)", height=400, width=800
    )


# Add the page to the GUI
gui.add_page("EVChargingProfile", ev_charging_profile_page)

# Run the GUI
gui.run()

