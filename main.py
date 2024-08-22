import os
import requests
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from tqdm import tqdm
from fpdf import FPDF

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_key']
audio_path = config['audio_path']
audio_file = config['audio_file']
output_format = config.get('output_format', 'plain')  # Default to plain text if not specified
email_recipient = config['email_recipient']
smtp_server = config['smtp_server']
smtp_port = config['smtp_port']
email_sender = config['email_sender']
email_password = config['email_password']

chunk_length_ms = 60000  # 1 minute chunks
gpt_post_process = True

api_url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Function to enhance audio
def enhance_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    enhanced_audio = audio.low_pass_filter(3000)  # Example: Remove high-frequency noise
    enhanced_file_path = file_path.replace(".wav", "_enhanced.wav")
    enhanced_audio.export(enhanced_file_path, format="wav")
    return enhanced_file_path

# Function to split audio into chunks
def split_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = f"chunk_{i}.wav"
        chunk.export(chunk_file, format="wav")
        chunk_files.append(chunk_file)
    return chunk_files

# Function to split transcription into chunks based on word count
def split_transcription(text, chunk_size=1000):
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

# Function to clean special characters for PDF
def clean_text_for_pdf(text):
    replacements = {
        '\u2019': "'",  # Right single quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        # Add more replacements if necessary
    }
    
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    return text

# Function to send a POST request with retries
def send_request_with_retries(api_url, headers, data, max_retries=3, delay=5):
    for attempt in range(max_retries):
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"Attempt {attempt + 1} failed: {response.status_code} - {response.json()}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    return None

# Function to transcribe audio using OpenAI Whisper model
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": audio_file},
            data={"model": "whisper-1"}
        )
        if response.status_code == 200:
            return response.json()['text']
        else:
            print(f"Transcription failed: {response.status_code} - {response.json()}")
            return None

# Function to transcribe audio chunks in parallel and delete chunk files after transcription
def transcribe_audio_parallel(chunk_files):
    transcriptions = []
    with ThreadPoolExecutor() as executor:
        for transcription, chunk_file in zip(executor.map(transcribe_audio, chunk_files), chunk_files):
            if transcription:
                transcriptions.append(transcription)
            # Delete the chunk file after transcription
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
                print(f"Deleted chunk file: {chunk_file}")
    return transcriptions

# Function to prompt user for summary type
def get_summary_type():
    print("Choose the format for the summary:")
    print("1. Meeting/Call")
    print("2. Interview")
    choice = input("Enter the number corresponding to your choice: ")
    
    if choice == "1":
        return "Meeting/Call"
    elif choice == "2":
        return "Interview"
    else:
        print("Invalid choice, defaulting to 'Meeting/Call'.")
        return "Meeting/Call"

# Function to generate summary based on selected prompt
def generate_summary(text_chunk, prompt_type, prompt_number):
    if prompt_type == "Meeting/Call":
        if prompt_number == 1:
            prompt = f"Please summarize the meeting with the following elements: 1. Summary by topic description (with description) and subtopic bullet points, 2. Any key decisions, 3. Any important questions raised during this meeting, 4. Any follow-up action items discussed, and 5. A general conclusion. Here is the transcription:\n\n{text_chunk}"
        elif prompt_number == 2:
            prompt = f"Please identify any recurring themes, trends, or patterns in the conversation. Highlight the most important points that were subtly mentioned or implied but not explicitly discussed. Please also extract any critical insights that may have been overshadowed by the main discussion. Focus on subtle cues, concerns, or opportunities that were mentioned briefly but could have a significant impact. Here is the transcription:\n\n{text_chunk}"
    elif prompt_type == "Interview":
        if prompt_number == 1:
            prompt = f"You are a helpful assistant and an expert interview assessor. Please summarize the key insights from this interview, highlighting any notable responses, themes, and takeaways. End with a list of questions asked, summary answers, and a general conclusion and feedback on how you think it went. Here is the transcription:\n\n{text_chunk}"
        elif prompt_number == 2:
            prompt = f"YPlease identify any recurring themes, trends, or patterns in the conversation. Highlight the most important points that were subtly mentioned or implied but not explicitly discussed. Please also extract any critical insights that may have been overshadowed by the main discussion. Focus on subtle cues, concerns, or opportunities that were mentioned briefly but could have a significant impact. Here is the transcription:\n\n{text_chunk}"
        elif prompt_number == 3:
            prompt = f"Please provide a summarized thank-you email (no more than 3 paragraphs) based on the topics discussed. Here is the transcription:\n\n{text_chunk}"

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,  # Adjust as needed
        "temperature": 0.5
    }
    
    return send_request_with_retries(api_url, headers, data)

