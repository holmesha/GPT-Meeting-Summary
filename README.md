# Audio Transcription and Summarization

This project demonstrates how to transcribe audio files and generate summaries using Python. The script converts `.m4a` files to `.wav`, transcribes the audio using Google's Speech Recognition API, and summarizes the transcription using OpenAI's GPT-4o-mini model.

## Features

- Converts `.m4a` audio files to `.wav`
- Transcribes audio to text
- Generates a concise, formatted summary of the transcription

## Requirements

- Python 3.7+
- `openai` library
- `pydub` library
- `speech_recognition` library
- `ffmpeg`

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/audio-transcription-summarization.git
    cd audio-transcription-summarization
    ```

2. Install the required Python libraries:
    ```bash
    pip install openai pydub speechrecognition
    ```

3. Install `ffmpeg`:
    - macOS:
        ```bash
        brew install ffmpeg
        ```
    - Ubuntu:
        ```bash
        sudo apt-get install ffmpeg
        ```
    - Windows:
        Download and install from [FFmpeg website](https://ffmpeg.org/download.html).

## Usage

1. Set your OpenAI API key:
    ```python
    openai.api_key = 'YOUR_OPENAI_API_KEY'
    ```

2. Place your `.m4a` audio file in the project directory.

3. Update the script with the path to your audio file:
    ```python
    input_audio_file_path = "path_to_your_audio_file.m4a"
    ```

4. Run the script:
    ```bash
    main.py
    ```
