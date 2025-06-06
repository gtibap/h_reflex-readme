import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio

from participants import participants_dict


def main(args):

    ## participant number
    id = int(args[1])

    ## folder data location
    path="../../data/mat_legacy/"
    
    ## retrieve data identification selected participant
    id_p = participants_dict[id]

    ## filename recorded h-reflex raw data    
    filename = id_p['filename']

    ## load h-reflex raw data
    mat = sio.loadmat(path+filename)
    print(f"mat:\n{mat}")

    ## get number of channels
    noChans = mat['noChans'][0,0]+1

    ## variables initialization
    channels = np.empty((noChans, 0)).tolist()
    channelsNames = np.empty((noChans, 0)).tolist()

    ## read raw data (channels) and channels names
    for i in np.arange(noChans):
        channels[i] = mat['Data'][0,i].flatten()
        channelsNames[i] = mat['channelNames'][0][i][0]

    ## data visualization
    fig, ax = plt.subplots((noChans-1), 1, sharex=True)
    ax = ax.flat
    for i in np.arange(noChans-1):
        ax[i].plot(channels[0], channels[i+1])
        ax[i].set_title(f"{i+1} - {channelsNames[i+1]}")

    plt.show(block=True)

    return 0


## initialization
if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
