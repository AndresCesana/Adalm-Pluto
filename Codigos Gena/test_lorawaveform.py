#LIBRERIAS UTILIZADAS
import numpy as np
import matplotlib.pyplot as plt
import adi

Uri = "ip:192.168.2.1"
sdr = None  # Inicializar para el finally

try:
    sdr = adi.Pluto(Uri)
    print("PlutoSDR conectado exitosamente")
except Exception as e:
    print(f"Error conectando al PlutoSDR: {e}")
    print("Verifica la conexión y la dirección IP (192.168.2.1)")
    exit()

#----------------------------- FUNCIONES ------------------------------------------------------------
def generate_chirp_iq(simbolo, sf, Bw_hz, fs_hz, samples):
    """Genera chirp LoRa complejo (I/Q) en basebanda."""
    M = 2**sf
    Ts = M / Bw_hz
    t = np.arange(samples) / fs_hz
    k = Bw_hz / Ts
    # Chirp con offset de símbolo
    phi = 2*np.pi * (((simbolo / M) - 0.5) * Bw_hz * t + 0.5 * k * t**2)
    return (0.8 * np.exp(1j * phi)).astype(np.complex64)

def plot_waveform(ax, t, wf, axis_x_label, axis_y_label, title, Ts, len_packet_tx):
    ax.set_facecolor('black')
    ax.set_title(title, fontdict={'color':'white','weight':'bold','size': 20}, pad=20)
    ax.set_xlabel(axis_x_label, fontdict={'color':'white','weight':'bold','size': 20}, labelpad=10)
    ax.set_ylabel(axis_y_label, fontdict={'color':'white','weight':'bold','size': 20}, labelpad=5)
    ax.tick_params(axis='both', which='major', labelsize=10, colors='white')
    ax.plot(t, wf, lw=2)
    ax.grid()

#------------------------------- SDR Parameter Configuration -------------------------------
SamplingRate = 16e6
Loopback = 1
TxLOFreq = 910e6
TxAtten = -10
TxRfBw = 4e6
RxLOFreq = TxLOFreq
RxRfBw = TxRfBw           # ← Agregar esta línea
GainControlModes = "slow_attack"
RxBufferSize = 2**15

#------------------------------- SDR Setup -------------------------------
try:
    sdr.sample_rate = int(SamplingRate)
    sdr.loopback = Loopback
    # TX
    sdr.tx_enabled_channels = [0]
    sdr.tx_lo = int(TxLOFreq)
    sdr.tx_hardwaregain_chan0 = TxAtten
    sdr.tx_rf_bandwidth = int(TxRfBw)
    sdr.tx_cyclic_buffer = True
    # RX
    sdr.rx_lo = int(RxLOFreq)
    sdr.gain_control_mode_chan0 = GainControlModes
    sdr.rx_rf_bandwidth = int(RxRfBw)
    sdr.rx_cyclic_buffer = False
    sdr.rx_buffer_size = int(RxBufferSize)

    #------------------------------ GENERACIÓN DE SEÑAL (200 MUESTRAS) --------------------
    sf = 7
    Bw = 125e3  # Hz (corregido de kHz)
    symb = 50
    N_SAMPLES = 200  # ← Forzar 200 muestras

    # Generar chirp complejo I/Q con exactamente 200 muestras
    tx_signal = generate_chirp_iq(symb, sf, Bw, SamplingRate, N_SAMPLES)

    print(f"Símbolo transmitido: {symb}")
    print(f"Muestras generadas: {len(tx_signal)}")
    print(f"Tipo de dato: {tx_signal.dtype}")
    print(f"Rango I: [{np.min(np.real(tx_signal)):.3f}, {np.max(np.real(tx_signal)):.3f}]")
    print(f"Rango Q: [{np.min(np.imag(tx_signal)):.3f}, {np.max(np.imag(tx_signal)):.3f}]")

    # Gráfico I vs tiempo
    fig1, ax1 = plt.subplots(1, figsize=(12, 4))
    fig1.patch.set_facecolor('black')
    t_plot = np.arange(N_SAMPLES) / SamplingRate * 1e3  # ms
    plot_waveform(ax1, t_plot, np.real(tx_signal), "Tiempo [ms]", "I (a.u.)", 
                  f"LoRa Chirp - Símbolo {symb} ({N_SAMPLES} muestras)", 0, N_SAMPLES)

    #------------------------------- Transmitter -------------------------------
    sdr.tx(tx_signal)  # Enviar señal complex64 normalizada
    print("\n✓ Transmitiendo en modo cíclico...")
    print("Presiona Ctrl+C para detener\n")

    # Mantener transmitiendo
    import time
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n⚠ Deteniendo transmisión...")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # CRÍTICO: Destruir buffer TX antes de que Python destruya el contexto
    if sdr is not None:
        try:
            print("\nLiberando recursos del SDR...")
            sdr.tx_destroy_buffer()  # ← Evita access violation
            print("✓ Buffer TX destruido correctamente")
        except Exception as cleanup_error:
            print(f"⚠ Error al destruir buffer: {cleanup_error}")
        
        try:
            del sdr
            print("✓ Contexto SDR liberado\n")
        except Exception:
            pass
    
    # Mostrar gráficos (si se crearon)
    try:
        plt.show()
    except Exception:
        pass