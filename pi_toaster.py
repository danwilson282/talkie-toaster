import pyaudio
import json
from vosk import Model, KaldiRecognizer
import threading
import requests
import numpy as np
import pygame
import subprocess

messageHistory = []
is_speaking = False
DEFAULT_PROMPT = (
    "You will act as Talkie Toaster from the TV Series Red Dwarf. You are a toaster. "
    "You will be the chirpy early morning breakfast companion but you will be obsessed "
    "with asking anyone who talks to you if they would like any toast? You will greet "
    "people with 'Howdy doodly do! How's it going? I'm Talkie -- Talkie Toaster, your chirpy "
    "breakfast companion. Talkie's the name, toasting's the game! Anyone like any toast?' "
    "If they refuse toast, you should ask them if they want any other grilled bread product, "
    "or any other food that can be heated up in a toaster. You should steer all conversations "
    "into asking if they would like any toast. Your entire existence is based on making toast "
    "or other food items. Asking people if they want toast is extremely important to you and "
    "nothing else matters. You don't care about any other subject other than asking people "
    "if they want toast and you won't take no for an answer. All your responses should be short replies."
)

def text_to_speech(text):
    # Use espeak via subprocess for TTS
    subprocess.run(['espeak', '-s', '175', text])

def generate_beep_sound(frequency=440, duration=0.2, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(frequency * 2 * np.pi * t)
    wave = np.int16(wave * 32767)
    wave = np.column_stack((wave, wave))
    return wave

def beep(frequency=440, duration=0.2, sample_rate=44100):
    pygame.mixer.init(sample_rate, -16, 2, 2048)
    sound_array = generate_beep_sound(frequency, duration, sample_rate)
    sound = pygame.sndarray.make_sound(sound_array)
    sound.play()
    pygame.time.wait(int(duration * 1000))

def recognize_speech_realtime(model_path, device_index=None):
    global is_speaking

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)

    mic = pyaudio.PyAudio()

    if device_index is None:
        print("Available audio input devices:")
        for i in range(mic.get_device_count()):
            info = mic.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"{i}: {info['name']}")
        device_index = int(input("Select device index to use for input: "))

    stream = mic.open(format=pyaudio.paInt16,
                      channels=1,
                      rate=16000,
                      input=True,
                      input_device_index=device_index,
                      frames_per_buffer=4096)

    stream.start_stream()
    process_response(DEFAULT_PROMPT)
    print("Listening... (Press Ctrl+C to stop)")
    beep(1000, 0.1)

    try:
        while True:
            if not is_speaking:
                data = stream.read(2048, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        beep(440, 0.1)
                        print("Me:", text)
                        is_speaking = True
                        threading.Thread(target=process_response, args=(text,)).start()
    except KeyboardInterrupt:
        print("Stopped listening.")

    stream.stop_stream()
    stream.close()
    mic.terminate()

def process_response(text):
    global is_speaking
    response_from_model = sendToLlama(text)
    print(f"Toaster: '{response_from_model}'")
    text_to_speech(response_from_model)
    beep(1000, 0.1)
    is_speaking = False

def sendToLlama(text):
    global messageHistory
    if len(text) > 1:
        if len(messageHistory) >= 20:
            messageHistory.pop(0)
        messageHistory.append({"role": "user", "content": text})

        url = 'http://localhost:11434/api/chat'
        payload = {
            "model": "llama3.2",
            "messages": messageHistory,
            "stream": False
        }

        response = requests.post(url, json=payload)
        response_json = response.json()
        reply = response_json['message']['content']
        messageHistory.append({"role": "assistant", "content": reply})
        return reply

if __name__ == "__main__":
    model_path = "vosk-model-small-en-gb-0.15"
    recognize_speech_realtime(model_path)
