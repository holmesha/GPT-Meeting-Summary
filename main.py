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

# Function to transcribe audio in chunks
def transcribe_audio(path):
    transcription = ""
    audio = AudioSegment.from_wav(path)
    chunk_length_ms = 60000  # 1 minute
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    
    for i, chunk in enumerate(chunks):
        chunk.export(f"chunk{i}.wav", format="wav")
        with sr.AudioFile(f"chunk{i}.wav") as source:
            audio_data = recognizer.record(source)
            try:
                transcription += recognizer.recognize_google(audio_data) + " "
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio chunk", i)
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
        os.remove(f"chunk{i}.wav")
    return transcription

# Transcribe the audio
transcription = transcribe_audio(output_audio_file_path)

# Check if transcription was successful
if transcription:
    print("Transcription:\n", transcription)
    
    # Save transcription to a text file
    transcription_file_path = "transcription.txt"
    with open(transcription_file_path, "w") as file:
        file.write(transcription)
    
    print(f"Transcription saved to {transcription_file_path}")

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
else:
    print("Transcription was not successful. Exiting the script.")
