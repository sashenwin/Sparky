import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io

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

# Function to generate text using the Gemini API
def generate_text(prompt_text, api_key):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
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
    print(f"API Response: {response_json}")  # Debugging line to print the full API response

    try:
        # Try to extract the text based on the expected response structure
        text = response_json['candidates'][0]['content']['parts'][0]['text']
        return text
    except (KeyError, IndexError) as e:
        print(f"Error extracting text: {e}")
        return ""

# Function to convert text to speech and play it
def play_story(story_text):
    tts = gTTS(text=story_text, lang='en')
    audio_io = io.BytesIO()
    tts.write_to_fp(audio_io)
    audio_io.seek(0)
    audio = AudioSegment.from_mp3(audio_io)
    play(audio)

# Function to extract options from the generated text
def extract_options(options_text):
    options = options_text.split("1. ")[1].split(" 2. ")
    option1 = options[0].strip()
    options = options[1].split(" 3. ")
    option2 = options[0].strip()
    option3 = options[1].strip()
    return option1, option2, option3

# Main execution
def main():
    # Step 1: Speak the initial prompt
    speak_prompt("Hi! I'm Wally. What would you like to hear a story about?")
    
    # Step 2: Capture user input via microphone
    user_input = capture_speech()
    
    if user_input:
        # Step 3: Generate the initial part of the story and provide options
        api_key = "AIzaSyDz5jzw8dSz7EEaMfK_T45FZsaNsilTnz4"  # Replace with your API key
        story_text = generate_text(f"Generate a fun and interactive children's story of about 50 words about {user_input}. At the end, provide three options to continue the story: 1. Option 1, 2. Option 2, 3. Option 3.", api_key)
        
        if story_text:
            # Optionally trim the story to about 50 words
            story_text = ' '.join(story_text.split()[:50])
            
            # Convert the generated story to speech and play it
            play_story(story_text)
            
            # Generate the question and options for the next part of the story
            options_prompt = f"The story so far: {story_text}. Ask a question and suggest three possible continuations for the story."
            options_text = generate_text(options_prompt, api_key)
            
            if options_text:
                # Speak the options
                speak_prompt(options_text)
                
                # Capture user choice for story continuation
                user_choice = capture_speech().lower()
                option1, option2, option3 = extract_options(options_text)
                
                if "one" in user_choice or "1" in user_choice:
                    continuation_choice = option1
                elif "two" in user_choice or "2" in user_choice:
                    continuation_choice = option2
                elif "three" in user_choice or "3" in user_choice:
                    continuation_choice = option3
                else:
                    continuation_choice = ""
                
                if continuation_choice:
                    # Generate the next part of the story based on user choice
                    continuation_prompt = f"Continue the story with the following choice: {continuation_choice}"
                    story_continuation = generate_text(continuation_prompt, api_key)
                    if story_continuation:
                        # Optionally trim the continuation to about 100 words
                        story_continuation = ' '.join(story_continuation.split()[:100])
                        
                        # Convert the continuation to speech and play it
                        play_story(story_continuation)
                    else:
                        print("No continuation text received.")
                else:
                    print("No valid choice received.")
            else:
                print("No options text received.")
        else:
            print("No story text received.")
    else:
        print("No input received.")

if __name__ == "__main__":
    main()