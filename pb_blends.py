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


class Group:
    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name
        self.samples = []

    def add_sample(self, sample: object):
        self.samples.append(sample)

    def analyze_singles(self):
        for enum, sample in enumerate(self.samples, 1):
            print(f"    Working on sample {enum}/{len(self.samples)}")
            sample.get_all_attributes()

    def graph_singles(self):
        for sample in self.samples:
            sample.graph()

    def graph_all(self):
        cols = mcp.gen_color(cmap="copper", n=len(self.samples))
        sns.set_theme()
        sns.set_style("whitegrid")
        fig, ax = plt.subplots()
        ax.set_title(f"{self.name}")
        ax.set_xlabel("2 Theta [°]")
        ax.set_ylabel("Intensity [-]")
        ax.set_xlim(5, 30)
        maxYs = []
        for e, sample in enumerate(self.samples):
            maxYs.append(max(sample.y))
            plt.plot(
                sample.x,
                sample.y,
                color=cols[e],
                label=f"Aged {round((sample.age), 1)} hours",
            )
        ax.set_ylim(0, max(maxYs) + 1000)
        ax.legend(loc="upper left")
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(
            f"{os.path.split(sample.path)[0]}\{self.name} (grouped).png", dpi=300
        )
        plt.close()

    def graph_halftime(self):
        times = []
        c_phases = []
        phases_1 = []
        phases_2 = []
        for sample in self.samples:
            times.append(sample.age)
            c_phases.append(sample.crystallinity)
            phases_1.append(sample.phase1)
            phases_2.append(sample.phase2)
        sns.set_theme()
        sns.set_style("whitegrid")
        fig, ax = plt.subplots()
        ax.set_title(f"{self.name}")
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
        plt.savefig(
            f"{os.path.split(sample.path)[0]}\{self.name} (halftime).png", dpi=300
        )
        plt.close()


