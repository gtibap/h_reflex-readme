import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
from scipy.fftpack import fft
import pandas as pd
from tkinter import *
from tkinter import filedialog
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import RectangleSelector
import matplotlib.widgets as mwidgets

from h_reflex_classes import StimulationResponses

## global variables 
window = []
label_file_explorer = []
filename = []
df = []
df_sel = []
ch_time = 0
ch_emg_list = [1,]
ch_sync = 2
channelsNames = []
fig_seg = []
fig_mea = []
ax_seg = []
ax_mea = []
ax_index = []
selectors=[]
emg_list=[]
stim_list=[]
obj_list=[]
tmin=0
tmax=0
samplingRate = 1

##########################
# Function for opening the 
# file explorer window
def browseFiles():
    global filename

    # filename = filedialog.askopenfilename(initialdir = "../", title = "Select a File", filetypes =(("mat files", "*.mat"), ("all files", "*.*")))
    filename = filedialog.askopenfilename(initialdir = "../../data/h_reflex_Karim/", title = "Select a File", filetypes =[("mat files", "*.mat")])

    file_list = filename.split('/')

    ## name of the selected file is printed
    label_file_explorer.configure(text=file_list[-1])

    open_file(file_list[-1])
    signal_segmentation(file_list[-1])

    plt.show()

    return 0

######################
def closeWindows():
    global obj_list

    plt.close('all')
    obj_list = []
    
    return 0

####################
def gui_filename():
    global window, label_file_explorer

    # Create the root window
    window = Tk()
    
    # Set window title
    window.title('File Explorer')
    
    # Set window size
    window.geometry("350x300")
    
    #Set window background color
    window.config(background = "white")
    
    # Create a File Explorer label
    label_file_explorer = Label(window, text = "select a matlab (legacy) file", width = 40, height = 2, fg = "blue")
    
        
    button_explore = Button(window, text = "Browse Files", command = browseFiles) 

    button_closeWin = Button(window, text = "Close all windows", command = closeWindows) 
    
    button_exit = Button(window, text = "Exit", command = exit) 
    
    # Grid method is chosen for placing
    # the widgets at respective positions 
    # in a table like structure by
    # specifying rows and columns
    label_file_explorer.grid(column = 1, row = 1)
    
    button_explore.grid(column = 1, row = 2)

    button_closeWin.grid(column = 1, row = 3)
    
    button_exit.grid(column = 1,row = 4)
    
    # Let the window wait for any events
    window.mainloop()

    return 0

##########################
def open_file(name_title):
    global df, channelsNames, ch_sync, samplingRate

    mat = sio.loadmat(filename)
    # print(f"mat:\n{mat}")
    samplingRate = mat['samplingRate'][0,0]
    print(f"samplingRate: {samplingRate}")

    ## get number of channels
    noChans = mat['noChans'][0,0]+1

    print(f"noChans: {noChans}")
    ch_sync = noChans-1

    ## variables initialization
    channels = np.empty((noChans, 0)).tolist()
    channelsNames = np.empty((noChans, 0)).tolist()
    df = pd.DataFrame()

    ## read raw data (channels) and channels names
    for i in np.arange(noChans):
        channels[i] = mat['Data'][0,i].flatten()
        channelsNames[i] = mat['channelNames'][0][i][0]
        ## dataframe of raw data
        df[channelsNames[i]] = channels[i]

    ## data visualization
    fig, ax = plt.subplots((noChans-1), 1, sharex=True,)
    if noChans > 2:
        ax = ax.flat
    else:
        ax = [ax]

    # for i in np.arange(noChans-1):
    #     ax[i].plot(channels[0], channels[i+1])
    #     ax[i].set_title(f"{i+1} - {channelsNames[i+1]}")
    
    ## emg signal filtering
    y = filter_emg(channels[1])

    grad_y = np.abs(np.gradient(y))

    ax[0].plot(channels[0], channels[1])
    ax[0].set_title(f"original emg signal")
    ax[0].grid(color = 'green', linestyle = '--', linewidth = 0.2)

    ax[1].plot(channels[0], channels[-1])
    ax[1].set_title(f"Sync stimulation")
    ax[1].grid(color = 'green', linestyle = '--', linewidth = 0.2)

    fig.suptitle(name_title, fontsize=16)

    return 0

