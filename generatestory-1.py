import os
import requests
from google.cloud import texttospeech, speech_v1p1beta1 as speech
from pydub import AudioSegment
from pydub.playback import play
import io
import pyaudio
import wave

# Path to your service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "storyteller-429005-67c86f0cca5a.json"

# Function to speak a prompt using Google Cloud Text-to-Speech
def speak_prompt(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F",
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

# Function to capture speech and convert to text using Google Cloud Speech-to-Text
def capture_speech():
    client = speech.SpeechClient()

    # Set up audio recording
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    rate = 16000  # Record at 16000 samples per second

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print("Listening...")
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []  # Initialize array to store frames

    # Store data in chunks for 5 seconds
    for i in range(0, int(rate / chunk * 5)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    wf = wave.open("output.wav", "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Load the recorded audio
    with io.open("output.wav", "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    try:
        text = response.results[0].alternatives[0].transcript
        print(f"Captured Speech: {text}")
        return text
    except IndexError:
        print("Sorry, I could not understand the audio.")
        return capture_speech()

# (Other functions remain the same, omitted for brevity)

if __name__ == "__main__":
    main()