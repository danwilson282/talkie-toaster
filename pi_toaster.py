import speech_recognition as sr
import pyttsx3
import requests


def speak(text):
    engine = pyttsx3.init(driverName='espeak')
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)

    # Get list of available voices and pick the first one
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[11].id)

    engine.say(text)
    engine.runAndWait()

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

def ask_ollama(prompt, model="llama3"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.RequestException as e:
        print(f"💥 Error: {e}")
        return "There was a problem communicating with the AI."

def voice_assistant():
    speak("Hi! How can I help you today?")
    # while True:
    #     user_input = transcribe_audio()
    #     if user_input:
    #         print(f"👤 You said: {user_input}")
    #         if user_input.lower() in ["exit", "quit", "stop"]:
    #             speak("Goodbye!")
    #             break
    #         response = ask_ollama(user_input)
    #         print(f"🤖 Ollama: {response}")
    #         speak(response)

# Run it
if __name__ == "__main__":
    voice_assistant()
