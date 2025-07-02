import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
import pandas as pd
from tkinter import *
from tkinter import filedialog
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import RectangleSelector
import matplotlib.widgets as mwidgets

from participants import participants_dict

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
    plt.close('all')
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
    fig, ax = plt.subplots((noChans-1)+1, 1, sharex=True,)
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

    ax[1].plot(channels[0], y)
    ax[1].set_title(f"filtered emg signal")
    ax[1].grid(color = 'green', linestyle = '--', linewidth = 0.2)

    ax[2].plot(channels[0], grad_y)
    ax[2].set_title(f"gradient filtered emg signal")
    ax[2].grid(color = 'green', linestyle = '--', linewidth = 0.2)

    fig.suptitle(name_title, fontsize=16)

    return 0
    # plt.show()

####################################
# def butter_lowpass_sos(cutoff, fs, order=3):
    # return butter(order, cutoff, fs=fs, btype='low', analog=False, output='sos')

def filter_emg(data):
    # Filter requirements.
    order = 5
    cutoff = 400.0  # desired cutoff frequency of the filter, Hz
    fs = samplingRate    # sample rate, Hz
    print(f"fs: {fs}")
    # sos = butter_lowpass_sos(cutoff, fs, order=order)
    sos = signal.butter(order, cutoff, fs=fs, btype='low', analog=False, output='sos')
    # y = lfilter(b, a, data)
    y = signal.sosfiltfilt(sos, data)
    return y

