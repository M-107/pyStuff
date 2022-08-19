import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.stats import norm
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# Hardcoded, because this was a single use script
# and the results could most likely be achieved by a few clicks in any statistical sofware
# But where's the fun in that
names = ["PA6 2018", "PA6 2022", "PA6.6 2018", "PA6.6 2022"]
irradiation_dose = [0, 15, 33, 45, 66, 99, 132, 165, 195]
pa6_density_2018 = [1.134, 1.133, 1.135, 1.137, 1.134, 1.134, 1.136, 1.136, 1.136]
pa6_density_2022 = [1.141, 1.144, 1.145, 1.142, 1.143, 1.142, 1.142, 1.145, 1.143]
pa66_density_2018 = [1.143, 1.144, 1.142, 1.143, 1.142, 1.141, 1.140, 1.139, 1.140]
pa66_density_2022 = [1.143, 1.144, 1.144, 1.143, 1.144, 1.144, 1.143, 1.144, 1.144]
density_lists = [pa6_density_2018, pa6_density_2022, pa66_density_2018, pa66_density_2022]
density_group_lists = [["PA6", pa6_density_2018, pa6_density_2022], ["PA6.6", pa66_density_2018, pa66_density_2022]]

# Was kinda figuring out what I'm even doing while writing it
# So this is just for quick switching between just showing the graphs and saving them
def plotting(testing, name):
    if testing == 0:
        plt.gcf().set_size_inches(16, 9)
        plt.savefig(f"C:/Users/marti/Documents/_ŠKOLA/Stáž/LV/{name}.png")
        plt.close()
    else:
        plt.show()

# Make a scatter plot from a sinlge set of XY data
# For determining if the Y values have a measurable effect on the X values
# and if further X values could be predicted
def scatPlot(x, y, name, plotType):
    # Basic plot setup, mostly self explanatory
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    ax.set_title(name)
    x_name = "Irradiation dose [kGy]"
    y_name = f"Density [g/cm\N{SUPERSCRIPT THREE}]"
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    # Only show the x axis ticks that actually represent measurements
    ax.set_xticks(np.array(x))
    color1 = "palevioletred"
    color2 = "royalblue"

    # Not really using these values anywhere, but I might, so here they are
    slope, intercept, r, p, std_err = stats.linregress(x, y)
    r_text = f"Correlation coefficient: {round(r, 4)}"
    p_text = f"P-value for a hypothesis that the slope is zero: {round(p, 4)}"
    std_err_text = f"Standard error of the estimated slope: {str(std_err)[:5]} e{str(std_err)[-3:]}"
    ax.legend(title=f"{r_text}\n{p_text}\n{std_err_text}", loc="upper center")
    
    # Get the confidence bands around the linear regression line
    df = pd.DataFrame(list(zip(x, y)),columns =["dose", "density"])
    X = sm.add_constant(df["dose"].values)
    ols_model = sm.OLS(df["density"].values, X)
    est = ols_model.fit()
    y_pred = est.predict(X)
    x_pred = df.dose.values
    pred = est.get_prediction(X).summary_frame()
    
    # Color the actuall data ticks accoring to wheter they are inside or outside the confidence bands
    for i in range(0, len(x)):
        if pred['mean_ci_lower'][i] < y[i] < pred['mean_ci_upper'][i]:
            col = color2
        else:
            col = color1
        ax.scatter(x[i], y[i], c=col)
    
    # Plot the linear regression line, confidence bands are shows as an area (because it's nicer)
    ax.plot(x_pred, y_pred, color="black")
    ax.fill_between(x_pred, pred['mean_ci_lower'], pred['mean_ci_upper'], color='black', alpha=0.1)
    
    # As mentioned, save/show switch because of the constatn changes
    plotting(plotType, name)

# Make a plot comparing the probability densitiy distribution of two sets of X values
# For comparing wheter two sets of values are significantly different
def histPlot(x1, x2, name, plotType):
    # Basic setup
    sns.set_theme()
    sns.set_style("whitegrid")
    fig, ax = plt.subplots()
    color1 = "palevioletred"
    color2 = "royalblue"
    plt.title(name)
    x_name = f"Density [g/cm\N{SUPERSCRIPT THREE}]"
    y_name = "Probability density distribution"
    npx1 = np.array(x1)
    npx2 = np.array(x2)
    # This is the actually important part, making the PDD graphs
    # Rest is mostly styling
    sns.distplot(npx1, fit=norm, kde=False, hist=False, label="2018", ax=ax, fit_kws={"color":color1})
    sns.distplot(npx2, fit=norm, kde=False, hist=False, label="2022", ax=ax, fit_kws={"color":color2})
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    # No need for more decimals because of the measurement method
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    ax.set_ylim(0)
    
    # Finding info about the drawn histograms
    kdeline1, kdeline2 = ax.lines
    mean1, mean2 = npx1.mean(), npx2.mean()
    xs1, xs2 = kdeline1.get_xdata(), kdeline2.get_xdata()
    ys1, ys2 = kdeline1.get_ydata(), kdeline2.get_ydata()
    std1, std2 = npx1.std(), npx2.std()
    height1, height2 = np.interp(mean1, xs1, ys1), np.interp(mean2, xs2, ys2)
    
    # The legend uses data that was obtained from the drawn graphs, so it must be set up after drawing them
    L = ax.legend(loc="upper center")
    L.get_texts()[0].set_text(f"2018 Mean:{round(mean1, 3)} StDev: {round(std1, 6)}")
    L.get_texts()[1].set_text(f"2022 Mean:{round(mean2, 3)} StDev: {round(std2, 6)}")
    
    # Set only the relevant x ticks, make nice mean lines and fill below the histograms
    ax.set_xticks([mean1, mean2])
    ax.vlines(mean1, 0, height1, color=color1, ls=':')
    ax.vlines(mean2, 0, height2, color=color2, ls=':')
    ax.fill_between(xs1, 0, ys1, facecolor=color1, alpha=0.2)
    ax.fill_between(xs2, 0, ys2, facecolor=color2, alpha=0.2)
    
    # Again, saving/showing
    plotting(plotType, name)

# Determine wheter to just show or save the graps and interate through the two lists of stuff
# Not very elegant, but it is a one time use script as mentioned
# and it could easily be adjusted to work with outside data
justShow = 0
for i in range(0, len(names)):
    scatPlot(irradiation_dose, density_lists[i], names[i], justShow)
for i in range(0, len(density_group_lists)):
    histPlot(density_group_lists[i][1], density_group_lists[i][2], density_group_lists[i][0], justShow)
