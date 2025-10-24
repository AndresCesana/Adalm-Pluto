# Import the library
import numpy as np
import adi
import time
import matplotlib.pyplot as plt

# Create a device interface
sdr = adi.Pluto("ip:192.168.2.1")

# ==============================================================================
# Configuración básica
# ==============================================================================
fc = 1e9              # Frecuencia portadora: 1 GHz
fs = 1e6              # Frecuencia de muestreo: 1 MHz
N = 1024            # Tamaño del buffer (número de muestras)

f_baseband = 5e3      # 5 kHz en basebanda (para ver oscilación en el gráfico)
amplitude = 0.5       # Amplitud normalizada (0 a 1)

# ==============================================================================
# Configurar PlutoSDR (orden correcto)
# ==============================================================================
# IMPORTANTE: Asegurar que solo hay 1 canal TX habilitado
sdr.tx_enabled_channels = [0]  # Solo canal 0

sdr.sample_rate = int(fs)
sdr.tx_lo = int(fc)
sdr.tx_rf_bandwidth = int(4e6)          # 4 MHz (coherente con rx_rf_bandwidth)
sdr.tx_hardwaregain_chan0 = -10         # Ganancia TX

# RX (para loopback si querés)
sdr.rx_lo = int(fc)
sdr.rx_rf_bandwidth = int(4e6)
sdr.gain_control_mode_chan0 = "slow_attack"


# DEBUG: Verificar configuración
print("\n=== CONFIGURACIÓN ===")
print(f"TX enabled channels: {sdr.tx_enabled_channels}")
print(f"Número de canales: {len(sdr.tx_enabled_channels)}")
print(f"Sample rate: {sdr.sample_rate/1e6} MS/s")
print(f"TX LO: {sdr.tx_lo/1e9} GHz")
print("=====================\n")

# ==============================================================================
# Generar señal senoidal REAL
# ==============================================================================
t = np.arange(N) / fs  # Vector de tiempo

# Señal real (coseno)
y_real = amplitude * np.cos(2.0 * np.pi * f_baseband * t)

# Convertir a formato COMPLEJO requerido por pyadi-iio
y = y_real.astype(np.float32) + 1j * np.zeros(N, dtype=np.float32)
y = y.astype(np.complex64)

# IMPORTANTE: Configurar ANTES de tx()
sdr.tx_destroy_buffer()
sdr.tx_cyclic_buffer = True


# DEBUG: Verificar señal
print("=== SEÑAL GENERADA ===")
print(f"Tipo: {y.dtype}")
print(f"Shape: {y.shape}")
print(f"Primeras 3 muestras: {y[:3]}")
print(f"Es array 1D: {y.ndim == 1}")
print("======================\n")

# ==============================================================================
# Visualización (NON-BLOCKING)
# ==============================================================================
plt.figure(figsize=(12, 4))
plt.plot(t[:500] * 1e3, np.real(y[:500]))  # Mostrar primeros 500 puntos
plt.xlabel('Tiempo (ms)')
plt.ylabel('Amplitud (I)')
plt.title(f'Señal basebanda: {f_baseband/1e3:.1f} kHz @ {fs/1e6:.1f} MS/s')
plt.grid(True)
plt.tight_layout()
plt.ion()  # Modo interactivo
plt.show()
plt.pause(0.1)  # Mostrar brevemente

# ==============================================================================
# Transmitir
# ==============================================================================
print(f"\n{'='*60}")
print(f"Transmitiendo en modo CÍCLICO:")
print(f"  Portadora: {fc/1e9:.3f} GHz")
print(f"  Basebanda: {f_baseband/1e3:.1f} kHz")
print(f"  RF LSB: {(fc-f_baseband)/1e9:.6f} GHz")
print(f"  RF USB: {(fc+f_baseband)/1e9:.6f} GHz")
print(f"  Muestras: {N}")
print(f"  Duración buffer: {N/fs*1e3:.1f} ms (se repite infinitamente)")
print(f"{'='*60}\n")

try:
    sdr.tx(y)  # Pasa array 1D directamente
    print("✓ Transmitiendo en LOOP... Presiona Ctrl+C para detener")
    
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n⚠ Deteniendo transmisión...")

except Exception as e:
    print(f"\n✗ Error durante transmisión: {e}")
    print(f"   Tipo de dato enviado: {type(y)}")
    print(f"   Shape: {y.shape}")

finally:
    try:
        print("⏳ Liberando recursos...")
        # 1. PRIMERO: Destruir buffer
        sdr.tx_destroy_buffer()
        
        # 2. DESPUÉS: Cambiar modo cíclico
        sdr.tx_cyclic_buffer = False
        
        # 3. FINALMENTE: Eliminar objeto
        del sdr
        print("✓ Recursos liberados")
    except Exception as e:
        print(f"⚠ Error al liberar: {e}")
    
    plt.close('all')  # Cerrar gráficos