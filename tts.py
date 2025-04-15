import pyttsx3

def text_to_speech(text):
    # Initialize the TTS engine
    engine = pyttsx3.init()

    # Set properties (optional)
    engine.setProperty('rate', 150)  # Speed of speech (words per minute)
    engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)

    # Use espeak-ng as the TTS engine
    engine.setProperty('voice', 'english')  # You can change the voice/language

    # Convert text to speech
    engine.say(text)
    engine.runAndWait()

# Example usage
if __name__ == "__main__":
    text = "Hello, how are you? I am Talkie Toaster, your chirpy breakfast companion. Would you like some toast?"
    text_to_speech(text)