# Audio Transcription and Summarization with OpenAI API

This Python script allows you to transcribe audio files and generate contextual summaries (e.g., for meetings, phone calls, or interviews) using OpenAI's Whisper and GPT-4 models. The results can be exported in various formats (`.txt`, `.md`, or `.pdf`) and automatically emailed using Gmail.

## Features

- **Audio Transcription**: Transcribe audio files using OpenAI's Whisper Model.
- **Contextual Summarization**: Generate detailed summaries for meetings, phone calls, or interviews based on user input using OpenAI's GPT 4o
- **Multi-Format Export**: Save transcriptions and summaries as `.txt`, `.md`, or `.pdf`.
- **Email Integration**: Automatically email the transcription and summary files as attachments.
- **Parallel Processing**: Speed up transcription by processing audio chunks concurrently.
- **Error Handling**: Robust error handling with retry logic for API requests.

## Installation 

1. ***Clone the Repository***
   ```bash
   git clone https://github.com/holmesha/GPT-Meeting-Summary.git
   cd GPT-Meeting-Summary
   ```
2. ***Install Python Dependencies***
    - Install the Python dependencies from the requirements.txt file
      ```bash
      pip install -r requirements.txt
      ```
3. ***Edit config.json File***
    - Add your OpenAI key, path to audio file, name of audio file, the output format you want (options are: `.pdf`, `.md` or `.txt`), the email of your recipient and your own email info.
    - I recommend setting an app specific email password - I personally used Gmail, which allowed me to generate an app-specific password (instructions [here](https://support.google.com/accounts/answer/185833?hl=en)).

4. ***Install ffmpeg for Audio Processing***
   - Next, install ffmpeg for audio processing. Use the following commands depending on your operating system:
	•	macOS: brew install ffmpeg
	•	Ubuntu: sudo apt install ffmpeg
	•	Windows: Download from [ffmpeg.org](https://ffmpeg.org/).

**Once everything is set up you can start the script by running:**
    ```
    python main.py
    ```


**Contributions are welcome! If you have suggestions for improvements or new features/prompt ideas/etc, feel free to submit a pull request or open an issue.**
