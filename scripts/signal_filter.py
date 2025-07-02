import numpy as np
from scipy.signal import butter, lfilter, freqz, sosfiltfilt, freqz_sos
import matplotlib.pyplot as plt


def butter_lowpass_sos(cutoff, fs, order=3):
    return butter(order, cutoff, fs=fs, btype='low', analog=False, output='sos')

def butter_lowpass_filter_sos(data, cutoff, fs, order=3):
    sos = butter_lowpass_sos(cutoff, fs, order=order)
    # y = lfilter(b, a, data)
    y = sosfiltfilt(sos, data)
    return y


def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Filter requirements.
order = 5
fs = 4000.0       # sample rate, Hz
cutoff = 150.0  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
# b, a = butter_lowpass(cutoff, fs, order)
sos = butter_lowpass_sos(cutoff, fs, order)

# Plot the frequency response.
# w, h = freqz(b, a, fs=fs, worN=8000)
w, h = freqz_sos(sos, fs=fs, worN=8000)
plt.subplot(2, 1, 1)
plt.plot(w, np.abs(h), 'b')
plt.plot(cutoff, 0.5*np.sqrt(2), 'ko')
plt.axvline(cutoff, color='k')
plt.xlim(0, 0.5*fs)
plt.title("Lowpass Filter Frequency Response")
plt.xlabel('Frequency [Hz]')
plt.grid()


# Demonstrate the use of the filter.
# First make some data to be filtered.
T = 0.1         # seconds
n = int(T * fs) # total number of samples
t = np.linspace(0, T, n, endpoint=False)
# "Noisy" data.  We want to recover the 1.2 Hz signal from this.
data = np.sin(100.0*2*np.pi*t) + 1.5*np.cos(200.0*2*np.pi*t) # + 0.5*np.sin(12.0*2*np.pi*t)

# Filter the data, and plot both the original and filtered signals.
y = butter_lowpass_filter_sos(data, cutoff, fs, order)

plt.subplot(2, 1, 2)
plt.plot(t, data, 'b-', label='data')
plt.plot(t, y, 'g-', linewidth=2, label='filtered data')
plt.xlabel('Time [sec]')
plt.grid()
plt.legend()

plt.subplots_adjust(hspace=0.35)
plt.show()