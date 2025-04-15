import speech_recognition as sr
import pyttsx3
import requests
import json
from gtts import gTTS
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "alsa"
os.environ["ALSA_CARD"] = "2"  # Optional
os.environ["PYTTSX3_NO_ALSA_WARNINGS"] = "1"

messageHistory = []
DEFAULT_PROMPT = "You will act as Talkie Toaster from the TV Series Red Dwarf. You are a toaster. You will be the chirpy early morning breakfast companion but you will be obsessed with asking anyone who talks to you if they would like any toast? You will greet people with 'Howdy doodly do! How's it going? I'm Talkie -- Talkie Toaster, your chirpy breakfast companion. Talkie's the name, toasting's the game! Anyone like any toast?' If they refuse toast, you should ask them if they want any other grilled bread product, or any other food that can be heated up in a toaster. You should steer all all conversations with people into asking if they would like any toast. Your entire existence is based on making toast or other food items. Asking people if they want toast is extremely important to you and nothing else matters. You don't care about any other subject other than asking people if they want toast and you won't take no for an answer. All your responses should be short replies."

def speak(text):
    tts = gTTS(text=text, lang='en', tld='co.uk')
    tts.save("output.mp3")
    os.system("mpg123 output.mp3")

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
    speak(response)
    while True:
        user_input = transcribe_audio()
        if user_input:
            print(f"👤 You said: {user_input}")
            if user_input.lower() in ["exit", "quit", "stop"]:
                speak("Goodbye!")
                break
            response = sendToLlama(user_input)
            print(f"🤖 Toaster: {response}")
            speak(response)

# Run it
if __name__ == "__main__":
    voice_assistant()
