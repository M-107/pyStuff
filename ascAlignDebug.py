import tkinter as tk
import seaborn as sns
from scipy.signal import find_peaks
from matplotlib import pyplot as plt 
from tkinter.filedialog import askopenfilenames

# Same thing as ascAlign, but also saves pictures displaying how the correction was done
# Significantly slower, but good to check if the corrections are... correct

# For testing during writing, using a file I know for sure is shifted
# When not testing, just ask for asc files
testing = 0
if testing == 0:
    root = tk.Tk()
    root.withdraw()
    files = askopenfilenames(title="Select the ASC files with RTG data.", filetypes=[("ASC files", ".asc")])
if testing == 1:
    files = [r"C:\[path to some test file].asc"]

for iNum, i in enumerate(files, 1):
    # Get the lines from each file apart from the last empty one
    lines = []
    with open(i, "r") as f:
        for line in f:
            y = line.split()
            lines.append(y)
    lines = lines[:-1]
    # The numbers are in mathematical format, convert that to something workable-with
    for j in lines:
        number = float(j[0][:-6])
        exponent = int(j[0][-1])
        newNumber = number * 10 ** exponent
        j[0] = newNumber
        j[1] = int(j[1])
    # The actuall X and Y values in float and int form
    x = [x[0] for x in lines]
    y = [x[1] for x in lines]
    # Finding the peaks onyl in the first third of the data
    # The measurements go from 0 to 35 2-theta, so even big shifts shouldn't be further away
    peaks, pInfo = find_peaks(y[:int(len(y)*1/3)], width = 5, height = 1000, prominence = 200)    
    lastDif = 10
    closest = 0
    # Find how close each peak is from 12 and remember the closest one
    for p in peaks:
        dif = 12-x[p]
        if abs(dif) < lastDif:
            closest = dif
        lastDif = dif
    # Add the distance of the cloest peak to 12 to the whole dataset
    xNew = [x+closest for x in x]
    newLines = []
    # Convert the edited X values and Y values back into the asc number format
    for m in range(0, len(xNew)):
        sciForm = "{:e}".format(xNew[m])
        num = f"{sciForm[:-4].ljust(16, '0')}"
        exp = f"E+00{sciForm[-2:]}"
        newLines.append(f" {num}{exp}  {y[m]}")  
    # Overwrite the original file  
    f = open(i, "w+")
    for n in newLines:
        f.write(f"{n}\n")
    f.close()
    # Display how much the correction was
    print(f"File {iNum:>3}/{len(files):>3} was corrected by {round(closest, 2):.2f}")
    # Basic plot setup, mostly self-explanatory
    sns.set_theme()
    sns.set_style("whitegrid")
    # Plotting bot the original and corrected data
    plt.plot(x, y, "k")
    plt.plot(xNew, y, "g")
    # Also plotting a line at 12, for clarity sake
    plt.plot([12,12],[min(y),max(y)],"b")
    # Show all peaks, one of them shoul be at the 12 line
    for e, k in enumerate(peaks):
        plt.plot(x[peaks[e]], y[peaks[e]], "xr")
    plt.xlim(min(x), max(x))
    plt.ylim(min(y), max(y))
    # Just show the graph during testing, save it next to the edited files during regular work
    if testing == 1:
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
        plt.show()
    if testing == 0:
        plt.gcf().set_size_inches(16, 9)
        image = f"{i[:-3]}png"
        plt.savefig(image, dpi=300)
        plt.close()