####################################
# def butter_lowpass_sos(cutoff, fs, order=3):
    # return butter(order, cutoff, fs=fs, btype='low', analog=False, output='sos')

def filter_emg(data):
    # Filter requirements.
    order = 5
    cutoff = 450.0  # desired cutoff frequency of the filter, Hz
    fs = samplingRate    # sample rate, Hz
    print(f"fs: {fs}")
    # sos = butter_lowpass_sos(cutoff, fs, order=order)
    sos = signal.butter(order, cutoff, fs=fs, btype='low', analog=False, output='sos')
    # y = lfilter(b, a, data)
    y = signal.sosfiltfilt(sos, data)
    return y

####################################
def signal_segmentation(name_title):
    global df_sel, fig_seg, ax_seg, stim_list, obj_list

    ## sync greater than zero -> stimulation (sync signal values: min=0, max=1)
    df_sync = df[df.iloc[:,ch_sync]>0.5]

    ## to identify the initial sample of each stimulation
    ## we apply the difference between adjacent values
    df_diff = df_sync.diff()

    ## if the difference in time is greater than 0.05 s, means the beginning of a new stimulation pulse
    ## because time between stimulations is bigger than 0.05 s (usually 10 s between two consecutive stimulations)
    ## the second condition is to identify NaN values 
    ## (the first difference is NaN but corresponds to the begining of the first stimulation pulse)
    df_stm = df_diff[ (df_diff.iloc[:,ch_time]>0.05) | (df_diff.iloc[:,ch_time]!=df_diff.iloc[:,ch_time]) ]

    n_pulses = len(df_stm.index)

    ## from the original dataframe we extract rows that correspond with the begining of each stimulation pulse
    ## (using the indexes from df_stm) 
    df_sel = df.iloc[df_stm.index]

    n_rows = int(np.ceil(np.sqrt(n_pulses)))
    n_cols = int(np.ceil(n_pulses/n_rows))

    ## channel number in the list, usually ch_emg = 1
    ch_emg = ch_emg_list[0]

    fig, ax = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, figsize=(3*n_cols, 2*n_rows))
    ax = ax.flat

    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    for i, t0 in enumerate(df_sel.iloc[:,ch_time]):
        # t0 is the time zero (t=0) of each stimulation
        df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]

        ## replace time values to the same range (-0.02, 0.08)
        df_seg.iloc[:,ch_time] = df_seg.iloc[:,ch_time].to_numpy() - t0

        ## create an object of class StimulationResponses for each emg stimulation responses
        obj_list.append(StimulationResponses(df_seg, i))

        ## plot emg segment at each subplot
        ax[i].plot(df_seg.iloc[:,ch_time], df_seg.iloc[:,ch_emg])
        ax[i].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[i].set_title(f"stim: {i}")
    fig.suptitle(f"{name_title}\n{channelsNames[ch_emg]}", fontsize=16)

    # for obj in obj_list:
    #     obj.myfunc()

    ax_seg = ax
    fig_seg = fig
    
    fig_seg.canvas.mpl_connect('button_press_event', on_click)

    return 0

#################################
def plot_vpp(mwave, hreflex, ax):
    ax[0].plot(mwave)
    ax[0].set_title("M wave max amplitude (peak to peak) per stimulation")
    ax[0].set_ylabel("Amplitude [uV]")
    ax[0].grid(color='g', linestyle='--', linewidth=0.2)

    ax[1].plot(hreflex)
    ax[1].set_title("H-reflex max amplitude (peak to peak) per stimulation")
    ax[1].set_ylabel("Amplitude [uV]")
    ax[1].set_xlabel("stimulation number")
    ax[1].grid(color='g', linestyle='--', linewidth=0.2)

    return ax

