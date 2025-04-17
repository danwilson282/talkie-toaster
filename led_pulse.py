import wave
import numpy as np
import RPi.GPIO as GPIO
import time

# --- Setup LED pin with PWM ---
LED_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
pwm = GPIO.PWM(LED_PIN, 100)  # 100Hz PWM
pwm.start(0)

# --- Audio playback and analysis ---
import pyaudio

def play_and_react_to_audio(filename):
    # Open the WAV file
    wf = wave.open(filename, 'rb')
    CHUNK = 1024

    # Setup PyAudio for playback
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    try:
        data = wf.readframes(CHUNK)
        while data:
            # Play audio
            stream.write(data)

            # Convert byte data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean() / 32768  # normalize to 0–1

            # Set LED brightness
            pwm.ChangeDutyCycle(min(volume * 100, 100))

            # Read next chunk
            data = wf.readframes(CHUNK)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        pwm.ChangeDutyCycle(0)

# --- Run it ---
try:
    play_and_react_to_audio("normal.wav")
finally:
    pwm.stop()
    GPIO.cleanup()
