import os
import numpy as np
import tkinter as tk
import seaborn as sns
from time import time
from scipy import sparse
from datetime import datetime
from scipy.signal import find_peaks
from shapely.geometry import Polygon
from matplotlib import pyplot as plt
from mycolorpy import colorlist as mcp
from scipy.sparse.linalg import spsolve
from shapely.geometry import LineString
from tkinter.filedialog import askopenfilenames

# Docstrings and comments generated with the help of an AI assistant trained by OpenAI (https://openai.com/)


def make_groups(files):
    """
    Group the given list of files into groups according to their code.

    Parameters:
    files (list): list of strings representing file names

    Returns:
    list: list of lists, where each inner list represents a group of files with the same code
    """
    one_group = []
    all_groups = []
    last_code = ""
    for file in files:
        file_name = os.path.split(file)[1]
        file_split = file_name.split(" ")
        name_split = file_split[1:-6]
        code = file_split[0]
        name = " ".join(str(x) for x in name_split)
        melt_date = file_split[-5]
        melt_time = file_split[-4]
        measure_date = file_split[-2]
        measure_time = file_split[-1][:-4]
        melt_raw = " ".join([melt_date, melt_time])
        measure_raw = " ".join([measure_date, measure_time])
        melt = datetime.strptime(melt_raw, "%d.%m.%Y %H.%M")
        measure = datetime.strptime(measure_raw, "%d.%m.%Y %H.%M")
        age = measure - melt
        age_secs = age.total_seconds()
        age_hours = round(age_secs / 3600, 1)
        file_info = [file, age_hours]
        if code != last_code:
            if bool(one_group):
                all_groups.append(one_group)
            one_group = [name]
            one_group.append(file_info)
        else:
            one_group.append(file_info)
        last_code = code
    all_groups.append(one_group)
    return all_groups


def make_XY_asc(file):
    """
    Extract the X and Y values from the given ASC file.

    Parameters:
    file (str): file name of the ASC file

    Returns:
    tuple: tuple containing two lists, the first representing the X values and the second representing the Y values
    """
    lines = []
    with open(file, "r") as f:
        for line in f:
            y = line.split()
            lines.append(y)
    lines = lines[:-1]
    for j in lines:
        number = float(j[0][:-6])
        exponent = int(j[0][-1])
        new_number = number * 10**exponent
        j[0] = new_number
        j[1] = int(j[1])
    x = [round(x[0], 3) for x in lines]
    y = [x[1] for x in lines]
    return x, y


# Extract the X and Y values from the ITX file
def make_XY_itx(file):
    """
    Extract the X and Y values from the given ITX file.

    Parameters:
    file (str): file name of the ITX file

    Returns:
    tuple: tuple containing two lists, the first representing the X values and the second representing the Y values
    """
    lines = []
    with open(file, "r") as f:
        for line in f:
            lines.append(line)
    lines = lines[3:-13]
    x_raw = [i.split(" ")[0] for i in lines]
    y_raw = [i.split(" ")[1] for i in lines]

    x = []
    y = []
    for j in range(0, len(x_raw)):
        x_number = float(x_raw[j][:8])
        x_exponent = int(x_raw[j][-1])
        y_number = float(y_raw[j][:8])
        y_exponent = int(y_raw[j][-1])
        x_new_format = round(x_number * 10**x_exponent, 2)
        y_new_format = round(y_number * 10**y_exponent, 10)
        x.append(x_new_format)
        y.append(y_new_format)
    return x, y


def align(file, format):
    """
    Align the X values in the given file to a reference point by finding the closest peak to the reference point in the
    first third of the data, and shifting the entire dataset by the distance between the closest peak and the reference
    point. The X and Y values are extracted from the file based on its format.

    Parameters:
    file (str): file name of the data file
    format (str): file format of the data file, either "asc" or "itx"

    Returns:
    tuple: tuple containing two lists, the first representing the aligned X values and the second representing the Y values
    """
    if format == "asc":
        x, y = make_XY_asc(file)
    else:
        # The machine that returns data in ITX format is always shifted to the right by roughly 2
        x_too_shifted, y = make_XY_itx(file)
        x = [k - 2 for k in x_too_shifted]
    # Finding the peaks only in the first third of the data
    # The measurements go from 0 to 35 2-theta, so even big shifts shouldn't be further away
    peaks, peaks_info = find_peaks(
        y[: int(len(y) * 1 / 3)], width=5, height=1000, prominence=200
    )
    last_dif = 10
    closest = 0
    for p in peaks:
        dif = 12 - x[p]
        if abs(dif) < last_dif:
            closest = dif
        last_dif = dif
    x_new = [x + closest for x in x]
    return x_new, y


