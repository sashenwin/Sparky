import os
import requests
import speech_recognition as sr
from google.cloud import texttospeech
import pyaudio
import wave
from google.cloud import speech
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


def record_audio(file_path, record_seconds=10, sample_rate=16000):
    chunk = 1024  # Record in chunks of 1024 samples
    format = pyaudio.paInt16  # 16 bits per sample
    channels = 1  # Mono
    rate = sample_rate

    # Play the beep sound before starting the recording
    sound = AudioSegment.from_mp3('beep.mp3')
    play(sound)

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    print("Recording...")

    frames = []

    for i in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    wf = wave.open(file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def capture_speech():
    client = speech.SpeechClient()

    while True:
        # Record audio and save to a file with a timeout
        audio_file = "recorded_audio.wav"
        record_audio(audio_file, record_seconds=10)  # Adjust the recording duration as needed

        with io.open(audio_file, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        print("Recognizing speech...")
        try:
            response = client.recognize(config=config, audio=audio)
            for result in response.results:
                text = result.alternatives[0].transcript
                if text.strip():  # Check if text is not empty
                    print(f"Captured Speech: {text}")
                    return text
                else:
                    print("No speech detected, trying again.")
                    speak_prompt("Sorry, I couldn't hear you. Can you say it again?")
        except Exception as e:
            print(f"Error: {e}")
            speak_prompt("Sorry, I couldn't catch that. Please say it again!")

# Function to generate a story using the Gemini API
def generate_story(prompt_text, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    speak_prompt(f"Alrighto! I will tell you a magical story about {prompt_text}. Are you ready? Here we gooooo")
    # Modify the payload to request a story of approximately 50 words
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Generate a fun, interactive children story of about 50 words about {prompt_text}. In the end, ask me how I want to continue the story by giving me 3 word options. It can't have * marks"}
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
                    {"text": f"{ongoing_story} Continue this fun, interactive children story with another 50 words with the option {prompt_text}. In the end, ask me again how I want to continue the story by giving me 3 word options. It can't have * marks"}
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
                    {"text": f"{ongoing_story} Finish this fun, interactive children story with another 50 words with a happy ending with option {prompt_text}"}
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
    while True:
        play(music) 

# Main execution
import threading

def main():
    # Start background music in a separate thread
    music_thread = threading.Thread(target=play_background_music, daemon=True)
    music_thread.start()

    # Speak the initial prompt
    speak_prompt("Hello there! It's Sparky here. I'm here to tell you amaaaaaazing stories. What is your name buddy? Say it after the beep.")
    name = capture_speech()
    speak_prompt(f"Nice to meet you {name}. Now, what magical tale or incredible adventure do you want to hear? Think of something and tell me right after the beep")


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
                speak_prompt("Tell me what do you think it should do after the beep?")
                user_input = capture_speech()
                speak_prompt("Gotcha!")
                
                if user_input:
                    # Continue the story based on the user's choice
                    story_text = continue_story(user_input, full_story, api_key)
                    
                    if story_text:
                        full_story += " " + story_text
                        play_story(story_text)
                        
                        # Step 3: Capture user input for ending the story
                        speak_prompt("Tell me what do you think it should do after the beep?")
                        user_input = capture_speech()
                        speak_prompt("Gotcha!")
                        
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
                break
            else:
                speak_prompt("I didn't quite get that. Do you wanna hear another story?")
        else:
            print("No input received for another story prompt.")

if __name__ == "__main__":
    main()