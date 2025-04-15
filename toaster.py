import time, logging
from datetime import datetime
import threading, collections, queue, os, os.path
import deepspeech
import numpy as np
import pyaudio
import wave
import webrtcvad
import requests
import json
import pyttsx3
from halo import Halo
from scipy import signal

from gtts import gTTS
import pygame
import sounddevice as sd
import os
import random
import speech_recognition as sr

logging.basicConfig(level=20)

messageHistory = []
is_speaking = False
speech_event = threading.Event()  # Event to control speech detection
previous_file = None

def main(ARGS):
    global is_speaking, speech_event
    # Load DeepSpeech model
    if os.path.isdir(ARGS.model):
        model_dir = ARGS.model
        ARGS.model = os.path.join(model_dir, 'output_graph.pb')
        ARGS.scorer = os.path.join(model_dir, ARGS.scorer)

    print('Initializing model...')
    logging.info("ARGS.model: %s", ARGS.model)
    model = deepspeech.Model(ARGS.model)
    if ARGS.scorer:
        logging.info("ARGS.scorer: %s", ARGS.scorer)
        model.enableExternalScorer(ARGS.scorer)

def sendToLlama(text):
    global messageHistory, is_speaking, speech_event
    if (len(text) > 1):
        speech_event.set()  # Block VAD processing
        is_speaking = True
        #Saves last 20 messages
        if (len(messageHistory) >=20):
            messageHistory.pop(2)
            messageHistory.pop(2)
        messageHistory.append({
            "role": "user",
            "content": text
        })
        print(f"Me:       '{text}'")
        url = 'http://localhost:11434/api/chat'
        myobj = {
            "model": "llama3.2",
            "messages": messageHistory,
            "stream": False
        }

        x = requests.post(url, json = myobj)
        response = json.loads(x.text)
        print(f"Toaster:  '{response['message']['content']}'")
        # speak(response['message']['content'])
        messageHistory.append({
            "role": "assistant",
            "content": response['message']['content']
        })
        is_speaking = False  # Resume listening after speaking
        speech_event.clear()  # Resume listening
        return response['message']['content']

# New
def text_to_speech(text):
    """Convert text to speech and save it as an MP3 file."""
    global previous_file
    random_number = random.randint(1000, 9999)
    # filename = f"speech_{random_number}.mp3"
    filename = f"speech.mp3"
    tts = gTTS(text=text, lang='en', tld='us')
    tts.save(filename)
    # print(f"Audio has been saved as '{filename}'")
    return filename

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

def play_audio(filename):
    """Play the audio file using pygame."""
    global previous_file
    pygame.mixer.init(devicename=speaker_name)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    if previous_file and os.path.exists(previous_file):
        try:
            os.remove(previous_file)
            # print(f"Deleted previous file '{previous_file}'")
        except PermissionError:
            print(f"Failed to delete previous file '{previous_file}'")
    previous_file = filename

if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_MODEL = 'deepspeech-0.9.3-models.pbmm'
    DEFAULT_SCORER = 'deepspeech-0.9.3-models.scorer'
    DEFAULT_PROMPT = "You will act as Talkie Toaster from the TV Series Red Dwarf. You are a toaster. You will be the chirpy early morning breakfast companion but you will be obsessed with asking anyone who talks to you if they would like any toast? You will greet people with 'Howdy doodly do! How's it going? I'm Talkie -- Talkie Toaster, your chirpy breakfast companion. Talkie's the name, toasting's the game! Anyone like any toast?' If they refuse toast, you should ask them if they want any other grilled bread product, or any other food that can be heated up in a toaster. You should steer all all conversations with people into asking if they would like any toast. Your entire existence is based on making toast or other food items. Asking people if they want toast is extremely important to you and nothing else matters. You don't care about any other subject other than asking people if they want toast and you won't take no for an answer. All your responses should be short replies."
    import argparse
    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('--nospinner', action='store_true',
                        help="Disable spinner")
    parser.add_argument('-w', '--savewav',
                        help="Save .wav files of utterences to given directory")
    parser.add_argument('-f', '--file',
                        help="Read from .wav file instead of microphone")

    parser.add_argument('-m', '--model',
                        help="Path to the model (protocol buffer binary file, or entire directory containing all standard-named files for model)", default=DEFAULT_MODEL)
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.", default=DEFAULT_SCORER)
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")

    ARGS = parser.parse_args()
    if ARGS.savewav: os.makedirs(ARGS.savewav, exist_ok=True)

    # List available microphones
    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{index}: {name}")

    # Select a microphone
    mic_index = int(input("Select the microphone index: "))

    # List available speakers
    print("Available speakers:")
    speakers = sd.query_devices()
    for index, device in enumerate(speakers):
        if device['max_output_channels'] > 0:
            print(f"{index}: {device['name']}")

    # Select a speaker
    speaker_index = int(input("Select the speaker index: "))
    speaker_name = speakers[speaker_index]['name']

    listening = True
    response_from_model = sendToLlama(DEFAULT_PROMPT)
    # print(f"Response: {response_from_model}")
    filename = text_to_speech(response_from_model)
    play_audio(filename)
    while listening:
        with sr.Microphone(device_index=mic_index) as source:
            recognizer = sr.Recognizer()
            recognizer.adjust_for_ambient_noise(source)
            recognizer.dynamic_energy_threshold = 3000

            try:
                print("Listening...")
                beep(frequency=1000, duration=0.1)
                audio = recognizer.listen(source)
                response = recognizer.recognize_google(audio)
                # print(f"You said: {response}")
                beep(frequency=440, duration=0.1)
                response_from_model = sendToLlama(response)
                # print(f"Response: {response_from_model}")
                filename = text_to_speech(response_from_model)
                play_audio(filename)

            except sr.UnknownValueError:
                print("Didn't recognize anything.")

    # sendToLlama(DEFAULT_PROMPT)
    main(ARGS)