def make_air(y):
    """
    Remove the air line from the given Y values by subtracting an evenly spaced Y values from the original Y values. The
    evenly spaced Y values are generated by linearly interpolating between the first and last Y value in the original
    data. The resulting Y values are guaranteed to have no negative values.

    Parameters:
    y (list): list of Y values

    Returns:
    list: list of Y values with the air line removed
    """
    y_air = np.linspace(y[0], y[-1], num=len(y))
    while True:
        difs = []
        for i in range(0, len(y)):
            dif = y[i] - y_air[i]
            difs.append(dif)
        # If all lines in original measurement are above tha air line, subtract it
        # Ensures no part of the resulting data will be negative on the Y axis
        if all(i >= 0 for i in difs):
            break
        else:
            for j in range(0, len(y_air)):
                y_air[j] -= 1
    y_no_air = []
    for i in range(0, len(y)):
        y_no_air.append(y[i] - y_air[i])
    return y_no_air


def baseline_als(y, lam, p, niter=10):
    """
    Remove the baseline from the given Y values using an Asymmetric Least Squares (ALS) method. The baseline is
    approximated as a piecewise linear function with the given number of iterations.

    Parameters:
    y (list): list of Y values
    lam (float): regularization parameter for the ALS method
    p (float): smoothness parameter for the ALS method
    niter (int, optional): number of iterations for the ALS method, default is 10

    Returns:
    numpy array: array of Y values with the baseline removed
    """
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
    w = np.ones(L)
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z


# Use the baseline_als with tested values for the RTG data
def make_baseline(y):
    """
    Remove the baseline from the given Y values using the Asymmetric Least Squares (ALS) method. The baseline is
    approximated as a piecewise linear function with the default number of iterations, regularization parameter, and
    smoothness parameter.

    Parameters:
    y (list): list of Y values

    Returns:
    numpy array: array of Y values with the baseline removed
    """
    lam = 10000
    p = 0.0001
    niter = 100
    y_base = baseline_als(y, lam, p, niter)
    return y_base


def get_crystallinity(x, y, y_base):
    """
    Calculate the crystallinity of the given data by comparing the area under the curve of the Y values to the area
    under the curve of the baseline-corrected Y values.

    Parameters:
    x (list): list of X values
    y (list): list of Y values
    y_base (numpy array): array of Y values with the baseline removed

    Returns:
    float: crystallinity of the data, in percentage
    """
    points_all = []
    points_base = []
    for i in range(0, len(x)):
        points_all.append([x[i], y[i]])
    points_all.append([x[0], y[0]])
    polygon_all = Polygon(points_all)
    area_all = polygon_all.area
    for i in range(0, len(x)):
        points_base.append([x[i], y_base[i]])
    points_base.append([x[0], y_base[0]])
    polygon_base = Polygon(points_base)
    area_base = polygon_base.area
    crystalline_area = 100 * (1 - (area_base / area_all))
    crystalline_area = round(crystalline_area, 1)
    return crystalline_area


def get_peaks(x, y, crystalline_number):
    """
    Find the percentage of crystalline phases 1 and 2 in the data, as well as the coordinates of the highest peak
    for each phase. The percentages are calculated based on the height of the peaks relative to the total height
    of both peaks, multiplied by the given crystalline number.

    Parameters:
    x (list): list of X values
    y (list): list of Y values
    crystalline_number (float): percentage of crystalline material in the sample

    Returns:
    tuple: tuple containing the percentage of crystalline phase 1, percentage of crystalline phase 2, coordinates of
           the highest peak for phase 1, and coordinates of the highest peak for phase 2
    """
    phase_1_max = 0
    phase_2_max = 0
    peak_1_coords = []
    peak_2_coords = []
    for i in range(0, len(x)):
        if 9.5 < x[i] < 10.3:
            if y[i] > phase_1_max:
                phase_1_max = y[i]
                peak_1_coords = [x[i], y[i]]
        if 11.9 < x[i] < 12.1:
            if y[i] > phase_2_max:
                phase_2_max = y[i]
                peak_2_coords = [x[i], y[i]]
    phase_1_percent = round(
        phase_1_max / (phase_1_max + phase_2_max) * crystalline_number, 1
    )
    phase_2_percent = round(
        phase_2_max / (phase_1_max + phase_2_max) * crystalline_number, 1
    )
    return phase_1_percent, phase_2_percent, peak_1_coords, peak_2_coords