####################################
def signal_segmentation(name_title):
    global df_sel, fig_seg, ax_seg, stim_list

    # print(f"df:\n{df.head()}")
    # print(f"ch_sync: {ch_sync}")
    ## sync greater than zero -> stimulation (sync signal values: min=0, max=1)
    df_sync = df[df.iloc[:,ch_sync]>0.5]
    # print(f"df_sync:\n{df_sync}")

    ## to identify the initial sample of each stimulation
    ## we apply the difference between adjacent values
    df_diff = df_sync.diff()
    # print(f"df_diff:\n{df_diff}")

    ## if the difference in time is greater than 0.02 s, means the beginning of an stimulation pulse
    ## because time between stimulations is bigger than 0.02 s (usually 10 s between two consecutive stimulations)
    ## the second condition is to identify NaN values 
    ## (the first difference is NaN but corresponds to the begining of the first stimulation pulse)
    df_stm = df_diff[ (df_diff.iloc[:,ch_time]>0.02) | (df_diff.iloc[:,ch_time]!=df_diff.iloc[:,ch_time]) ]
    # print(f"df_stm:\n{df_stm}")

    # print(f"df_stm indexes:\n{df_stm.index}")
    # print(f"number of pulses:\n{len(df_stm.index)}")

    n_pulses = len(df_stm.index)

    ## from the original dataframe we extract rows that correspond with the begining of each stimulation pulse
    ## (using the indexes from df_stm) 
    df_sel = df.iloc[df_stm.index]
    # print(f"df_sel:\n{df_sel}")

    n_rows = int(np.ceil(np.sqrt(n_pulses)))
    n_cols = int(np.ceil(n_pulses/n_rows))

    # for ch_emg in ch_emg_list:
    ch_emg = ch_emg_list[0]

    fig_vpp, ax_vpp = plt.subplots(2,1, sharex=True)

    fig, ax = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, figsize=(3*n_cols, 2*n_rows))
    ax = ax.flat

    ## list of segments, stimulation segments
    vpp_mwave_list = []
    vpp_hreflex_list = []
    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    for i, t0 in enumerate(df_sel.iloc[:,ch_time]):
        print(f"t0: {t0}")
        df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]

        ## replace time values
        df_seg.iloc[:,ch_time] = df_seg.iloc[:,ch_time].to_numpy() - t0
        # print(f"df seg:\m{df_seg}")
        # stim_list.append(df_seg)
       
        ## calculate peak to peak voltage of M-wave
        lim_inf=0.007
        lim_sup=0.02
        vpp_mwave_list.append(get_vpp_with_grad(df_seg, lim_inf, lim_sup))
        # vpp_mwave_list.append(get_vpp(df_seg, lim_inf, lim_sup))

        ## calculate peak to peak voltage of H-reflex
        lim_inf=0.025
        lim_sup=0.05
        vpp_hreflex_list.append(get_vpp(df_seg, lim_inf, lim_sup))
       
        # print(f"vpp mwave: {vpp_mwave}")
        # vpp_mwave_list.append(vpp_mwave)

        # vpp_hreflex = get_vpp_hreflex(df_seg)

        # print(f"df_seg:\n{df_seg}")
        ## time axis
        # t = np.linspace(-0.02, 0.08, len(df_seg))
        ## plot emg segment at each subplot
        ax[i].plot(df_seg.iloc[:,ch_time], df_seg.iloc[:,ch_emg])
        ax[i].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[i].set_title(f"stim: {i}")
    fig.suptitle(f"{name_title}\n{channelsNames[ch_emg]}", fontsize=16)



    ax_seg = ax
    fig_seg = fig

    ## function to plot h-reflex max values
    ax_vpp = plot_vpp(vpp_mwave_list, vpp_hreflex_list, ax_vpp)
    fig_vpp.suptitle(f"{name_title}", fontsize=12)
    
    
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
def get_vpp(df, lim_inf, lim_sup):

    # for ch_emg in ch_emg_list:
    ch_emg = ch_emg_list[0]

    df_emg = df[(df.iloc[:,ch_time]>=lim_inf) & (df.iloc[:,ch_time]<=lim_sup)]
    # print(f"df_seg:\n{df_seg}")

    id_max = df_emg.iloc[:,ch_emg].idxmax()
    id_min = df_emg.iloc[:,ch_emg].idxmin()

    df_max = df_emg[df_emg.index==id_max]
    df_min = df_emg[df_emg.index==id_min]

    vpp = df_max.iloc[0,ch_emg] - df_min.iloc[0,ch_emg]
    
    # emg_grad = np.gradient(df_seg.iloc[:,ch_emg].to_numpy())
    
    # df_a = pd.DataFrame()
    # df_a['time'] = df_seg.iloc[:,ch_time]
    # df_a['emg'] = df_seg.iloc[:,ch_emg]
    # df_a['grad'] = np.abs(emg_grad)
    # # print(f"df_a:\n{df_a}\n")


    # df_max = df_a[df_a['grad']==df_a['grad'].max()]
    # # print(f"df max:\n{df_max}\n")
    
    # t0 = df_max['time'].values[0]
    # # print(f"t0 = {t0}")

    # df_1 = df_a.loc[(df_a['time'] <= t0)]
    # df_2 = df_a.loc[(df_a['time'] >= t0)]
    # # print(f"df_1:\n{df_1}\n")
    # # print(f"df_2:\n{df_2}\n")

    # df_1_max = df_1.loc[ df_1['emg'].abs() == df_1['emg'].abs().max()]
    # df_2_max = df_2.loc[ df_2['emg'].abs() == df_2['emg'].abs().max()]
    # # print(f"df_1_max:\n{df_1_max}\n")
    # # print(f"df_2_max:\n{df_2_max}\n")

    # vpp = np.abs(df_2_max['emg'].values[0] - df_1_max['emg'].values[0])
    # # print(f"vpp: {vpp}")

    return vpp

