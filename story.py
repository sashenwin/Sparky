from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io

# Your story text
story_text = """
Blah blah black sheep, have you any wool? Yes sir, yes sir, three bags full.
One for the master, one for the dame, and one for the little boy who lives down the lane.
"""

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