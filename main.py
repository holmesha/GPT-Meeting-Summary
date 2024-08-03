audio_file = "<<INSERT FILE PATH>>" #must be in a .m4a format
api_key = '<<INSERT CHAT GPT API KEY>>'


import openai
import speech_recognition as sr
from pydub import AudioSegment
import os
import asyncio

# Define the paths as variables
input_audio_file_path = audio_file
output_audio_file_path = "output.wav"

# Convert m4a to wav
audio = AudioSegment.from_file(input_audio_file_path, format="m4a")
audio.export(output_audio_file_path, format="wav")

# Initialize recognizer
recognizer = sr.Recognizer()

# Load the converted audio file
with sr.AudioFile(output_audio_file_path) as source:
    audio_data = recognizer.record(source)

# Transcribe the audio
try:
    transcription = recognizer.recognize_google(audio_data)
    print("Transcription:\n", transcription)
    
    # Save transcription to a text file
    transcription_file_path = "transcription.txt"
    with open(transcription_file_path, "w") as file:
        file.write(transcription)
    
    print(f"Transcription saved to {transcription_file_path}")
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand the audio")
except sr.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")

# Clean up the temporary wav file
os.remove(output_audio_file_path)

# Set up OpenAI API client
openai.api_key = api_key

# Prompt to summarize the transcription
summary_prompt = f"""
Here is the transcription of an audio recording:

{transcription}

Please provide a concise, nicely formatted summary of the main points discussed in the transcription.
"""

# Async function to create completion
async def create_summary():
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=openai.api_key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": summary_prompt}
        ]
    )
    return response

# Run the async function
response = asyncio.run(create_summary())

# Print the nicely formatted summary
summary = response.choices[0].message.content.strip()
print("Formatted Summary:\n", summary)

# Save the summary to a text file
summary_file_path = "summary.txt"
with open(summary_file_path, "w") as file:
    file.write(summary)

print(f"Formatted summary saved to {summary_file_path}")
