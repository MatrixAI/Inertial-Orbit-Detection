from sine import sine
import numpy as np
import matplotlib.pyplot as plt 

def setup(lower_y, upper_y):

    # make matplotlib interactive
    # this just makes sure that plt.* functions will auto update the plot
    # that would be relevant to the imperative state-machine API
    plt.ion()

    # we're going to use the matplotlib object oriented API instead!
    
    # create a figure with only 1 axes in a 1 by 1 grid, the axes is what you should call the "plot"
    # the figure is the actual window, the axes represent the plot that contains axis objects
    fig, axes = plt.subplots(1, 1)
    
    # set the labels of the plot
    axes.set_xlabel('Time (s)')
    axes.set_ylabel('Acceleration (m/s^2)')
    
    # set the y limits of the plot
    axes.set_ylim(lower_y, upper_y)

    # initialise the zero, east and up curves on the plot
    return {
        "figure": fig, 
        "zero": {
            "curve": axes.plot([], [], 'c-')
        },
        "east": {
            "points": axes.plot([], [], 'r.'),
            "curve": axes.plot([], [], 'r-')
        },
        "up": {
            "points": axes.plot([], [], 'b.'),
            "curve": axes.plot([], [], 'b-')
        }
    }

def display(graph, norm_data_window, frequencies, wave_properties, time_delta_s):

    # roll the graph window
    plt.xlim(norm_data_window["time"][0], norm_data_window["time"][-1])

    graph["zero"]["curve"][0].set_xdata(norm_data_window["time"])
    graph["zero"]["curve"][0].set_ydata(norm_data_window["time"] * 0)

    graph["east"]["points"][0].set_xdata(norm_data_window['time'])
    graph["east"]["points"][0].set_ydata(norm_data_window['east'])

    graph["up"]["points"][0].set_xdata(norm_data_window['time'])
    graph["up"]["points"][0].set_ydata(norm_data_window['up'])

    # graph rendering is a matter of plotting coordinates and then "connecting the dots"
    # this means a straight line is drawn from each coordinate to the next coordinate
    # if you have irregularly spaced intervals and large intervals, the graph may not look nice
    # however our time values have been corrected to be regularly spaced, so it's all good!

    graph["east"]["curve"][0].set_xdata(norm_data_window['time'])
    graph["east"]["curve"][0].set_ydata( 
        sine(
            frequencies["east"], 
            norm_data_window['time'], 
            wave_properties["east"]["popt"][0], 
            wave_properties["east"]["popt"][1], 
            wave_properties["east"]["popt"][2]
        )
    )

    graph["up"]["curve"][0].set_xdata(norm_data_window['time'])
    graph["up"]["curve"][0].set_ydata( 
        sine(
            frequencies["up"], 
            norm_data_window['time'], 
            wave_properties["up"]["popt"][0], 
            wave_properties["up"]["popt"][1], 
            wave_properties["up"]["popt"][2]
        )
    )

    # repaint the graph with the new data and curve
    graph["figure"].canvas.draw()
    graph["figure"].canvas.flush_events()