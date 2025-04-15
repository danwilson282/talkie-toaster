from gtts import gTTS
import os
import subprocess

def speak_annoying_male(text):
    # 1. Generate male-ish TTS (use US or Indian accent for a deeper vibe)
    tts = gTTS(text=text, lang='en', tld='co.in')  # Try 'com' or 'co.in'
    tts.save("normal.mp3")

    # 2. Convert to WAV for pitch processing
    os.system("ffmpeg -y -i normal.mp3 normal.wav")

    # 3. Lower pitch and slow it down slightly
    subprocess.run([
        "sox", "normal.wav", "bro_voice.wav",
        "pitch", "-300", "speed", "0.9"
    ])

    # 4. Play it
    subprocess.run(["aplay", "bro_voice.wav"])

speak_annoying_male("Yo bro, I'm your AI. Let's get things done, or not.")