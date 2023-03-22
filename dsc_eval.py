import os
import numpy as np
import tkinter as tk
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.signal import find_peaks
from tkinter.filedialog import askopenfilenames

DEBUG = 0


class Curve:
    def __init__(self, x, y, sign=-1):
        self.x = x
        self.y = y
        self.peaks = None
        self.peaks_info = None
        self.sign = sign

    def find_peaks(self):
        y_line = np.linspace(self.y[0], self.y[-1], num=len(self.y))
        y_flat = self.y - y_line
        self.peaks, self.peaks_info = find_peaks(
            y_flat * self.sign, width=(0.1, 400), height=(0.5, 100), prominence=(0.1, 100)
        )

    def plot(self, name, color):
        plt.plot(self.x, self.y, color, label=name)
        plt.plot(self.x[self.peaks], self.y[self.peaks], f'x{color}')
        for enum, peak in enumerate(self.peaks):
            plt.annotate(
                int(self.x[peak]),
                (self.x[peak], self.y[peak]),
                xytext=(-10, 15 * self.sign),
                textcoords="offset points",
                fontsize=12,
                bbox=dict(
                    facecolor='white', alpha=0.75, edgecolor='gray', boxstyle='round'
                ),
            )

    def plot_debug(self):
        for enum, peak in enumerate(self.peaks):
            text = f'{int(self.x[peak])}\n' \
                   f'W: {round(self.peaks_info["widths"][enum], 3)}\n' \
                   f'H: {round(self.peaks_info["peak_heights"][enum], 3)}\n' \
                   f'P: {round(self.peaks_info["prominences"][enum], 3)}'
            plt.annotate(
                text,
                (self.x[peak], self.y[peak]),
                xytext=(-10, 15 * self.sign),
                textcoords="offset points",
                fontsize=10,
                bbox=dict(
                    facecolor='white', alpha=0.75, edgecolor='red', boxstyle='round'
                ),
            )
            tri_l = [self.x[peak]-self.peaks_info['widths'][enum],
                     self.y[peak]-self.peaks_info['peak_heights'][enum] * self.sign]
            tri_r = [self.x[peak]+self.peaks_info['widths'][enum],
                     self.y[peak]-self.peaks_info['peak_heights'][enum] * self.sign]
            tri_t = [self.x[peak],
                     self.y[peak]]
            tri_x = [tri_l[0], tri_t[0], tri_r[0], tri_l[0]]
            tri_y = [tri_l[1], tri_t[1], tri_r[1], tri_l[1]]
            plt.fill_between(tri_x, tri_y, color='gray', alpha=0.3)


class Sample:
    def __init__(self, name, path, heat_1, heat_2, cool):
        self.name = name
        self.path = path
        self.curve_heat_1 = heat_1
        self.curve_heat_2 = heat_2
        self.curve_cool = cool

    def find_curve_peaks(self):
        self.curve_heat_1.find_peaks()
        self.curve_heat_2.find_peaks()
        self.curve_cool.find_peaks()

    def plot_curves(self):
        sns.set_theme()
        sns.set_style('whitegrid')
        self.curve_cool.plot('Cooling', 'r')
        self.curve_heat_2.plot('Second heating', 'b')
        self.curve_heat_1.plot('First heating', 'k')
        plt.title(self.name, fontweight='bold')
        plt.xlabel('Temperature [°C]')
        plt.ylabel('Heat flow [W/g]')
        plt.xlim(50, 275)
        plt.yticks(color='None', fontsize=0)
        plt.legend(loc='upper left')
        if DEBUG:
            self.curve_cool.plot_debug()
            self.curve_heat_2.plot_debug()
            self.curve_heat_1.plot_debug()
            fig_manager = plt.get_current_fig_manager()
            fig_manager.window.showMaximized()
            plt.show()
        else:
            plt.gcf().set_size_inches(16, 9)
            plt.savefig(f'{self.path[:-4]}.png', dpi=300)
            plt.close()


if __name__ == '__main__':
    files = askopenfilenames(
        title="Select text files with DSC evaluations.",
        filetypes=[("Text files", ".txt")],
    )
    samples = []

    print(f'Reading {len(files)} files\n')
    for file in files:
        file_name = os.path.split(file)[1][:-4]
        with open(file) as f:
            lines = f.read().replace(',', '.').splitlines()
        start_lines = []
        end_lines = []
        for index, line in enumerate(lines):
            if 'Curve Values:' in line:
                start_lines.append(index+3)
            if 'Results:' in line:
                end_lines.append(index - 2)

        heat1 = np.array(
            [[i.split()[2], i.split()[3]]
             for i in lines[start_lines[0]:end_lines[0]]
             if 50 < float(i.split()[2]) < 275]
        ).astype(float)
        heat2 = np.array(
            [[float(i.split()[2]), float(i.split()[3]) + 8]
             for i in lines[start_lines[2]:end_lines[2]]
             if 50 < float(i.split()[2]) < 275]
        ).astype(float)
        cool1 = np.array(
            [[float(i.split()[2]), float(i.split()[3]) + 8]
             for i in lines[start_lines[1]:end_lines[1]]
             if 50 < float(i.split()[2]) < 275]
        ).astype(float)

        samples.append(
            Sample(
                file_name,
                file,
                Curve(heat1.T[0], heat1.T[1]),
                Curve(heat2.T[0], heat2.T[1]),
                Curve(cool1.T[0], cool1.T[1], 1)
            )
        )

    for sample in samples:
        print(f'Analyzing: {sample.name}')
        sample.find_curve_peaks()
        sample.plot_curves()