def graph_single(
    file_path,
    name,
    x,
    y,
    y_no_air,
    y_base,
    crystalline_percentage,
    phase_1,
    phase_2,
    peak_1,
    peak_2,
):
    """
    Generate a graph of the data for a single sample.

    Parameters:
    file_path (str): The path to the file that the data was loaded from.
    name (str): The name of the sample.
    x (list): A list of x values.
    y (list): A list of y values.
    y_no_air (list): A list of y values with air removed.
    y_base (list): A list of baseline y values.
    crystalline_percentage (float): The percentage of crystallinity.
    phase_1 (float): The percentage of phase I.
    phase_2 (float): The percentage of phase II.
    peak_1 (list): A list with x and y coordinates for peak 1.
    peak_2 (list): A list with x and y coordinates for peak 2.

    Returns:
    None
    """
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.set_title(name)
    ax.set_xlabel("2 Theta [°]")
    ax.set_ylabel("Intensity [-]")
    ax.set_xlim(5, 30)
    ax.set_ylim(0, max(y))
    plt.plot(x, y, "k-", label="Source data with air", alpha=0.25)
    plt.plot(x, y_no_air, "k-", label="Source data")
    plt.plot(x, y_base, "b-", label="Baseline")
    plt.plot(peak_1[0], peak_1[1], "xr")
    plt.plot(peak_2[0], peak_2[1], "xr")
    peak_1_index = x.index(peak_1[0])
    peak_2_index = x.index(peak_2[0])
    plt.plot([peak_1[0], peak_1[0]], [y_base[peak_1_index], peak_1[1]], "r-")
    plt.plot([peak_2[0], peak_2[0]], [y_base[peak_2_index], peak_2[1]], "r-")
    legend_text = f"Crystalline: {crystalline_percentage} %\nPhase  I: {phase_1} %\nPhase II: {phase_2} %"
    ax.legend(title=legend_text, loc="upper left")
    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{os.path.split(file_path)[0]}\{name}.png", dpi=300)
    plt.close()


def graph_group(sublist, name, format):
    """
    Plot a group of curves in a single figure.

    Parameters
    ----------
    sublist : list
        A list of lists, where each inner list contains a file path and a number representing the age of the sample in hours.
    name : str
        The name to give to the figure.
    format : str
        The format of the data in the files. Can be "asc" or "itx".

    Returns
    -------
    None
    """
    i = sublist
    cols = mcp.gen_color(cmap="copper", n=len(i))
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.set_title(f"{name}")
    ax.set_xlabel("2 Theta [°]")
    ax.set_ylabel("Intensity [-]")
    ax.set_xlim(5, 30)
    maxYs = []
    for e, j in enumerate(i):
        x, y = align(j[0], format)
        maxYs.append(max(y))
        y_no_air = make_air(y)
        plt.plot(x, y_no_air, color=cols[e], label=f"Aged {round((j[1]), 1)} hours")
    ax.set_ylim(0, max(maxYs) + 1000)
    ax.legend(loc="upper left")
    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{os.path.split(i[1][0])[0]}\{name} (grouped).png", dpi=300)
    plt.close()


