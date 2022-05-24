import os
import xlsxwriter
import numpy as np
import tkinter as tk
import seaborn as sns
from time import time
from datetime import datetime
from matplotlib import pyplot as plt
from tkinter.filedialog import askopenfilenames
from scipy.signal import find_peaks, savgol_filter

root = tk.Tk()
root.withdraw()
files = askopenfilenames(title="Select text files with DSC evaluations.", filetypes=[("Text files", ".txt")])
peaks = []
t0 = time()
for dataFile in files:
    t1 = time()
    path = os.path.split(dataFile)[0]
    name = os.path.split(dataFile)[1][:-4]
    print(f"Working on file {name}.")
    with open(dataFile) as f:
        data = f.read().splitlines()
    for x, i in enumerate(data):
        data[x] = i.replace(",",".")
    data = [[i for i in line.split()] for line in data]
    for i in data:
        if not i:
            i.append("empty")
    for i in data:
        try:
            i[0] = int(i[0])
        except:
            pass
    indexes = []
    for i in data:
        if isinstance(i[0], int):
            indexes.append(i[0])
        else:
            indexes.append(-1)
    maxI = max(indexes)
    mins = [i for i, e in enumerate(indexes) if e == 0]
    maxs = [i for i, e in enumerate(indexes) if e == maxI]

    data2 = data[mins[2] + 10: maxs[2] - 10]
    data4 = data[mins[1] + 10: maxs[1] - 10]
    data6 = data[mins[0] + 10: maxs[0] - 10]

    data2 = [i[3:5] for i in data2]
    data4 = [i[3:5] for i in data4]
    data6 = [i[3:5] for i in data6]

    xMin = round(float(data2[0][0]))
    xMax = round(float(data2[-1][0]))

    try:
        data2 = np.array(data2).astype(float)
        data4 = np.array(data4).astype(float)
        data6 = np.array(data6).astype(float)

        cut = int(round(len(data2)/20, 0))
        window = 71
        polyorder = 3
        pWidth = 50
        pHeigth = 0.3
        pProminence = 0.01

        x2, y2 = data2.T
        x4, y4 = data4.T
        x6, y6 = data6.T

        y4 += 1.5
        y6 += 1

        y2Smooth = savgol_filter(y2, window, polyorder)
        y4Smooth = savgol_filter(y4, window, polyorder)
        y6Smooth = savgol_filter(y6, window, polyorder)

        peaks2, pInfo2 = find_peaks(-y2Smooth[cut:-cut], width=pWidth, height=pHeigth, prominence=pProminence)
        peaks4, pInfo4 = find_peaks(y4Smooth[cut:-cut], width=pWidth, height=pHeigth, prominence=pProminence)
        peaks6, pInfo6 = find_peaks(-y6Smooth[cut:-cut], width=pWidth, height=pHeigth, prominence=pProminence)
        
        realPeaks2 = []
        realPeaks4 = []
        realPeaks6 = []
        for i in peaks2:
            realPeaks2.append(round(x2[i], 1))
        for i in peaks4:
            realPeaks4.append(round(x4[i], 1))
        for i in peaks6:
            realPeaks6.append(round(x6[i], 1))
        print(f"    Found {len(peaks2):>2} peaks at first heating curve.  (", end="")
        print(*realPeaks2, sep=", ", end=")\n")
        print(f"    Found {len(peaks6):>2} peaks at second heating curve. (", end="")
        print(*realPeaks6, sep=", ", end=")\n")
        print(f"    Found {len(peaks4):>2} peaks at cooling curve.        (", end="")
        print(*realPeaks4, sep=", ", end=")\n")

        sns.set_theme()
        sns.set_style("whitegrid")

        plt.plot(x4, y4Smooth, "r", label="Cooling")
        plt.plot(x6, y6Smooth, "b", label="Second heating")
        plt.plot(x2, y2Smooth, "k", label="FIrst heating")

        plt.plot(x4[peaks4+cut], y4Smooth[peaks4+cut],  "xr")
        plt.plot(x6[peaks6+cut], y6Smooth[peaks6+cut],  "xb")
        plt.plot(x2[peaks2+cut], y2Smooth[peaks2+cut],  "xk")

        for n, i in enumerate(peaks4+cut):
            plt.annotate(round(x4[i], 1), (x4[i], y4Smooth[i]), xytext=(5,5), textcoords = "offset points")
        for n, i in enumerate(peaks6+cut):
            plt.annotate(round(x6[i], 1), (x6[i], y6Smooth[i]), xytext=(-15,-15), textcoords = "offset points")
        for n, i in enumerate(peaks2+cut):
            plt.annotate(round(x2[i], 1), (x2[i], y2Smooth[i]), xytext=(-15,-15), textcoords = "offset points")

        plt.title(name, fontweight="bold")
        plt.xlabel("Temperature [°C]")
        plt.ylabel("Heat flow [W/g]")
        plt.xlim(xMin, xMax)
        plt.yticks(color="None", fontsize=0)
        plt.legend(loc="upper right")
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(f"{os.path.join(path, name)}.png", dpi=300)
        plt.close()

        peaks.append([name, realPeaks2, realPeaks6, realPeaks4])
        t2 = time()
        print(f"File {name} was saved to {path}.")
        print(f"This loop took {round(t2 - t1, 2)} seconds.\n")
    except:
        print(f"Couldn't properly read the file {name}. Make sure it is exported correctly.\n")

print("All images are saved. Creating excel file with peak values.")

now = datetime.now().strftime("%Y-%m-%d %H.%M")
wbName = "Peaks from " + now + ".xlsx"
wb = xlsxwriter.Workbook(os.path.join(path, wbName))
ws = wb.add_worksheet()

cfTop = wb.add_format({"bottom":True, "align":"center"})
cf = wb.add_format({"align":"center"})
ws.set_column('A:A', 5)
ws.set_column('B:D', 25)
ws.write(0, 0, "n", cfTop)
ws.write(0, 1, "TM1", cfTop)
ws.write(0, 2, "TM2", cfTop)
ws.write(0, 3, "TC", cfTop)

for i in range(0, len(peaks)):
    name = peaks[i][0]
    tm1 = "   ".join(str(i) for i in peaks[i][1])
    tm2 = "   ".join(str(i) for i in peaks[i][2])
    tc = "   ".join(str(i) for i in peaks[i][3])
    if not tm1:
        tm1 = "Ø"
    if not tm2:
        tm2 = "Ø"
    if not tc:
        tc = "Ø"
    ws.write(i+1, 0, name, cf)
    ws.write(i+1, 1, tm1, cf)
    ws.write(i+1, 2, tm2, cf)
    ws.write(i+1, 3, tc, cf)

wb.close()
tf = time()
print(f"Excel file \"{wbName}\" is saved in {path}")
print(f"Total execution time is {round(tf - t0, 2)} seconds.\n")
os.startfile(path)