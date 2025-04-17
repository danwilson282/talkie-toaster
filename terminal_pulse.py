import wave
import numpy as np
import pyaudio
import time
import os

def print_volume_bar(volume, max_length=50):
    bar_length = int(volume * max_length)
    bar = '█' * bar_length
    space = ' ' * (max_length - bar_length)
    print(f"\r|{bar}{space}| {int(volume * 100)}%", end='', flush=True)

def play_audio_with_visualizer(filename):
    # Open WAV file
    wf = wave.open(filename, 'rb')
    CHUNK = 1024

    # Set up PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    try:
        print("Playing audio... Press Ctrl+C to stop.")
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)

            # Analyze volume
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean() / 32768  # normalize 0–1

            # Show volume bar in terminal
            print_volume_bar(volume)

            data = wf.readframes(CHUNK)

        print("\nDone.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# --- Run it ---
play_audio_with_visualizer("normal.wav")
