import multiprocessing
import time
import subprocess
import os
import sys
import psutil  # For CPU usage and load monitoring
import numpy as np  # For matrix multiplications
import hashlib  # For cryptographic hashing

def simple_arithmetic(intensity):
    """Phase 1: Light arithmetic to slightly increase temperature."""
    x = 0
    for _ in range(intensity * 500):
        x += 1  # Minimal operations for gradual temp rise

def complex_arithmetic(intensity):
    """Phase 2: More operations for moderate load."""
    x = 1
    for _ in range(intensity * 1000):
        x *= 2  # Increasing complexity

def matrix_operations(intensity):
    """Phase 3: Matrix multiplications for higher stress."""
    size = intensity * 15  # Gradually larger matrices
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    np.dot(a, b)

def intensive_hashing(intensity):
    """Phase 4: Hashing for extreme load to induce throttling."""
    data = b"stress_data" * (intensity * 10)
    for _ in range(intensity * 20):
        hashlib.sha256(data).digest()

def stress_worker(phase, intensity):
    """Worker function for phase-specific tasks in a loop."""
    while True:
        if phase == 1:
            simple_arithmetic(intensity)
        elif phase == 2:
            complex_arithmetic(intensity)
        elif phase == 3:
            matrix_operations(intensity)
        elif phase == 4:
            intensive_hashing(intensity)

def get_cpu_frequency():
    """Get current CPU frequency in MHz."""
    try:
        freq_str = subprocess.check_output(['vcgencmd', 'measure_clock', 'arm']).decode('utf-8')
        freq = int(freq_str.split('=')[1]) / 1_000_000
        return freq
    except Exception:
        return None

def get_cpu_temperature():
    """Get current CPU temperature in °C."""
    try:
        temp_str = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
        temp = float(temp_str.split('=')[1].split("'")[0])
        return temp
    except Exception:
        return None

def main():
    num_cores = multiprocessing.cpu_count()
    print(f"Detected {num_cores} CPU cores. Starting gradual stress test...")

    # Start stress processes on each core
    processes = []
    phase = 1  # Start with light phase
    intensity = 1  # Starting intensity
    phase_start_time = time.time()
    phase_duration = 30  # Seconds before escalating phase

    manager = multiprocessing.Manager()
    shared_phase = manager.Value('i', phase)
    shared_intensity = manager.Value('i', intensity)

    for _ in range(num_cores):
        p = multiprocessing.Process(target=stress_worker, args=(shared_phase, shared_intensity))
        p.start()
        processes.append(p)

    try:
        last_log_time = time.time()
        while True:
            current_time = time.time()

            # Escalate phase and intensity
            if current_time - phase_start_time >= phase_duration:
                phase += 1
                if phase > 4:
                    phase = 4  # Max at phase 4, keep ramping intensity
                shared_phase.value = phase
                intensity += 1
                shared_intensity.value = intensity
                phase_start_time = current_time
                print(f"Escalating to phase {phase} with intensity {intensity}")

            # Log every 1 second
            if current_time - last_log_time >= 1:
                cpu_freq = get_cpu_frequency()
                cpu_temp = get_cpu_temperature()
                load_avg = os.getloadavg()
                cpu_usage = psutil.cpu_percent(interval=0.1)
                print(f"Phase: {phase} | Intensity: {intensity} | CPU Freq: {cpu_freq} MHz | CPU Temp: {cpu_temp}°C | Usage: {cpu_usage}% | Load: {load_avg}")
                last_log_time = current_time

            time.sleep(0.2)  # Avoid busy-waiting

    except KeyboardInterrupt:
        print("Stopping test...")
        for p in processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
