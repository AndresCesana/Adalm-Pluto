# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import adi

# Create radio
sdr = adi.Pluto()

# Configure properties
sdr.rx_rf_bandwidth = 4_000_000
sdr.rx_lo = 2000_000_000
sdr.tx_lo = 1400_000_000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain_chan0 = -30
sdr.gain_control_mode_chan0 = "slow_attack"

# Create a sinewave waveform
fs = int(sdr.sample_rate)

# Parámetros chirp
N = 1024                           # muestras por bloque (lo que pediste)
BW = 15e6                          # ancho de banda 15 MHz
Tp = N / float(fs)                 # duración del chirp (s) = N/fs

# Definir f_start y f_end en baseband (relativas al LO del TX).
# Si quieres un chirp de 0 -> BW en baseband: f_start = 0.0, f_end = BW
# Si prefieres centrado en 0: f_start = -BW/2, f_end = +BW/2
f_start = -BW/2.0                  # por ejemplo centrado en 0 (±7.5 MHz)
f_end =  BW/2.0

# Vector tiempo para N muestras
t = np.arange(N) / float(fs)

# Pendiente (Hz/s)
k = (f_end - f_start) / Tp

# Fase correcta (radianes): 2π * (f_start*t + 0.5*k*t^2)
phase = 2.0 * np.pi * (f_start * t + 0.5 * k * t**2)

# Señal compleja IQ, escalada y casteada
amp = 2**14
tx_chirp = (np.exp(1j * phase) * amp).astype(np.complex64)

# Enviar (asegurate tx_cyclic_buffer True si querés repetir)
sdr.tx_cyclic_buffer = True
sdr.tx(tx_chirp)

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x, fs)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e2])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()