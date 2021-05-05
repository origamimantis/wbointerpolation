"""
Script to visualize the benchmark data for the WBO comparison
between Openeye AM1 and QCArchive values

Usage:
    visualize_benchmark_data.py
"""
# from danieljcabrera

# notes
# each pickle file should contain 
#     [ dataset name, benchmark data ], where benchmark data is
#         [ ( smiles, ([wbo method 0, wbo method 1], [torsion indices]) ) ]

# clone danieljcabrera/plotmol into the directory, and move plotmol/plotmol to plotmol




import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import plotmol

from bokeh.palettes import Category20b, Category20c
from bokeh.plotting import Figure, output_file, save, show
from plotmol.plotmol import default_tooltip_template
from scipy import stats


# TODO make this an argument or something
method0 = "QCArchive"
method1 = "Openeye AM1"
pkldir = "benchmark_results"


def read_data(dataset_file_name):
    """
    Reads the dictionary genereated by central_torsion_wbo.py
    """
    
    with open(f"{pkldir}/{dataset_file_name}.pkl", "rb") as file:
        print(dataset_file_name)
        return pickle.load(file)
        

def plot_all_interactive():
    benchmarks = {}
    colors = Category20b[20] + Category20c[20]

    for file in os.listdir(f"{pkldir}"):
        if ".pkl" in file:
            dataset_file_name = file[:-4]
            dataset_name, benchmark_data = read_data(dataset_file_name)
            dataset_file_name = dataset_name.replace(" ", "")
            
            benchmark_wbo_data = {}
            benchmark_wbo_data.update(benchmark_data)

            benchmarks[dataset_name] = benchmark_wbo_data
            
    # get axis bounds
    maxx = 0
    maxy = 0
    for benchmark_name, benchmark_data in benchmarks.items():
        wbo0 = []
        wbo1 = []
        for smiles, data in benchmark_data.items():
            wbo0.append(data[0][0]) #method0 wbo
            wbo1.append(data[0][1]) #method1 wbo

            mx = max(wbo0)
            my = max(wbo1)
            if mx > maxx: maxx = mx
            if my > maxy: maxy = my

    
    figure = Figure(
                tooltips = default_tooltip_template(),
                title = f"{method0} - {method1} WBO Benchmark",
                x_axis_label = method0,
                y_axis_label = method1,
                plot_width = 1600,
                plot_height = 800,
                x_range = [0, maxx*1.1],
                y_range = [0, maxy*1.1]
                )
                
    figure.line(x = [0,maxx*1.1], y = [0, maxy*1.1])
            
    color_index = 0
    
    for benchmark_name, benchmark_data in benchmarks.items():
        mols = {}
        wbo0 = []
        wbo1 = []
        print("BEANS", benchmark_name)
        if len(benchmark_data) > 0:
            for smiles, data in benchmark_data.items():
                mols[smiles] = data[1] #Torsion indices
                #mols[smiles] = data[0] #Torsion indices
                wbo0.append(data[0][0]) #method0 wbo
                wbo1.append(data[0][1]) #method1 wbo

            plotmol.scatter(figure,
                    x = wbo0,
                    y = wbo1,
                    smiles = mols,
                    marker = "o",
                    marker_size = 10,
                    marker_color = "black",
                    fill_color = colors[color_index],
                    legend_label = f"{benchmark_name} Benchmark ({len(benchmark_data)} mols)"
                    )
            color_index += 1
                
    figure.legend.location = "top_left"
    figure.legend.click_policy = "hide"
    figure.add_layout(figure.legend[0], "right")
   
    #show(figure)
    output_file(f"All_Datasets_interactive.html")
    save(figure)

def main():
    plot_all_interactive()


if __name__ == "__main__":
    main()