##################################
def get_vpp(obj, lim_inf, lim_sup):

    df = obj.get_df()
    # print(f"get df: {df}")

    ch_emg = ch_emg_list[0]

    df_emg = df[(df.iloc[:,ch_time]>=lim_inf) & (df.iloc[:,ch_time]<=lim_sup)]
    # print(f"df_seg:\n{df_seg}")

    id_max = df_emg.iloc[:,ch_emg].idxmax()
    id_min = df_emg.iloc[:,ch_emg].idxmin()

    df_max = df_emg[df_emg.index==id_max]
    df_min = df_emg[df_emg.index==id_min]

    vmax = df_max.iloc[0,ch_emg]
    vmin = df_min.iloc[0,ch_emg]
    vpp  = vmax - vmin
    
    return vpp, vmin, vmax


###################
def on_click(event):
    global ax_index

    ax_copy = np.copy(ax_seg)

    # print(f"onclick event.inaxes: {event.inaxes}")
    if event.button is MouseButton.RIGHT:
        print(f"button right")
        print(f"event.inaxes: {event.inaxes}")
        ## is the mouse over any subplot?
        if event.inaxes in ax_copy:
            ## which subplot?
            ax_index = np.argwhere(event.inaxes == ax_copy)[0][0]
            ## subplot index
            print(f"selected ax: {ax_index}")
            ## open a new window with the signals of the selected subplot
            signal_measurements(ax_index)
        else:
            pass
            # print(f"event.inaxes out of ax")
    else:
        pass
        # print(f"other button")

    return 0

####################################
def signal_measurements(ax_index):
    global fig_mea, ax_mea, emg_list, selectors

    ## close previous figure
    if type(fig_mea) != type([]):
        plt.close(fig_mea)
    else:
        pass
    
    ## creates a figure to plot the selected stimulation responses 
    n_rows = 1
    n_cols = 1
    fig, ax = plt.subplots(n_rows, n_cols, sharex=True, figsize=(10*n_cols, 5*n_rows))
    
    ch_emg = ch_emg_list[0]

    emg_list = []
    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    idx=0

    for i, t0 in enumerate(df_sel.iloc[:,ch_time]):
        if i == ax_index:
            df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]
            ## time, emg, and sync data from selected stimulations
            df_seg.iloc[:,ch_time] = df_seg.iloc[:,ch_time].to_numpy() - t0
            ## list of emg segments
            emg_list.append(df_seg)
            ## time axis
            t = df_seg.iloc[:,ch_time].to_numpy()
            ## plot emg segment at each subplot
            ax.plot(t, df_seg.iloc[:,ch_emg])
            ax.grid(color = 'green', linestyle = '--', linewidth = 0.2)
            ax.set_title(f"stim: {i}")

            span = mwidgets.SpanSelector(ax, onselect, 'horizontal', interactive=True, useblit=True, props=dict(facecolor='blue', alpha=0.2))
            selectors.append(span)

            # print (f"ax: {ax}, {type(ax)}")
            idx+=1

            fig_mea = fig
            ax_mea = ax
        
        else:
            pass

    fig_mea.suptitle(f"{channelsNames[ch_emg]}")
    plt.show()

    # fig_mea.canvas.mpl_connect('button_press_event', on_click)
    fig_mea.canvas.mpl_connect('key_press_event', on_press)


    return 0

###########################
def onselect(vmin, vmax):
    global tmin, tmax
    print(vmin, vmax)

    tmin = vmin
    tmax = vmax

    return 0


