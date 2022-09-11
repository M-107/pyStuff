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

# Group the files into groups according to the code
def make_groups(files):
    one_group = []
    all_groups = []
    last_code = ""
    for file in files:
        file_name = os.path.split(file)[1]
        file_split = file_name.split(" ")
        name_split = file_split[1:-6]
        code = file_split[0]
        name = " ".join(str(x) for x in name_split)
        name += " %"
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


# Extract the X and Y values from the ASC file
def make_XY_asc(file):
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


# The asc data should always show a noticeable peak at 12 2-theta
# The measurements are sometimes slightly shifted, this functions corrects it
def align(file, format):
    if format == "asc":
        x, y = make_XY_asc(file)
    else:
        x_too_shifted, y = make_XY_itx(file)
        x = [k - 2 for k in x_too_shifted]
    # Finding the peaks only in the first third of the data
    # The measurements go from 0 to 35 2-theta, so even big shifts shouldn't be further away
    peaks, peaks_info = find_peaks(
        y[: int(len(y) * 1 / 3)], width=5, height=1000, prominence=200
    )
    last_dif = 10
    closest = 0
    # Find how close each peak is from 12 and remember the closest one
    for p in peaks:
        dif = 12 - x[p]
        if abs(dif) < last_dif:
            closest = dif
        last_dif = dif
    # Add the distance of the cloest peak to 12 to the whole dataset
    x_new = [x + closest for x in x]
    return x_new, y


# The measurement was concluded in regular atmosphere, which means that air is present in the data
# Because of it, the data steadily grows along the X axis
# This function finds the air line ands shifts it further down to not intersect the original line
def make_air(y):
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


# Taken from Asymmetric Least Squares Smoothing by P. Eilers and H. Boelens
# Finds the baseline of a 1d array
def baseline_als(y, lam, p, niter=10):
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
    lam = 10000
    p = 0.0001
    niter = 100
    y_base = baseline_als(y, lam, p, niter)
    return y_base


# Get the area under the whole graph and the area under the baseline
# All - Baseline = Crystalline
def get_crystallinity(x, y, y_base):
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


# Thanks to previous alignment, the peaks are now at set posititons
# Take a few points from around those positions and keep the largest one from each
# Phase one is around 10.1 and phase two is around 12
def get_peaks(x, y, crystalline_number):
    phase_1_max = 0
    phase_2_max = 0
    peak_1_coords = []
    peak_2_coords = []
    for i in range(0, len(x)):
        if 10 < x[i] < 10.3:
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


# Graphs a single file with various corrections and the peaks shown, mostly for ensuring no errors occured
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


# Graphs all files from a single group at once, used to ensure all shifts were done correctly
def graph_group(sublist, name, format):
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
        if format == "asc":
            x, y = make_XY_asc(j[0])
        else:
            x, y = make_XY_itx(j[0])
        maxYs.append(max(y))
        plt.plot(x, y, color=cols[e], label=f"Aged {round((j[1]), 1)} hours")
    ax.set_ylim(0, max(maxYs) + 1000)
    ax.legend(loc="upper left")
    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{os.path.split(i[1][0])[0]}\grouped {name}.png", dpi=300)
    plt.close()


# Graph the phase 1 and 2 ammounts from each group at various sample ages
# Their crossover is considered th phase II->1 transformation halftime
# Also show the crystalline phase, could be useful
def graph_halftime(sublist, name):
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
    # Set the visuals
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
    # Find the intersecting point of phase 1 and phase 2 lines if they intersect
    if (
        len(times) > 1
        and (phases_1[0] - phases_2[0]) * (phases_1[-1] - phases_2[-1]) < 0
    ):
        line1 = LineString(np.column_stack((times, phases_1)))
        line2 = LineString(np.column_stack((times, phases_2)))
        intersection = line1.intersection(line2)
        xInter, yInter = intersection.xy[0][0], intersection.xy[1][0]
        # Plot everything
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
    plt.savefig(f"{os.path.split(i[1][0])[0]}\halftime {name}.png", dpi=300)
    plt.close()


# Start of the script
root = tk.Tk()
root.withdraw()
# Ask for the files
# The naming scheme is important
# CODE NAME melted DD.MM.YYYY HH.MM measured DD.MM.YYYY HH.MM
print(f"\nSelect the RTG data files")
files = askopenfilenames(
    title="Select the ITX or ASC files with RTG data.",
    filetypes=[("RTG data files", ".itx"), ("RTG data files", ".asc")],
)

# Group the files and print some intro info about the groups
files_grouped = make_groups(files)
print(f"\nWorking on {len(files)} files")
print(f"Found {len(files_grouped)} groups")
print("------------------------------------------------------")
for i in files_grouped:
    print(f"{i[0]:<35}          ({len(i)-1} files)")
print("------------------------------------------------------\n")
t_start = time()

# Run all the functions on already grouped files
for i in files_grouped:
    name = i[0]
    paths = i[1:]
    print(f"Working on group {name}")
    for j in paths:
        file = j[0]
        age = j[1]
        filetype = file[-3:].lower()
        title_name = f"{name} (Aged {age} hours)"
        print(f"    Working on file {title_name}")
        x, y = align(file, filetype)
        y_no_air = make_air(y)
        y_base = make_baseline(y_no_air)
        crystalline_percentage = get_crystallinity(x, y_no_air, y_base)
        phase_1, phase_2, peak_1_coords, peak_2_coords = get_peaks(
            x, y_no_air, crystalline_percentage
        )
        j.append(crystalline_percentage)
        j.append(phase_1)
        j.append(phase_2)
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
    print("Individual files from group analyzed, making combined and halftime graphs")
    graph_group(paths, name, filetype)
    graph_halftime(paths, name)
    print(f"Group {name} done\n")

t_end = time()
print(f"All files done\n\nThe analysis took {round((t_end-t_start)/60, 2)} minutes.")
print(f"Average time per file: {round((t_end-t_start)/len(files), 2)} seconds.")
input("\nPress any key to exit")
os.startfile(os.path.split(file)[0])