class Sample:
    def __init__(self, path: str):
        self.path = path
        self.format = path[-3:].lower()

    def get_name(self):
        file_name = os.path.split(self.path)[1]
        file_split = file_name.split(" ")
        name_split = file_split[1:-6]
        name = " ".join(str(x) for x in name_split)
        name += " %"
        self.name = name

    def get_age(self):
        file_name = os.path.split(self.path)[1]
        file_split = file_name.split(" ")
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
        self.age = age_hours

    def get_xy(self):
        if self.format == "asc":
            self.x, self.y = get_xy_asc(self.path)
        elif self.format == "itx":
            self.x, self.y = get_xy_itx(self.path)
        elif self.format == "scn":
            self.x, self.y = get_xy_scn(self.path)
        else:
            print("Could not read the file.")

    def align(self):
        if self.format == "itx":
            x_move = [k - 2 for k in self.x]
            self.x = x_move
        peaks, peaks_info = find_peaks(
            self.y[: int(len(self.y) * 1 / 3)], width=5, height=1000, prominence=200
        )
        last_dif = 10
        closest = 0
        for p in peaks:
            dif = 12 - self.x[p]
            if abs(dif) < last_dif:
                closest = dif
            last_dif = dif
        x_aligned = [x + closest for x in self.x]
        self.x = x_aligned

    def remove_air(self):
        y_air = np.linspace(self.y[0], self.y[-1], num=len(self.y))
        while True:
            difs = []
            for i in range(0, len(self.y)):
                dif = self.y[i] - y_air[i]
                difs.append(dif)
            if all(i >= 0 for i in difs):
                break
            else:
                for j in range(0, len(y_air)):
                    y_air[j] -= 1
        y_no_air = []
        for i in range(0, len(self.y)):
            y_no_air.append(self.y[i] - y_air[i])
        self.y_with_air = self.y
        self.air_line = y_air
        self.y = y_no_air

    def get_baseline(self):
        lam = 10000
        p = 0.0001
        niter = 100
        L = len(self.y)
        D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
        w = np.ones(L)
        for i in range(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = spsolve(Z, w * self.y)
            w = p * (self.y > z) + (1 - p) * (self.y < z)
        self.baseline = z

    def get_crystallinity(self):
        points_all = []
        points_base = []
        for i in range(0, len(self.x)):
            points_all.append([self.x[i], self.y[i]])
        points_all.append([self.x[0], self.y[0]])
        polygon_all = Polygon(points_all)
        area_all = polygon_all.area
        for i in range(0, len(self.x)):
            points_base.append([self.x[i], self.baseline[i]])
        points_base.append([self.x[0], self.baseline[0]])
        polygon_base = Polygon(points_base)
        area_base = polygon_base.area
        crystalline_area = 100 * (1 - (area_base / area_all))
        crystalline_area = round(crystalline_area, 1)
        self.crystallinity = crystalline_area

    def get_peaks(self):
        phase_1_max = 0
        phase_2_max = 0
        peak_1_coords = []
        peak_2_coords = []
        for i in range(0, len(self.x)):
            if 9.5 < self.x[i] < 10.3:
                if self.y[i] > phase_1_max:
                    phase_1_max = self.y[i]
                    peak_1_coords = [self.x[i], self.y[i]]
            if 11.9 < self.x[i] < 12.1:
                if self.y[i] > phase_2_max:
                    phase_2_max = self.y[i]
                    peak_2_coords = [self.x[i], self.y[i]]
        phase_1_percent = round(
            phase_1_max / (phase_1_max + phase_2_max) * self.crystallinity, 1
        )
        phase_2_percent = round(
            phase_2_max / (phase_1_max + phase_2_max) * self.crystallinity, 1
        )
        self.phase1 = phase_1_percent
        self.phase2 = phase_2_percent
        self.peak1 = peak_1_coords
        self.peak2 = peak_2_coords

    def get_all_attributes(self):
        self.get_name()
        self.get_age()
        self.get_xy()
        self.align()
        self.remove_air()
        self.get_baseline()
        self.get_crystallinity()
        self.get_peaks()

    def graph(self):
        sns.set_theme()
        sns.set_style("whitegrid")
        fig, ax = plt.subplots()
        ax.set_title(f"{self.name}\nAged {self.age} hours")
        ax.set_xlabel("2 Theta [°]")
        ax.set_ylabel("Intensity [-]")
        ax.set_xlim(5, 30)
        ax.set_ylim(0, max(self.y))
        plt.plot(
            self.x, self.y_with_air, "k-", label="Source data with air", alpha=0.25
        )
        plt.plot(self.x, self.y, "k-", label="Source data")
        plt.plot(self.x, self.baseline, "b-", label="Baseline")
        plt.plot(self.peak1[0], self.peak1[1], "xr")
        plt.plot(self.peak2[0], self.peak2[1], "xr")
        peak_1_index = self.x.index(self.peak1[0])
        peak_2_index = self.x.index(self.peak2[0])
        plt.plot(
            [self.peak1[0], self.peak1[0]],
            [self.baseline[peak_1_index], self.peak1[1]],
            "r-",
        )
        plt.plot(
            [self.peak2[0], self.peak2[0]],
            [self.baseline[peak_2_index], self.peak2[1]],
            "r-",
        )
        legend_text = f"Crystalline: {self.crystallinity} %\nPhase  I: {self.phase1} %\nPhase II: {self.phase2} %"
        ax.legend(title=legend_text, loc="upper left")
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(
            f"{os.path.split(self.path)[0]}\{self.name} (Aged {self.age} hours).png",
            dpi=300,
        )
        plt.close()


def make_groups(files: list):
    groups = []
    for file in files:
        file_name = os.path.split(file)[1]
        file_split = file_name.split(" ")
        code = file_split[0]
        name_split = file_split[1:-6]
        name = " ".join(str(x) for x in name_split)
        name += " %"
        if not any(group.code == code for group in groups):
            groups.append(Group(code, name))
        group_obj = [group for group in groups if group.code == code][0]
        group_obj.add_sample(Sample(file))
    return groups


def get_xy_asc(path: str):
    lines = []
    with open(path, "r") as f:
        for line in f:
            l = line.split()
            lines.append(l)
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


def get_xy_itx(path: str):
    lines = []
    with open(path, "r") as f:
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


def get_xy_scn(path: str):
    x = []
    y = []
    with open(path, "r") as f:
        for line in f:
            if len(line.split()) == 2:
                one_x = float(line.split()[0])
                one_y = float(line.split()[1])
                x.append(one_x)
                y.append(one_y)
    return x, y


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    print(f"\nSelect the RTG data files")
    files = askopenfilenames(
        title="Select the ITX, ASC or SCN files with RTG data.",
        filetypes=[
            ("RTG data files", ".itx"),
            ("RTG data files", ".asc"),
            ("RTG data files", ".scn"),
        ],
    )
    files_grouped = make_groups(files)
    print(f"\nWorking on {len(files)} files")
    print(f"Found {len(files_grouped)} groups")
    print("------------------------------------------------------")
    for group in files_grouped:
        print(f"{group.name:<35}          ({len(group.samples)} files)")
    print("------------------------------------------------------\n")
    t_start = time()
    for group in files_grouped:
        print(f"Working on group {group.name}")
        group.analyze_singles()
        group.graph_singles()
        group.graph_all()
        group.graph_halftime()
        print(f"Group {group.name} done\n")
    t_end = time()
    total_time = t_end - t_start
    print(f"All files done\n\nThe analysis took {round(total_time/60, 2)} minutes.")
    print(f"Average time per file: {round(total_time/len(files), 2)} seconds.")
    input("\nPress any key to exit")
    os.startfile(os.path.split(files[0])[0])
