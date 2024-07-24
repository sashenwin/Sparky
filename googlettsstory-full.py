import os
import requests
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
import threading
import io
from AppKit import NSSound

# Path to your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "storyteller-429005-67c86f0cca5a.json"

# Path to your background music file
BACKGROUND_MUSIC_PATH = 'background2.mp3'
BACKGROUND_MUSIC_VOLUME_DB = -30  # Volume adjustment in decibels (negative to reduce volume)

# Function to speak a prompt using Google Cloud Text-to-Speech
def speak_prompt(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F",  # Updated to use en-US-Journey-F
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    audio_io = io.BytesIO(response.audio_content)
    audio = AudioSegment.from_mp3(audio_io)
    play(audio)

# Function to capture speech and convert to text
def capture_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    sound = NSSound.soundNamed_("Glass")
    sound.play()

    print("Listening...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Convert speech to text
        text = recognizer.recognize_google(audio)
        print(f"Captured Speech: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        speak_prompt("Sorry, I couldn't catch that. Please say it again!")
        return capture_speech()
    except sr.RequestError:
        print("Sorry, there was an issue with the speech recognition service.")
        speak_prompt("Sorry, There was an issue. Please say it again!")
        return capture_speech()

# Function to generate a story using the Gemini API
def generate_story(prompt_text, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    speak_prompt(f"Alrighto! I will tell you a magical story about {prompt_text}. Are you ready? Here we gooooo")
    # Modify the payload to request a story of approximately 50 words
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Generate a fun, interactive children story of about 50 words about {prompt_text}. In the end, ask me how I want to continue the story by giving me 3 word options"}
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(f"{api_url}?key={api_key}", json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()  # Check if the request was successful

    response_json = response.json()
    try:
        story_text = response_json['candidates'][0]['content']['parts'][0]['text']
        return story_text
    except (KeyError, IndexError) as e:
        print(f"Error extracting story text: {e}")
        return ""

def continue_story(prompt_text, ongoing_story, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    # Include the ongoing story and prompt text in the payload
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{ongoing_story} Continue this fun, interactive children story with the option {prompt_text}. In the end, ask me again how I want to continue the story by giving me 3 word options."}
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(f"{api_url}?key={api_key}", json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()  # Check if the request was successful

    response_json = response.json()
    try:
        story_text = response_json['candidates'][0]['content']['parts'][0]['text']
        return story_text
    except (KeyError, IndexError) as e:
        print(f"Error extracting story text: {e}")
        return ""       

def end_story(prompt_text, ongoing_story, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    # Include the ongoing story and prompt text in the payload
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{ongoing_story} Finish this fun, interactive children story with a happy ending with option {prompt_text}"}
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(f"{api_url}?key={api_key}", json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()  # Check if the request was successful

    response_json = response.json()
    try:
        story_text = response_json['candidates'][0]['content']['parts'][0]['text']
        return story_text
    except (KeyError, IndexError) as e:
        print(f"Error extracting story text: {e}")
        return ""

# Function to convert text to speech and play it
def play_story(story_text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=story_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F",  # Updated to use en-US-Journey-F
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    audio_io = io.BytesIO(response.audio_content)
    audio = AudioSegment.from_mp3(audio_io)
    play(audio)

# Function to play background music with adjusted volume
def play_background_music():
    music = AudioSegment.from_mp3(BACKGROUND_MUSIC_PATH)
    music = music + BACKGROUND_MUSIC_VOLUME_DB  # Adjust volume
    play(music)    

# Main execution
import threading

def main():
    # Start background music in a separate thread
    music_thread = threading.Thread(target=play_background_music, daemon=True)
    music_thread.start()

    # Speak the initial prompt
    speak_prompt("Hey! It's Sparky here. I'm here to tell you amaaaaaazing stories. What shall the story be about today? Tell me right after the beep")

    def tell_story():
        
        # Capture user input via microphone
        user_input = capture_speech()
        
        if user_input:
            # Replace with your API key
            api_key = "AIzaSyDz5jzw8dSz7EEaMfK_T45FZsaNsilTnz4"
            full_story = ""
            
            # Step 1: Generate the initial story
            story_text = generate_story(user_input, api_key)
            
            if story_text:
                full_story += " " + story_text
                play_story(story_text)
                
                # Step 2: Capture user input for continuing the story
                speak_prompt("Tell me what do you think it should do?")
                user_input = capture_speech()
                
                if user_input:
                    # Continue the story based on the user's choice
                    story_text = continue_story(user_input, full_story, api_key)
                    
                    if story_text:
                        full_story += " " + story_text
                        play_story(story_text)
                        
                        # Step 3: Capture user input for ending the story
                        speak_prompt("Tell me what do you think it should do?")
                        user_input = capture_speech()
                        
                        if user_input:
                            # End the story based on the user's choice
                            story_text = end_story(user_input, full_story, api_key)
                            
                            if story_text:
                                play_story(story_text)
                            else:
                                print("No ending story text received.")
                        else:
                            print("No input received for ending the story.")
                    else:
                        print("No continued story text received.")
                else:
                    print("No input received for continuing the story.")
            else:
                print("No initial story text received.")
        else:
            print("No initial input received.")

    # Initial story
    tell_story()

    while True:
        # Ask if the user wants to hear another story
        speak_prompt("Do you wanna hear another story?")
        user_input = capture_speech()
        
        if user_input:
            if "yes" in user_input.lower():
                speak_prompt("What do you want to hear a story about?")
                tell_story()
            elif "no" in user_input.lower():
                speak_prompt("Bye bye for now. Come back for more fun stories!")
                b