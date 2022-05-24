import os
import tkinter as tk
import seaborn as sns
from matplotlib import pyplot as plt 
from tkinter.filedialog import askopenfilenames

root = tk.Tk()
root.withdraw()
files = askopenfilenames(title="Select the ASC files with RTG data.", filetypes=[("ASC files", ".asc")])

def makeXY(file):
    lines = []
    with open(file, "r") as f:
        for line in f:
            y = line.split()
            lines.append(y)
    lines = lines[:-1]
    for j in lines:
        number = float(j[0][:-6])
        exponent = int(j[0][-1])
        newNumber = number * 10 ** exponent
        j[0] = newNumber
        j[1] = int(j[1])
    x = [x[0] for x in lines]
    y = [x[1] for x in lines]
    return x, y

def plotThree(x18, y18, x21, y21, x22, y22):
    sns.set_theme()
    sns.set_style("whitegrid")
    plt.plot(x18, y18, "k", label = "2018")
    plt.plot(x21, y21, "b", label = "2021")
    plt.plot(x22, y22, "r", label = "2022")
    plt.xlim(5, 30)
    plt.title(os.path.split(i)[1][:-9])
    plt.xlabel("2Θ")
    plt.ylabel("intensity")
    plt.legend(loc="upper right")
    plt.gcf().set_size_inches(16, 9)
    plt.savefig(f"{i[:-9]}.png", dpi=300)
    plt.close()

for iNum, i in enumerate(files, 1):
    print(f"Working on file {iNum} out of {len(files)}")
    if "2018" in i:
        x18, y18 = makeXY(i)
        i21 = i.replace("2018", "2021")
        i22 = i.replace("2018", "2022")
        x21, y21 = makeXY(i21)
        x22, y22 = makeXY(i22)
        plotThree(x18, y18, x21, y21, x22, y22)
