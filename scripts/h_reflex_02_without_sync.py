################################################
## When the stimulation signals is not available,
## we generate a stim signals detecting the first peak of each 
## muscular reaction recorded in the emg signal 
################################################
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
from matplotlib.backend_bases import MouseButton

from participants import participants_dict

###############
def main(args):
    global binding_id

    ## participant number
    id = int(args[1])

    ## folder data location
    path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    filename    = id_p['filename']
    ch_emg_list = id_p['ch_emg']
    # ch_sync     = id_p['ch_sync']
    ch_mea      = id_p['ch_mea']
    
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


    #################################
    ###############################
    ## identify starting stimulation from EMG
    ## emg threshold stimulation
    thr = 300 ## uV
    df_sync = df[(df.iloc[:,ch_mea]>thr) | (df.iloc[:,ch_mea]<-thr)]

    ## raw data segmentation
    ## taking the begining of each stimulation signal (sync > 0 ) as t0
    ## we extract segments of 0.1 s from (t0 - 0.02 s) to (t0 + 0.08 s)

    ## to identify the initial sample of each stimulation
    ## we apply the difference between adjacent values
    df_diff = df_sync.diff()
    # print(f"df_diff:\n{df_diff}")

    ## if the difference in time is greater than 1 s, means the beginning of an stimulation pulse
    ## because time between stimulations is bigger than 1 s (usually 10 s between two consecutive stimulations)
    ## the second condition is to identify NaN values 
    ## (the first difference is NaN but corresponds to the begining of the first stimulation pulse)
    df_stm = df_diff[ (df_diff.iloc[:,ch_time]>1) | (df_diff.iloc[:,ch_time]!=df_diff.iloc[:,ch_time]) ]

    ## finding peak value from emg (time t0) for each stimulation
    ## from the first sample + 0.007 s we search the peak for each stimulation

    df_sel = df.iloc[df_stm.index]

    df_max = pd.DataFrame()

    for tx in df_sel.iloc[:,ch_time]:
        df_roi = df[(df.iloc[:,ch_time]>=tx) & (df.iloc[:,ch_time]<(tx+0.007))]
        ## peak stimulation

        id_max = df_roi.iloc[:,ch_mea].idxmax()
        id_min = df_roi.iloc[:,ch_mea].idxmin()

        if np.abs(df.iloc[id_min,ch_mea]) > np.abs(df.iloc[id_max,ch_mea]):
            df_m = df[df.index==id_min]
        else:
            df_m = df[df.index==id_max]

        df_max = pd.concat([df_max,df_m], axis=0)
        
    ###############################
    #################################


    # print(f"df_stm indexes:\n{df_stm.index}")
    # print(f"number of pulses:\n{len(df_stm.index)}")

    n_pulses = len(df_max.index)

    ## from the original dataframe we extract rows that correspond with the begining of each stimulation pulse
    ## (using the indexes from df_stm) 
    # df_sel = df.iloc[df_stm.index]
    # print(f"df_sel:\n{df_sel}")

    n_rows = int(np.ceil(np.sqrt(n_pulses)))
    n_cols = int(np.ceil(n_pulses/n_rows))

    for ch_emg in ch_emg_list:
        fig, ax = plt.subplots(n_rows, n_cols, sharex=True, sharey=True, figsize=(3*n_cols, 2*n_rows))
        ax = ax.flat
        ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
        ## iterate using time (column 0)
        for i, t0 in enumerate(df_max.iloc[:,ch_time]):
            print(f"t0: {t0}")
            df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<=(t0+0.08))]
            # print(f"df_seg:\n{df_seg}")
            ## time axis
            df_seg.iloc[:,ch_time] = df_seg.iloc[:,ch_time].to_numpy() - t0
            t = df_seg.iloc[:,ch_time].to_numpy()
            # t = np.linspace(-0.02, 0.08, len(df_seg))
            ## plot emg segment at each subplot
            ax[i].plot(t, df_seg.iloc[:,ch_emg])
            ax[i].grid(color = 'green', linestyle = '--', linewidth = 0.2)
            ax[i].set_title(f"stim: {i}")
        fig.suptitle(f"{channelsNames[ch_emg]}")

    plt.show(block=True)

    return 0

##########################
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
