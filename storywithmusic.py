import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io
import threading

# Path to your background music file
BACKGROUND_MUSIC_PATH = 'background.mp3'
BACKGROUND_MUSIC_VOLUME_DB = -20  # Volume adjustment in decibels (negative to reduce volume)

# Function to speak a prompt
def speak_prompt(text):
    tts = gTTS(text=text, lang='en')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    audio_io.seek(0)
    audio = AudioSegment.from_mp3(audio_io)
    play(audio)

# Function to capture speech and convert to text
def capture_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

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
        return ""
    except sr.RequestError:
        print("Sorry, there was an issue with the speech recognition service.")
        return ""

# Function to generate a story using the Gemini API
def generate_story(prompt_text, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
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
                    {"text": f"{ongoing_story} Continue this story with the option {prompt_text}. In the end, ask me again how I want to continue the story by giving me 3 word options."}
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
                    {"text": f"{ongoing_story} Finish this story with a happy ending with option {prompt_text}"}
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

# Function to play background music with adjusted volume
def play_background_music():
    music = AudioSegment.from_mp3(BACKGROUND_MUSIC_PATH)
    music = music + BACKGROUND_MUSIC_VOLUME_DB  # Adjust volume
    play(music)

# Function to convert text to speech and play it
def play_story(story_text):
    tts = gTTS(text=story_text, lang='en')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    audio_io.seek(0)
    audio = AudioSegment.from_mp3(audio_io)
    play(audio)

# Main execution
def main():
    # Start background music in a separate thread
    music_thread = threading.Thread(target=play_background_music, daemon=True)
    music_thread.start()

    # Speak the initial prompt
    speak_prompt("Hi. I'm Wally. What do you want to hear a story about?")
    
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
            speak_prompt("Please choose one of the options to continue the story.")
            user_input = capture_speech()
            
            if user_input:
                # Continue the story based on the user's choice
                story_text = continue_story(user_input, full_story, api_key)
                
                if story_text:
                    full_story += " " + story_text
                    play_story(story_text)
                    
                    # Step 3: Capture user input for ending the story
                    speak_prompt("Please choose one of the options to finish the story.")
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

if __name__ == "__main__":
    main()