def graph_halftime(sublist, name):
    """
    Plots a graph of time (x-axis) against the percentage of crystalline phase, phase 1 and phase 2 (y-axis).
    The graph also shows the intersection of phase 1 and phase 2 lines, if it exists.

    Parameters:
    sublist (list): A list of tuples, each tuple containing the path to a file, time (in hours),
                    percentage of crystalline phase, percentage of phase 1 and percentage of phase 2.
    name (str): The name of the graph.

    Returns:
    None
    """
    i = sublist
    times = []
    c_phases = []
    phases_1 = []
    phases_2 = []
    for j in range(0, len(i)):
        time_hrs = i[j][1]
        c_phase = i[j][2]
        phase_1 = i[j][3]
        phase_2 = i[j][4]
        times.append(time_hrs)
        c_phases.append(c_phase)
        phases_1.append(phase_1)
        phases_2.append(phase_2)
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.set_title(f"{name}")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Phase ammount [%]")
    ax.set_xlim(min(times), max(times))
    ax.set_ylim(0, round(max(c_phases) + 10, -1))
    plt.plot(times, c_phases, "k-", label=f"Crystalline phase", alpha=0.5)
    plt.plot(times, phases_1, "b-", label=f"Phase 1")
    plt.plot(times, phases_2, "r-", label=f"Phase 2")
    plt.legend(loc="upper left")
    if (
        len(times) > 1
        and (phases_1[0] - phases_2[0]) * (phases_1[-1] - phases_2[-1]) < 0
    ):
        line1 = LineString(np.column_stack((times, phases_1)))
        line2 = LineString(np.column_stack((times, phases_2)))
        intersection = line1.intersection(line2)
        xInter, yInter = intersection.xy[0][0], intersection.xy[1][0]
        plt.plot(*intersection.xy, "ko")
        plt.annotate(
            f"{round(xInter, 2)}",
            (xInter, yInter),
            xytext=(-14, 10),
            textcoords="offset points",
            fontsize=12,
            bbox=dict(
                facecolor="white", alpha=0.75, edgecolor="gray", boxstyle="round"
            ),
        )
    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{os.path.split(i[1][0])[0]}\{name} (halftime).png", dpi=300)
    plt.close()


# Create the root window
root = tk.Tk()
# Withdraw the root window (it will not be displayed)
root.withdraw()
# Print a message to the user
print(f"\nSelect the RTG data files")
# Open a file selection dialog to allow the user to select ITX or ASC files with RTG data
files = askopenfilenames(
    title="Select the ITX or ASC files with RTG data.",
    filetypes=[("RTG data files", ".itx"), ("RTG data files", ".asc")],
)
# Group the selected files
files_grouped = make_groups(files)
# Print the number of selected files and the number of groups
print(f"\nWorking on {len(files)} files")
print(f"Found {len(files_grouped)} groups")

# Print a separator line
print("------------------------------------------------------")
# Iterate over the groups
for i in files_grouped:
    # Print the name of the group and the number of files in it
    print(f"{i[0]:<35}          ({len(i)-1} files)")
# Print a separator line
print("------------------------------------------------------\n")

# Record the start time
t_start = time()

# Iterate over the groups
for i in files_grouped:
    # Get the group name and file paths
    name = i[0]
    paths = i[1:]
    # Print a message to the user
    print(f"Working on group {name}")
    # Iterate over the file paths
    for j in paths:
        # Get the file path, age, and file type
        file = j[0]
        age = j[1]
        filetype = file[-3:].lower()
        # Create a title for the file using the group name and age
        title_name = f"{name} (Aged {age} hours)"
        # Print a message to the user
        print(f"    Working on file {title_name}")
        # Align the data
        x, y = align(file, filetype)
        # Remove the air peak
        y_no_air = make_air(y)
        # Calculate the baseline
        y_base = make_baseline(y_no_air)
        # Calculate the crystallinity percentage
        crystalline_percentage = get_crystallinity(x, y_no_air, y_base)
        # Get the peaks and their coordinates
        phase_1, phase_2, peak_1_coords, peak_2_coords = get_peaks(
            x, y_no_air, crystalline_percentage
        )
        # Append the crystallinity percentage, phase 1, and phase 2 to the file path
        j.append(crystalline_percentage)
        j.append(phase_1)
        j.append(phase_2)
        # Generate a graph for the file
        graph_single(
            file,
            title_name,
            x,
            y,
            y_no_air,
            y_base,
            crystalline_percentage,
            phase_1,
            phase_2,
            peak_1_coords,
            peak_2_coords,
        )
    # Print a message to the user
    print("Individual files from group analyzed, making combined and halftime graphs")
    # Generate graphs for the group
    graph_group(paths, name, filetype)
    graph_halftime(paths, name)
    # Print a message to the user
    print(f"Group {name} done\n")

# Record the end time
t_end = time()
# Calculate the total time taken for the analysis
total_time = t_end - t_start
# Print the total time taken and the average time per file
print(f"All files done\n\nThe analysis took {round(total_time/60, 2)} minutes.")
print(f"Average time per file: {round(total_time/len(files), 2)} seconds.")
# Prompt the user to press a key to exit
input("\nPress any key to exit")
# Open the directory containing the files
os.startfile(os.path.split(file)[0])