# Function to save the transcription or summary based on the selected format
def save_output(content, base_filename, format="plain"):
    if format == "plain":
        filename = base_filename + ".txt"
    elif format == "markdown":
        filename = base_filename + ".md"
        content = content.replace("**", "")  # Clean up bolding if needed for Markdown
    elif format == "pdf":
        filename = base_filename + ".pdf"
        # Clean the content for PDF
        content = clean_text_for_pdf(content)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.output(filename)
        return filename  # Return early, since we've already saved the PDF
    
    # Save as plain text or markdown (Markdown can be plain text with formatting)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    
    return filename

# Function to send email with attachments
def send_email_with_attachment(subject, body, files):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    for file in files:
        attachment = open(file, 'rb')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file)}")
        msg.attach(part)
        attachment.close()

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_sender, email_password)
        text = msg.as_string()
        server.sendmail(email_sender, email_recipient, text)
        server.quit()
        print(f"Email sent to {email_recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Main function to run the transcription and summarization
def main():
    try:
        # Enhance the audio
        enhanced_audio_file = enhance_audio(os.path.join(audio_path, audio_file))

        # Split audio into chunks
        chunk_files = split_audio(enhanced_audio_file)

        # Transcribe each chunk in parallel
        transcriptions = transcribe_audio_parallel(chunk_files)
        full_transcription = " ".join(transcriptions)
        print("Full Transcription:\n", full_transcription)

        # Prompt user for summary type
        summary_type = get_summary_type()

        # Base file names
        transcription_base = os.path.join(audio_path, "transcription")
        summary_base = os.path.join(audio_path, "summary")

        # Save full transcription based on the selected format
        transcription_file = save_output(full_transcription, transcription_base, format=output_format)
        print(f"Full transcription saved to: {transcription_file}")

        # Optionally summarize the transcription
        if gpt_post_process:
            combined_text = full_transcription  # Use the entire transcription as one text block

            # Generate summaries in sequence based on the user's choice
            summaries = []
            
            if summary_type == "Meeting/Call":
                summary_1 = generate_summary(combined_text, summary_type, 1)
                summary_2 = generate_summary(combined_text, summary_type, 2)
                summaries.append(summary_1)
                summaries.append(summary_2)
            elif summary_type == "Interview":
                summary_1 = generate_summary(combined_text, summary_type, 1)
                summary_2 = generate_summary(combined_text, summary_type, 2)
                summary_3 = generate_summary(combined_text, summary_type, 3)
                summaries.append(summary_1)
                summaries.append(summary_2)
                summaries.append(summary_3)

            # Combine all summaries into one final summary
            final_summary = "\n\n".join(summaries)
            print("Formatted Summary:\n", final_summary)

            # Save the summary based on the selected format
            summary_file = save_output(final_summary, summary_base, format=output_format)
            print(f"Formatted summary saved to: {summary_file}")

        # Send transcription and summary via email
        send_email_with_attachment(
            "Requested Audio Transcription and Summary",
            "Please find your audio transcription and summary attached.",
            [transcription_file, summary_file]
        )

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
