participants_dict={
    1:{
        ## to run h_reflex_01.py
        'filename':"Megane_JD.mat",
        ## from the resultant plot of h_reflex_01.py, identify the channels' order from top to bottom, (starting at 1)
        'ch_emg': [1,], 
        'ch_sync': 2,
        ## from the resultant plot of h_reflex_02.py, identify the stim numbers that correspond to the max pick to pick of both h-reflex (stim_h) and M-wave (stim_m). Additionally, identify the emg channel selected for measuring (ch_mea)
        'ch_mea': 1,
        'stim_hm': [7,12,13],
    },
}