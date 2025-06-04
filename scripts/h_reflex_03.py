import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
from matplotlib.backend_bases import MouseButton

from matplotlib.widgets import EllipseSelector, RectangleSelector

from participants import participants_dict

## global variables
ax=[]
selectors=[]

###############
def main(args):
    global ax

    ## participant number
    id = int(args[1])

    ## folder data location
    path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    filename = id_p['filename']
    ch_emg   = id_p['ch_mea']
    ch_sync  = id_p['ch_sync']
    seg_stim = id_p['stim_hm']
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

    n_rows = len(seg_stim)
    n_cols = 1

    # fig = plt.figure(sharex=True)
    fig, ax = plt.subplots(n_rows, n_cols, sharex=True, figsize=(10*n_cols, 5*n_rows))
    ax = ax.flat

    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    
    idx=0

    for i, t0 in enumerate(df_sel.iloc[:,ch_time]):
        if i in seg_stim:
            df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]
            ## time axis
            t = np.linspace(-0.02, 0.08, len(df_seg))
            ## plot emg segment at each subplot
            ax[idx].plot(t, df_seg.iloc[:,ch_emg])
            ax[idx].grid(color = 'green', linestyle = '--', linewidth = 0.2)
            ax[idx].set_title(f"stim: {i}")

            selectors.append(RectangleSelector(
            ax[idx], select_callback,
            useblit=True,
            button=[1, 3],  # disable middle button
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True))

            print (f"ax: {ax[idx]}, {type(ax[idx])}")
            idx+=1
        
        else:
            pass

    fig.suptitle(f"{channelsNames[ch_emg]}")

    fig.canvas.mpl_connect('axes_enter_event', on_enter_axes)

    plt.show()

    return 0

def select_callback(eclick, erelease):
    """
    Callback for line selection.

    *eclick* and *erelease* are the press and release events.
    """
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    print(f"({x1:3.3f}, {y1:3.1f}) --> ({x2:3.3f}, {y2:3.1f})")
    print(f"The buttons you used were: {eclick.button} {erelease.button}")


def on_enter_axes(event):
    
    ax_index = np.argwhere(event.inaxes == ax)
    print(f"ax_index: {ax_index[0][0]}")
  


##########################
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
