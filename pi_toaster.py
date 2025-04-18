import speech_recognition as sr
import requests
import json
from gtts import gTTS
import os
import numpy as np
import pygame
import subprocess
import logging
import pyaudio
# import RPi.GPIO as GPIO

logging.disable(logging.CRITICAL)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "alsa"
os.environ["ALSA_CARD"] = "2"  # Optional
os.environ["PYTTSX3_NO_ALSA_WARNINGS"] = "1"
# GPIO input
LED_PIN = 18
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LED_PIN, GPIO.OUT)
# pwm = GPIO.PWM(LED_PIN, 100)  # 100Hz PWM
# pwm.start(0)
messageHistory = []
DEFAULT_PROMPT = "You will act as Talkie Toaster from the TV Series Red Dwarf. You are a toaster. You will be the chirpy early morning breakfast companion but you will be obsessed with asking anyone who talks to you if they would like any toast? You will greet people with 'Howdy doodly do! How's it going? I'm Talkie -- Talkie Toaster, your chirpy breakfast companion. Talkie's the name, toasting's the game! Anyone like any toast?' If they refuse toast, you should ask them if they want any other grilled bread product, or any other food that can be heated up in a toaster. You should steer all all conversations with people into asking if they would like any toast. Your entire existence is based on making toast or other food items. Asking people if they want toast is extremely important to you and nothing else matters. You don't care about any other subject other than asking people if they want toast and you won't take no for an answer. All your responses should be short replies."

def speak(text):
    tts = gTTS(text=text, lang='en', tld='com')
    tts.save("output.mp3")
    # 2. Convert to WAV for pitch processing
    os.system("ffmpeg -y -i output.mp3 output.wav")

    # 3. Lower pitch and slow it down slightly
    subprocess.run([
        "sox", "output.wav", "toaster_voice.wav",
        "pitch", "200", "speed", "1.3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

    # 4. Play it
    # subprocess.run(["aplay", "toaster_voice.wav"])
    play_audio_with_visualizer("toaster_voice.wav")

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
            # pwm.ChangeDutyCycle(min(volume * 100, 100))
            data = wf.readframes(CHUNK)

        print("\nDone.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        # pwm.ChangeDutyCycle(0)

def transcribe_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone(device_index=1) as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("🧠 Recognizing...")
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return None
    except sr.RequestError:
        speak("Speech recognition service is down.")
        return None

def sendToLlama(text):
    global messageHistory
    if len(text) > 1:
        # Save last 20 messages
        if len(messageHistory) >= 20:
            messageHistory.pop(0)  # Remove the oldest message
        messageHistory.append({
            "role": "user",
            "content": text
        })

        url = 'http://localhost:11434/api/chat'
        myobj = {
            "model": "llama3.2",
            "messages": messageHistory,
            "stream": False
        }

        x = requests.post(url, json=myobj)
        response = json.loads(x.text)
        assistant_response = response['message']['content']
        messageHistory.append({
            "role": "assistant",
            "content": assistant_response
        })
        return assistant_response

def voice_assistant():
    response = sendToLlama(DEFAULT_PROMPT)
    print(f"🍞 Toaster: {response}")
    speak(response)
    beep(frequency=1000, duration=0.1)
    while True:
        user_input = transcribe_audio()
        if user_input:
            beep(frequency=440, duration=0.1)
            print(f"👤 You said: {user_input}")
            if user_input.lower() in ["exit", "quit", "stop", "goodbye", "bye"]:
                print("👋 Goodbye!")
                speak("Goodbye!")
                break
            response = sendToLlama(user_input)
            print(f"🍞 Toaster: {response}")
            speak(response)
            beep(frequency=1000, duration=0.1)

def generate_beep_sound(frequency=440, duration=0.5, sample_rate=44100):
    # Generate a sine wave for the beep sound
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(frequency * 2 * np.pi * t)
    
    # Normalize the wave to 16-bit range
    wave = np.int16(wave * 32767)
    
    # Convert to stereo (2 channels)
    wave = np.column_stack((wave, wave))
    
    return wave

def beep(frequency=440, duration=0.5, sample_rate=44100):
    # Initialize pygame mixer
    pygame.mixer.init(sample_rate, -16, 2, 2048)
    
    # Generate the beep sound
    beep_sound = generate_beep_sound(frequency, duration, sample_rate)
    
    # Create a pygame Sound object
    sound = pygame.sndarray.make_sound(beep_sound)
    
    # Play the sound
    sound.play()
    
    # Wait for the sound to finish playing
    pygame.time.wait(int(duration * 1000))

# Run it
if __name__ == "__main__":
    voice_assistant()
