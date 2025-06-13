import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
from matplotlib.backend_bases import MouseButton

from participants import participants_dict

####################
## global variables
fig = []
ax  = []

###############
def main(args):
    global fig, ax

    ## participant number
    id = int(args[1])

    ## folder data location
    path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    filename    = id_p['filename']
    ch_emg_list = id_p['ch_emg']
    ch_sync     = id_p['ch_sync']
    ## id time channel is zero
    ch_time = 0

    ## load h-reflex raw data
    mat = sio.loadmat(path+filename)

    ## number of channels +1 to include time channel
    noChans = mat['noChans'][0,0]+1

    ## variables initialization
    channels = np.empty((noChans, 0)).tolist()
    channelsNames = np.empty((noChans, 0)).tolist()
    df = pd.DataFrame()

    ## raw data and channels names
    for i in np.arange(noChans):
        channels[i] = mat['Data'][0,i].flatten()
        channelsNames[i] = mat['channelNames'][0][i][0]
        ## dataframe of raw data
        df[channelsNames[i]] = channels[i]

    ## signals filtering (pass-band filter), is it required ?

    ## raw data segmentation
    ## taking the begining of each stimulation signal (sync > 0 ) as t0
    ## we extract segments of 0.1 s from (t0 - 0.02 s) to (t0 + 0.08 s)

    ## sync greater than zero -> stimulation (sync signal values: min=0, max=1)
    df_sync = df[df.iloc[:,ch_sync]>0.5]
    # print(f"df_sync:\n{df_sync}")

    ## to identify the initial sample of each stimulation
    ## we apply the difference between adjacent values
    df_diff = df_sync.diff()
    # print(f"df_diff:\n{df_diff}")

    ## if the difference in time is greater than 1 s, means the beginning of an stimulation pulse
    ## because time between stimulations is bigger than 1 s (usually 10 s between two consecutive stimulations)
    ## the second condition is to identify NaN values 
    ## (the first difference is NaN but corresponds to the begining of the first stimulation pulse)
    df_stm = df_diff[ (df_diff.iloc[:,ch_time]>1) | (df_diff.iloc[:,ch_time]!=df_diff.iloc[:,ch_time]) ]
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

    for ch_emg in ch_emg_list:
        fig, ax = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, figsize=(3*n_cols, 2*n_rows))
        ax = ax.flat
        ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
        ## iterate using time (column 0)
        for i, t0 in enumerate(df_sel.iloc[:,ch_time]):
            print(f"t0: {t0}")
            df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]
            # print(f"df_seg:\n{df_seg}")
            ## time axis
            t = np.linspace(-0.02, 0.08, len(df_seg))
            ## plot emg segment at each subplot
            ax[i].plot(t, df_seg.iloc[:,ch_emg])
            ax[i].grid(color = 'green', linestyle = '--', linewidth = 0.2)
            ax[i].set_title(f"stim: {i}")
        fig.suptitle(f"{channelsNames[ch_emg]}")

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()

    return 0

###################
def on_click(event):
    global ax_index

    ax_copy = np.copy(ax)

    # print(f"onclick event.inaxes: {event.inaxes}")
    if event.button is MouseButton.RIGHT:
        print(f"button right")
        print(f"event.inaxes: {event.inaxes}")
        if event.inaxes in ax_copy:
            ax_index = np.argwhere(event.inaxes == ax_copy)[0]
            print(f"selected ax: {ax_index}")
        else:
            print(f"event.inaxes out of ax")
    else:
        print(f"other button")

    return 0

##########################
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