#########################
def on_press(event):
    global ax_seg, fig_seg, tmin, tmax
    # print('press', event.key)
    sys.stdout.flush()

    df_emg = emg_list[0]
    ax = [ax_mea]
    ax_sel = 0
    ch_emg = ch_emg_list[0]

    x1 = tmin
    x2 = tmax

    fig = fig_mea

    ## measuring amplitude peak to peak
    if event.key == 'a':
        
        ax_mea.cla()

        ## plot emg segment at each subplot
        t = df_emg.iloc[:,ch_time].to_numpy()
        ax[ax_sel].plot(t, df_emg.iloc[:,ch_emg])
        ax[ax_sel].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[ax_sel].set_title(f"stim: {ax_index}")

        ###################
        ## peak to peak value between x1 >= t <= x2
        vpp, vmin, vmax = get_vpp(obj_list[ax_index], tmin, tmax)
        # df_emg = df_emg[(df_emg.iloc[:,ch_time]>=x1) & (df_emg.iloc[:,ch_time]<=x2)]
        
        # id_max = df_emg.iloc[:,ch_emg].idxmax()
        # id_min = df_emg.iloc[:,ch_emg].idxmin()

        # df_max = df_emg[df_emg.index==id_max]
        # df_min = df_emg[df_emg.index==id_min]

        # vpp = df_max.iloc[0,ch_emg] - df_min.iloc[0,ch_emg]
        print(f"Vpp: {vpp:3.2f} uV")
        ## peak to peak value between x1 >= t <= x2

        ax[ax_sel].axhline(y=vmin, linestyle="--", color='tab:purple')
        ax[ax_sel].axhline(y=vmax, linestyle="--", color='tab:purple')

        ####################
        x_a = x2 + 0.01
        y_a = vmin + (vpp)/3

        bbox = dict(boxstyle="round", fc="0.8")
        ax[ax_sel].annotate(f"Vpp={vpp:3.1f} uV", xy=(x_a, y_a), xytext=(x_a, y_a),fontsize=16, bbox=bbox,)

        fig.canvas.draw()

    ## measuring latency (delta time)
    elif event.key == 't':
        
        ax[ax_sel].cla()

        df_emg = emg_list[ax_sel]
        ## plot emg segment at each subplot
        t = df_emg.iloc[:,ch_time].to_numpy()
        ax[ax_sel].plot(t, df_emg.iloc[:,ch_emg])
        ax[ax_sel].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[ax_sel].set_title(f"stim: {ax_index}")

        df_emg = df_emg[(df_emg.iloc[:,ch_time]>=x1) & (df_emg.iloc[:,ch_time]<=x2)]
        
        id_max = df_emg.iloc[:,ch_time].idxmax()
        id_min = df_emg.iloc[:,ch_time].idxmin()

        df_max = df_emg[df_emg.index==id_max]
        df_min = df_emg[df_emg.index==id_min]

        delta_t = df_max.iloc[0,ch_time] - df_min.iloc[0,ch_time]
        print(f"latency: {delta_t:5.4} s")

        ax[ax_sel].axvline(x=df_min.iloc[0,ch_time], linestyle="--", color='tab:orange')
        ax[ax_sel].axvline(x=df_max.iloc[0,ch_time], linestyle="--", color='tab:orange')

        # tmax = df_emg.iloc[:,ch_time].max()
        # tmin = df_emg.iloc[:,ch_time].min()
        # delta_t = tmax-tmin

        x_a = x2 + 0.01
        y_a = 0
        # y_a = y1 + (y2-y1)/10


        bbox = dict(boxstyle="round", fc="0.8")
        ax[ax_sel].annotate(f"t ={delta_t:4.3f} s", xy=(x_a, y_a), xytext=(x_a, y_a),fontsize=16, bbox=bbox,)

        fig.canvas.draw()
    
    ## measuring max. amplitude stimulation voltage
    elif event.key == 'b':

        ## amplitude peak to peak
        print(f"peak stimulation voltage: ")
        ax[ax_sel].cla()

        df_emg = emg_list[ax_sel]

        ## plot emg segment at each subplot
        t = df_emg.iloc[:,ch_time].to_numpy()
        ax[ax_sel].plot(t, df_emg.iloc[:,ch_emg])
        ax[ax_sel].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[ax_sel].set_title(f"stim: {ax_index}")


        df_emg = df_emg[(df_emg.iloc[:,ch_time]>=x1) & (df_emg.iloc[:,ch_time]<=x2)]
        id_max = df_emg.iloc[:,ch_emg].idxmax()
        id_min = df_emg.iloc[:,ch_emg].idxmin()

        df_max = df_emg[df_emg.index==id_max]
        df_min = df_emg[df_emg.index==id_min]

        v_stim = np.max([np.abs(df_max.iloc[0,ch_emg]), np.abs(df_min.iloc[0,ch_emg])])
        print(f"v_stim: {v_stim:3.2f} uV")

        ax[ax_sel].axhline(y=0, linestyle="--", color='tab:purple')

        if np.abs(df_max.iloc[0,ch_emg]) > np.abs(df_min.iloc[0,ch_emg]):
            ax[ax_sel].axhline(y=df_max.iloc[0,ch_emg], linestyle="--", color='tab:purple')
        else:
            ax[ax_sel].axhline(y=df_min.iloc[0,ch_emg], linestyle="--", color='tab:purple')

        x_a = x2 + 0.01
        y_a = df_min.iloc[0,ch_emg] + (v_stim)/3

        bbox = dict(boxstyle="round", fc="0.8")
        ax[ax_sel].annotate(f"V_stim={v_stim:3.1f} uV", xy=(x_a, y_a), xytext=(x_a, y_a),fontsize=16, bbox=bbox,)

        fig.canvas.draw()


    elif event.key == 'c':

        ax[ax_sel].cla()
        df_emg = emg_list[ax_sel]
        ## plot emg segment at each subplot
        t = df_emg.iloc[:,ch_time].to_numpy()
        ax[ax_sel].plot(t, df_emg.iloc[:,ch_emg])
        ax[ax_sel].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[ax_sel].set_title(f"stim: {ax_index}")

        fig.canvas.draw()

    elif event.key == 'm':
        print(f"\npeak to peak voltages:\n")
        
        vpp_list=[]
        for i, obj in enumerate(obj_list):
            vpp, vmin, vmax = get_vpp(obj, tmin, tmax)
            updating_plot(obj,vmin,vmax,ax_seg[i])
            print(f"{vpp}")
            vpp_list.append(vpp)
        
        print(f"\n")

        fig_local, ax_local = plt.subplots(1,1)
        ax_local.plot(vpp_list)
        plt.show()

        fig_seg.canvas.draw()


    else:
        pass

    return 0

