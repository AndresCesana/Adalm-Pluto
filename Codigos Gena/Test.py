import time
import msvcrt  # Solo Windows
import numpy as np
import adi

URI          = "ip:192.168.2.1"
FS           = 2_000_000
TX_LO        = 910_000_000
TX_ATTEN_DB  = -10             # sube potencia para probar
TX_RFBW      = 1_500_000
TONE_BB_HZ   = 200_000
N_SAMPLES    = 2**14
BURST_SEC    = N_SAMPLES / FS   # duración de la ráfaga cuando uses DDS

sdr = adi.Pluto(URI)
try: sdr._ctx.set_timeout(10000)
except Exception: pass

# Configuración base
sdr.loopback              = 0
sdr.sample_rate           = int(FS)
sdr.tx_lo                 = int(TX_LO)
sdr.tx_hardwaregain_chan0 = float(TX_ATTEN_DB)
sdr.tx_rf_bandwidth       = int(TX_RFBW)
sdr.tx_enabled_channels   = [0]         # usar TX0

# Asegurar DDS apagado al iniciar
try: sdr.dds_single_tone(0, 0.0, channel=0)
except Exception: pass

# Señal compleja de prueba (para DMA)
t = np.arange(N_SAMPLES) / FS
signal = (0.8 * np.exp(1j * 2*np.pi * TONE_BB_HZ * t)).astype(np.complex64)

print("Listo. Pulsa 'v' para transmitir una vez (elige modo abajo), 'q' para salir.")
print("Modo A: DMA por ráfaga | Modo B: DDS temporizado")
modo = "B"   # Cambia a "A" para probar DMA

try:
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'v', b'V'):
                if modo.upper() == "A":
                    # --- Opción A: ráfaga por DMA (no cíclico) ---
                    sdr.tx_cyclic_buffer = False
                    try:
                        # re-crear buffer limpio antes de cada envío
                        sdr.tx_destroy_buffer()
                    except Exception:
                        pass
                    # tamaño de buffer de TX explícito
                    try:
                        sdr.tx_buffer_size = int(N_SAMPLES)
                    except Exception:
                        pass
                    # enviar ráfaga
                    try:
                        sdr.tx(signal)
                        print(f"DMA TX enviado: {len(signal)} muestras")
                    except Exception as e:
                        print(f"DMA TX error: {e}")

                else:
                    # --- Opción B: DDS interno (encender por BURST_SEC y apagar) ---
                    try:
                        sdr.dds_single_tone(int(TONE_BB_HZ), 0.8, channel=0)
                        time.sleep(BURST_SEC)  # misma duración que N_SAMPLES/FS
                    finally:
                        # apagar DDS
                        sdr.dds_single_tone(int(TONE_BB_HZ), 0.0, channel=0)
                    print(f"DDS TX enviado: {BURST_SEC*1e3:.1f} ms")
            elif ch in (b'q', b'Q'):
                print("Saliendo...")
                break
        time.sleep(0.01)
finally:
    # apagar cualquier tono DDS y liberar DMA
    try: sdr.dds_single_tone(int(TONE_BB_HZ), 0.0, channel=0)
    except Exception: pass
    try: sdr.tx_destroy_buffer()
    except Exception: pass