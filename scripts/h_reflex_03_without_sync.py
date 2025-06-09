############################
## Measuring tool for H-Reflex analysis
## keyboard functions:
## key a: amplitude peak to peak value
## key b: amplitude peak from baseline (O V)
## key t: latency (time)
## key c: clean measurement values
##############################
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
from matplotlib.backend_bases import MouseButton

from matplotlib.widgets import EllipseSelector, RectangleSelector

from participants import participants_dict

## global variables
fig=[]
ax=[]
selectors=[]
emg_list=[]
seg_stim=[]
ch_time = 0
ch_emg = 1
ax_sel = 0
x1,y1,x2,y2 = 0,0,0,0

###############
def main(args):
    global fig, ax, ch_emg, seg_stim

    ## participant number
    id = int(args[1])

    ## folder data location
    path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    filename = id_p['filename']
    ch_emg   = id_p['ch_mea']
    # ch_sync  = id_p['ch_sync']
    seg_stim = id_p['stim_hm']
    ## id time channel is zero in the matlab (legacy) file format data

    ## load h-reflex raw data [matlab (legacy) file format]
    mat = sio.loadmat(path+filename)

    ## number of channels +1 to include time channel
    noChans = mat['noChans'][0,0]+1

    ## variables initialization
    channels = np.empty((noChans, 0)).tolist()
    channelsNames = np.empty((noChans, 0)).tolist()
    df = pd.DataFrame()

    ## extract raw data and allocate each channel in each variable
    for i in np.arange(noChans):
        channels[i] = mat['Data'][0,i].flatten()
        channelsNames[i] = mat['channelNames'][0][i][0]
        ## dataframe of raw data
        df[channelsNames[i]] = channels[i]

    ## signals filtering (pass-band filter), is it required ?

    ## raw data segmentation
    ## taking the begining of each stimulation signal (sync > 0 ) as t0
    ## we extract segments of 0.1 s from (t0 - 0.02 s) to (t0 + 0.08 s)

    ## identify starting stimulation from EMG
    ## emg threshold stimulation
    thr = 300 ## uV
    df_sync = df[(df.iloc[:,ch_emg]>thr) | (df.iloc[:,ch_emg]<-thr)]

    ## sync greater than zero -> stimulation (sync signal values: min=0, max=1)
    # df_sync = df[df.iloc[:,ch_sync]>0.5]
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

    df_sel = df.iloc[df_stm.index]

    df_max = pd.DataFrame()

    for tx in df_sel.iloc[:,ch_time]:
        df_roi = df[(df.iloc[:,ch_time]>=tx) & (df.iloc[:,ch_time]<(tx+0.007))]
        ## peak stimulation

        id_max = df_roi.iloc[:,ch_emg].idxmax()
        id_min = df_roi.iloc[:,ch_emg].idxmin()

        if np.abs(df.iloc[id_min,ch_emg]) > np.abs(df.iloc[id_max,ch_emg]):
            df_m = df[df.index==id_min]
        else:
            df_m = df[df.index==id_max]

        df_max = pd.concat([df_max,df_m], axis=0)


    ## number of stimulations
    # n_pulses = len(df_stm.index)
    n_pulses = len(df_max.index)

    ## from the original dataframe we extract rows that correspond with the begining of each stimulation pulse
    ## (using the indexes from df_stm) 
    # df_sel = df.iloc[df_stm.index]
    # print(f"df_sel:\n{df_sel}")

    ## creates a figure to plot the selected stimulation responses 
    n_rows = len(seg_stim)
    n_cols = 1
    fig, ax = plt.subplots(n_rows, n_cols, sharex=True, figsize=(10*n_cols, 5*n_rows))

    if len(seg_stim) > 1:
        ax = ax.flat
    else:
        ax = [ax]
        

    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    
    idx=0

    for i, t0 in enumerate(df_max.iloc[:,ch_time]):
        if i in seg_stim:
            df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]
            ## time, emg, and sync data from selected stimulations
            df_seg.iloc[:,ch_time] = df_seg.iloc[:,ch_time].to_numpy() - t0
            ## list of emg segments
            emg_list.append(df_seg)
            ## time axis
            t = df_seg.iloc[:,ch_time].to_numpy()
            ## plot emg segment at each subplot
            ax[idx].plot(t, df_seg.iloc[:,ch_emg])
            ax[idx].grid(color = 'green', linestyle = '--', linewidth = 0.2)
            ax[idx].set_title(f"stim: {i}")

            ## interactive rectangle selector
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

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_press)

    plt.show()

    return 0

def select_callback(eclick, erelease):
    """
    Callback for line selection.

    *eclick* and *erelease* are the press and release events.
    """
    global x1,y1,x2,y2

    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    # print(f"({x1:3.3f}, {y1:3.1f}) --> ({x2:3.3f}, {y2:3.1f})")
    # print(f"The buttons you used were: {eclick.button} {erelease.button}")


def on_click(event):
    global ax_sel
    # print(f"onclick event.inaxes: {event.inaxes}")
    if len(seg_stim) > 1:
        # print(f"ax: {ax}")
        ax_index = np.argwhere(event.inaxes == ax)
    else:
        # print(f"ax[0]: {ax[0]}")
        ax_index = [[0]]
    # print(f"onclick: {ax_index}")
    ax_sel = ax_index[0][0]
    # print(f"ax_index: {ax_sel}")

def on_press(event):
    # print('press', event.key)
    sys.stdout.flush()

    ## measuring amplitude peak to peak
    if event.key == 'a':
        
        ax[ax_sel].cla()

        df_emg = emg_list[ax_sel]

        ## plot emg segment at each subplot
        t = df_emg.iloc[:,ch_time].to_numpy()
        ax[ax_sel].plot(t, df_emg.iloc[:,ch_emg])
        ax[ax_sel].grid(color = 'green', linestyle = '--', linewidth = 0.2)
        ax[ax_sel].set_title(f"stim: {seg_stim[ax_sel]}")


        df_emg = df_emg[(df_emg.iloc[:,ch_time]>=x1) & (df_emg.iloc[:,ch_time]<=x2)]
        
        id_max = df_emg.iloc[:,ch_emg].idxmax()
        id_min = df_emg.iloc[:,ch_emg].idxmin()

        df_max = df_emg[df_emg.index==id_max]
        df_min = df_emg[df_emg.index==id_min]

        vpp = df_max.iloc[0,ch_emg] - df_min.iloc[0,ch_emg]
        print(f"Vpp: {vpp:3.2f} uV")

        ax[ax_sel].axhline(y=df_max.iloc[0,ch_emg], linestyle="--", color='tab:purple')
        ax[ax_sel].axhline(y=df_min.iloc[0,ch_emg], linestyle="--", color='tab:purple')

        x_a = x2 + (x2-x1)/10
        y_a = df_min.iloc[0,ch_emg] + (vpp)/10

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
        ax[ax_sel].set_title(f"stim: {seg_stim[ax_sel]}")

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

        x_a = x2 + (x2-x1)/5
        y_a = y1 + (y2-y1)/10

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
        ax[ax_sel].set_title(f"stim: {seg_stim[ax_sel]}")


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

        x_a = x2 + (x2-x1)/10
        y_a = df_min.iloc[0,ch_emg] + (v_stim)/10

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
        ax[ax_sel].set_title(f"stim: {seg_stim[ax_sel]}")

        fig.canvas.draw()

    else:
        pass



##########################
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
