import os
import numpy as np
from scipy import sparse
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.sparse.linalg import spsolve
from matplotlib.animation import FuncAnimation
from tkinter.filedialog import askopenfilename

# Trying out animation, most functions are taken from pb_blend_analysis
# Which is where they are commented as well


def align(file, format):
    if format == "asc":
        x, y = make_XY_asc(file)
    else:
        x_too_shifted, y = make_XY_itx(file)
        x = [k - 2 for k in x_too_shifted]
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


def make_air(y):
    y_air = np.linspace(y[0], y[-1], num=len(y))
    while True:
        difs = []
        for i in range(0, len(y)):
            dif = y[i] - y_air[i]
            difs.append(dif)
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
    y_iters = []
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
    w = np.ones(L)
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
        y_iters.append(z)
    return z, y_iters


def animate(i):
    ax.clear()
    ax.plot(x, y_no_air, "k-", label="Original data", alpha=0.5)
    for j in range(0, len(y_iterations)):
        ax.plot(x, y_iterations[j], "c-", alpha=0.05 * (j + 1))
    ax.plot(x, y_iterations[i], "r-", label=f"Iteration {i + 1:<3}")
    ax.set_title(
        f"{name}\nAsymmetric Least Squares Smoothing by P. Eilers and H. Boelens"
    )
    ax.legend(loc="upper left")
    ax.set_xlim(5, 30)
    ax.set_ylim(0, max_y)


file = askopenfilename(
    title="Select the ITX or ASC file with RTG data.",
    filetypes=[("RTG data files", ".itx"), ("RTG data files", ".asc")],
)
file_name = os.path.split(file)[1]
file_split = file_name.split(" ")
name_split = file_split[1:-6]
code = file_split[0]
name = " ".join(str(x) for x in name_split)
name += " %"
filetype = file[-3:].lower()
x, y = align(file, filetype)
max_y = max(y) + 1000
y_no_air = make_air(y)
y_base, y_iterations = baseline_als(y_no_air, 10000, 0.0001, 15)

fig, ax = plt.subplots(1, 1)


anim = FuncAnimation(fig, animate, frames=len(y_iterations), interval=150, repeat=0)
mng = plt.get_current_fig_manager()
mng.window.state("zoomed")
plt.show()
# anim.save(filename="test.gif", dpi=300)
plt.close()