def updating_plot(obj,vmin,vmax,ax):

    ax.cla()
    df_seg = obj.get_df()
    ch_emg = ch_emg_list[0]

    ax.plot(df_seg.iloc[:,ch_time], df_seg.iloc[:,ch_emg])

    ax.axhline(y=vmin, linestyle="--", color='tab:purple')
    ax.axhline(y=vmax, linestyle="--", color='tab:purple')

    ax.grid(color = 'green', linestyle = '--', linewidth = 0.2)

    # ax.set_title(f"stim: {i}")
    # fig.suptitle(f"{name_title}\n{channelsNames[ch_emg]}", fontsize=16)

    return 0


####################
def main(args):


    ## graphical user interface
    gui_filename()

    

    ## participant number
    # id = int(args[1])
    # id = 1
    ## folder data location
    # path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    # id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    # filename = id_p['filename']

    ## load h-reflex raw data
    # mat = sio.loadmat(path+filename)
    # mat = sio.loadmat(filename)
    # # print(f"mat:\n{mat}")

    # ## get number of channels
    # noChans = mat['noChans'][0,0]+1

    # ## variables initialization
    # channels = np.empty((noChans, 0)).tolist()
    # channelsNames = np.empty((noChans, 0)).tolist()

    # ## read raw data (channels) and channels names
    # for i in np.arange(noChans):
    #     channels[i] = mat['Data'][0,i].flatten()
    #     channelsNames[i] = mat['channelNames'][0][i][0]

    # ## data visualization
    # fig, ax = plt.subplots((noChans-1), 1, sharex=True)
    # ax = ax.flat
    # for i in np.arange(noChans-1):
    #     ax[i].plot(channels[0], channels[i+1])
    #     ax[i].set_title(f"{i+1} - {channelsNames[i+1]}")

    # plt.show(block=True)

    return 0


## initialization
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
