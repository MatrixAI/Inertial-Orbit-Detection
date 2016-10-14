from sine import sine
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
    axes.set_ylabel('Accleration (m/s^2)')
    
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

def display(graph, norm_data_window, frequencies, wave_properties):

    # roll the graph window
    plt.xlim(norm_data_window["time"][0], norm_data_window["time"][-1])

    graph["zero"]["curve"].set_xdata(norm_data_window["time"])
    graph["zero"]["curve"].set_ydata(norm_data_window["time"] * 0)

    graph["east"]["points"].set_xdata(norm_data_window['time'])
    graph["east"]["points"].set_ydata(norm_data_window['east'])

    graph["up"]["points"].set_xdata(norm_data_window['time'])
    graph["up"]["points"].set_ydata(norm_data_window['up'])

    graph["east"]["curve"].set_xdata(norm_data_window['time'])
    graph["east"]["curve"].set_ydata( 
        sine(
            frequencies["east"], 
            norm_data_window['time'], 
            wave_properties["east"]["popt"][0], 
            wave_properties["east"]["popt"][1], 
            wave_properties["east"]["popt"][2]
        )
    )

    graph["up"]["curve"].set_xdata(norm_data_window['time'])
    graph["up"]["curve"].set_ydata( 
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