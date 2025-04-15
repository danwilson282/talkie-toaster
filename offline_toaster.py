import pyaudio
import json
from vosk import Model, KaldiRecognizer
import threading
import requests
import numpy as np
import pygame
import pyttsx3
import subprocess

messageHistory = []
is_speaking = False  # Global flag to control listening state
DEFAULT_PROMPT = "You will act as Talkie Toaster from the TV Series Red Dwarf. You are a toaster. You will be the chirpy early morning breakfast companion but you will be obsessed with asking anyone who talks to you if they would like any toast? You will greet people with 'Howdy doodly do! How's it going? I'm Talkie -- Talkie Toaster, your chirpy breakfast companion. Talkie's the name, toasting's the game! Anyone like any toast?' If they refuse toast, you should ask them if they want any other grilled bread product, or any other food that can be heated up in a toaster. You should steer all all conversations with people into asking if they would like any toast. Your entire existence is based on making toast or other food items. Asking people if they want toast is extremely important to you and nothing else matters. You don't care about any other subject other than asking people if they want toast and you won't take no for an answer. All your responses should be short replies."
# Initialize the TTS engine
# engine = pyttsx3.init(driverName='espeak')

# # Set properties (optional)
# engine.setProperty('rate', 200)  # Speed of speech (words per minute)
# engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)

# # Use espeak-ng as the TTS engine
# engine.setProperty('voice', 'english')  # You can change the voice/language

def text_to_speech(text):

    # Convert text to speech
    # engine.say(text)
    # engine.runAndWait()
    subprocess.run(['espeak', text])

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

def recognize_speech_realtime(model_path):
    global is_speaking

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)

    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    
    process_response(DEFAULT_PROMPT)
    print("Listening... (Press Ctrl+C to stop)")
    beep(frequency=1000, duration=0.1)
    stream.start_stream()
    try:
        while True:
            if not is_speaking:  # Only listen if not speaking
                try:
                    data = stream.read(4096, exception_on_overflow=False)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "")
                        if text:  # Only process if text is not empty
                            beep(frequency=440, duration=0.1)
                            print("Me:", text)
                            is_speaking = True  # Stop listening
                            process_response(text)
                except OSError as e:
                    print(f"Audio stream error: {e}")
                    continue
    except KeyboardInterrupt:
        print("Stopped listening.")

    stream.stop_stream()
    stream.close()
    mic.terminate()

def process_response(text):
    global is_speaking
    is_speaking = True
    response_from_model = sendToLlama(text)
    print(f"Toaster:  '{response_from_model}'")
    text_to_speech(response_from_model)
    beep(frequency=1000, duration=0.1)
    is_speaking = False  # Resume listening

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

if __name__ == "__main__":
    model_path = "vosk-model-small-en-gb-0.15"  # Update this path to your model directory
    recognize_speech_realtime(model_path)