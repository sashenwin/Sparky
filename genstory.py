import requests
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io

# Replace with your actual Gemini API key
api_key = "AIzaSyDz5jzw8dSz7EEaMfK_T45FZsaNsilTnz4"
api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

# Request payload for generating a story
payload = {
    "contents": [
        {
            "parts": [
                {"text": "Generate a short story about a magical adventure."}
            ]
        }
    ]
}

# Make the request to the Gemini API
headers = {
    "Content-Type": "application/json"
}
response = requests.post(f"{api_url}?key={api_key}", json=payload, headers=headers)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    response.raise_for_status()  # Check if the request was successful

# Extract the story text from the response
response_json = response.json()

# Print the structure to verify
print("Full API Response:", response_json)

# Extract story text based on provided response structure
try:
    story_text = response_json['candidates'][0]['content']['parts'][0]['text']
except (KeyError, IndexError) as e:
    print(f"Error extracting story text: {e}")
    story_text = ""

if not story_text.strip():
    raise ValueError("The story text is empty. Please check the API response.")

# Print the extracted story text (optional)
print("Extracted Story:\n", story_text)

# Convert the story text to speech
tts = gTTS(text=story_text, lang='en')

# Save the audio to a BytesIO object
audio_io = io.BytesIO()
tts.write_to_fp(audio_io)
audio_io.seek(0)

# Load the audio data into pydub
audio = AudioSegment.from_mp3(audio_io)

# Play the audio
play(audio)