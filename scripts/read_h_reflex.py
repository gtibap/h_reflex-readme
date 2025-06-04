import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.io as sio
from matplotlib.backend_bases import MouseButton

binding_id = []

def on_move(event):
    if event.inaxes:
        print(f'data coords {event.inaxes} {event.xdata} {event.ydata},',
              f'pixel coords {event.x} {event.y}')


def on_click(event):
    if event.button is MouseButton.LEFT:

        print(f'{event.inaxes} disconnecting callback')
        plt.disconnect(binding_id)



def main(args):
    global binding_id

    # print(f"h reflex !")
    
    path="../../data/mat_legacy/"
    
    filename="Megane_JD.mat"
    ch_time, ch_emg, ch_sync = 0, 1, 2
    
    # filename="H-Reflexe_LuisR.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2

    # filename="H-Reflexe_IuliaC.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2

    # filename="MIA_test1.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2

    # filename="MIA_test2_protocole.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2

    # filename="MIA_test3_protocole.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2

    # filename="MIA_test4_protocole.mat"
    # ch_time, ch_emg, ch_sync = 0, 1, 2
    

    mat = sio.loadmat(path+filename)
    # print(f"mat:\n{mat}")

    # print(f"header: {mat['__header__']}")
    # print(f"samplingRate: {mat['samplingRate']}")
    # print(f"length_sec: {mat['length_sec']}")
    # print(f"noChans: {mat['noChans']}")
    # print(f"channelNames: {mat['channelNames']}")
    # print(f"data: {mat['Data'].shape}")

    noChans = mat['noChans'][0,0]+1
    channels = np.empty((noChans, 0)).tolist()
    channelsNames = np.empty((noChans, 0)).tolist()

    df = pd.DataFrame()

    for i in np.arange(noChans):
        channels[i] = mat['Data'][0,i].flatten()
        channelsNames[i] = mat['channelNames'][0][i][0]

        df[channelsNames[i]] = channels[i]

    print(f"channels:\n{channels}")
    print(f"channelsNames:\n{channelsNames}")


    # fig_a, ax_a = plt.subplots(2, 1, sharex=True)
    # ax_a = ax_a.flat
    # ax_a[0].plot(channels[0], channels[1])
    # ax_a[1].plot(channels[0], channels[2])

    # plt.show(block=True)

    
    # print(f"dataframe:\n{df}")
    # print(f"df column 2:\n{df.iloc[:,2]}")

    ## sync greater than zero -> stimulation
    df_sync = df[df.iloc[:,ch_sync]>0]
    print(f"df_sync:\n{df_sync}")

    ## initial time each stimulation
    df_diff = df_sync.diff()
    print(f"df_diff:\n{df_diff}")

    ## != condition is to identify NaN values (first one)
    df_stm = df_diff[ (df_diff.iloc[:,ch_time]>1) | (df_diff.iloc[:,ch_time]!=df_diff.iloc[:,ch_time]) ]
    print(f"df_stm:\n{df_stm}")

    print(f"df_stm indexes:\n{df_stm.index}")

    df_sel = df.iloc[df_stm.index]
    print(f"df_sel:\n{df_sel}")

    fig, ax = plt.subplots(4, 4, sharex=True, sharey=True)
    ax = ax.flat
    ## segment signal from (t0 - 0.02 s) to (t0 + 0.08 s) 
    ## iterate using time (column 0)
    for i, t0 in enumerate(df_sel.iloc[:,0]):
        # print(f"t0: {t0}")
        df_seg = df[(df.iloc[:,ch_time]>=(t0-0.02)) & (df.iloc[:,ch_time]<(t0+0.08))]
        print(f"df_seg:\n{df_seg}")

        t = np.linspace(-0.02, 0.08, len(df_seg))
        ax[i].plot(t, df_seg.iloc[:,ch_emg])
        ax[i].grid(color = 'green', linestyle = '--', linewidth = 0.5)

    # df[df[2]]

    ax[0].set_ylim([-8000,5000])
    # cursor = Cursor(ax[0], color='green', linewidth=2)
    

    # fig, ax = plt.subplots(2, 1, sharex=True)
    # ax = ax.flat
    # ax[0].plot(channels[0], channels[1])
    # ax[1].plot(channels[0], channels[2])

    binding_id = plt.connect('motion_notify_event', on_move)
    plt.connect('button_press_event', on_click)

    plt.show(block=True)


    

    # print(f"header: {mat['__header__']}")


    # sampling_rate = mat['samplingRate'][0,0]
    # noChans = mat['noChans'][0,0]+1

    # print(f"sampling rate, channels: {sampling_rate, noChans}")
        
    # channels = np.empty((noChans, 0)).tolist()
    # channelsNames = np.empty((noChans, 0)).tolist()

    # for i in np.arange(noChans):
    #     channels[i] = mat['Data'][0,i].flatten()
    #     channelsNames[i] = mat['channelNames'][0][i][0]

    

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