##################################
def get_vpp_with_grad(df, lim_inf, lim_sup):

    # for ch_emg in ch_emg_list:
    ch_emg = ch_emg_list[0]

    # df_emg = df[(df.iloc[:,ch_time]>=lim_inf) & (df.iloc[:,ch_time]<=lim_sup)]
    # print(f"df_seg:\n{df_seg}")

    # id_max = df_emg.iloc[:,ch_emg].idxmax()
    # id_min = df_emg.iloc[:,ch_emg].idxmin()

    # df_max = df_emg[df_emg.index==id_max]
    # df_min = df_emg[df_emg.index==id_min]

    # vpp = df_max.iloc[0,ch_emg] - df_min.iloc[0,ch_emg]

     ## emg signal filtering
    emg_filtered = filter_emg(df.iloc[:,ch_emg].to_numpy())
    emg_gradient = np.abs(np.gradient(emg_filtered))
    
    # emg_grad = np.gradient(df_emg.iloc[:,ch_emg].to_numpy())
    
    df_emg = pd.DataFrame()
    df_emg['time'] = df.iloc[:,ch_time]
    df_emg['emg']  = df.iloc[:,ch_emg]
    df_emg['emg_filtered'] = emg_filtered
    df_emg['emg_gradient'] = emg_gradient
    # print(f"df_a:\n{df_a}\n")

    df_mwave = df_emg[(df_emg['time']>=lim_inf) & (df_emg['time']<=lim_sup)]

    df_max = df_mwave[df_mwave['emg_gradient']==df_mwave['emg_gradient'].max()]
    # print(f"df max:\n{df_max}\n")
    
    t0 = df_max['time'].values[0]
    # print(f"t0 = {t0}")

    # df_max = df_emg[df_emg['emg_gradient']==df_mwave['emg_gradient'].max()]

    ## look for the minimum values to the left and right of the gradient from the gradient's peak
    tp = 0.0025 ## in seconds 
    df_1 = df_emg[(df_emg['time'] >= (t0-tp)) & (df_emg['time'] < t0)]
    df_2 = df_emg[(df_emg['time'] > t0)       & (df_emg['time'] <= (t0+tp))]
    # print(f"df_1:\n{df_1}\n")
    # print(f"df_2:\n{df_2}\n")

    df_1_min = df_1[ (df_1['emg_gradient']) == (df_1['emg_gradient'].min())]
    df_2_min = df_2[ (df_2['emg_gradient']) == (df_2['emg_gradient'].min())]
    # print(f"df_1_max:\n{df_1_max}\n")
    # print(f"df_2_max:\n{df_2_max}\n")

    t_peak_1 = df_1_min['time'].values[0]
    t_peak_2 = df_2_min['time'].values[0]

    vp_1 = df_emg[(df_emg['time']==t_peak_1)]['emg_filtered'].values[0]
    vp_2 = df_emg[(df_emg['time']==t_peak_2)]['emg_filtered'].values[0]

    vpp = np.abs(vp_1 - vp_2)

    # vpp = np.abs(df_emg['emg_filtered'].values[0] - df_1_max['emg'].values[0])

    # vpp = np.abs(df_2_max['emg'].values[0] - df_1_max['emg'].values[0])
    # print(f"vpp: {vpp}")

    return vpp


###################
def on_click(event):
    global ax_index

    ax_copy = np.copy(ax_seg)

    # print(f"onclick event.inaxes: {event.inaxes}")
    if event.button is MouseButton.RIGHT:
        print(f"button right")
        print(f"event.inaxes: {event.inaxes}")
        if event.inaxes in ax_copy:
            ax_index = np.argwhere(event.inaxes == ax_copy)[0]
            print(f"selected ax: {ax_index}")
            signal_measurements(ax_index[0])
        else:
            pass
            # print(f"event.inaxes out of ax")
    else:
        pass
        # print(f"other button")

    return 0

####################################
def signal_measurements(ax_index):
    global fig_mea, ax_mea, emg_list

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


        df_emg = df_emg[(df_emg.iloc[:,ch_time]>=x1) & (df_emg.iloc[:,ch_time]<=x2)]
        
        id_max = df_emg.iloc[:,ch_emg].idxmax()
        id_min = df_emg.iloc[:,ch_emg].idxmin()

        df_max = df_emg[df_emg.index==id_max]
        df_min = df_emg[df_emg.index==id_min]

        vpp = df_max.iloc[0,ch_emg] - df_min.iloc[0,ch_emg]
        print(f"Vpp: {vpp:3.2f} uV")

        ax[ax_sel].axhline(y=df_max.iloc[0,ch_emg], linestyle="--", color='tab:purple')
        ax[ax_sel].axhline(y=df_min.iloc[0,ch_emg], linestyle="--", color='tab:purple')

        x_a = x2 + 0.01
        y_a = df_min.iloc[0,ch_emg] + (vpp)/3

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

    else:
        pass

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
