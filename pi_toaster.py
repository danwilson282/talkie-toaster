import speech_recognition as sr
import pyttsx3
import requests
import json
from gtts import gTTS
import os
messageHistory = []
def speak(text):
    tts = gTTS(text=text, lang='en')
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
    speak("Hi! How can I help you today?")
    while True:
        user_input = transcribe_audio()
        if user_input:
            print(f"👤 You said: {user_input}")
            if user_input.lower() in ["exit", "quit", "stop"]:
                speak("Goodbye!")
                break
            response = sendToLlama(user_input)
            print(f"🤖 Ollama: {response}")
            speak(response)

# Run it
if __name__ == "__main__":
    voice_assistant()
