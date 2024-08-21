import os
import json
import requests
import PyPDF2
from fpdf import FPDF

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config['api_key']
pdf_path = config['pdf_path']  # Path to the existing transcript PDF file
output_format = config.get('output_format', 'plain')  # Default to plain text if not specified

api_url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Function to read text from a PDF file
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

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
            prompt = f"Please identify any recurring themes, trends, or patterns in the conversation. Highlight the most important points that were subtly mentioned or implied but not explicitly discussed. Please also extract any critical insights that may have been overshadowed by the main discussion. Focus on subtle cues, concerns, or opportunities that were mentioned briefly but could have a significant impact. Here is the transcription:\n\n{text_chunk}"
        elif prompt_number == 3:
            prompt = f"Please provide a summarized thank-you email (no more than 3 paragraphs) based on the topics discussed. Here is the transcription:\n\n{text_chunk}"

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,  # Adjust as needed
        "temperature": 0.5
    }
    
    return send_request_with_retries(api_url, headers, data)

# Function to save the summary based on the selected format
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
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.output(filename)
        return filename  # Return early, since we've already saved the PDF
    
    # Save as plain text or markdown (Markdown can be plain text with formatting)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    
    return filename

# Main function to process the existing transcript PDF
def main():
    try:
        # Read the PDF and extract the transcription
        transcription_text = read_pdf(pdf_path)
        print("Transcription extracted from PDF:\n", transcription_text)

        # Split the transcription into chunks
        transcription_chunks = split_transcription(transcription_text)  # Adjust chunk size if necessary

        # Prompt user for summary type
        print("Choose the format for the summary:")
        print("1. Meeting/Call")
        print("2. Interview")
        choice = input("Enter the number corresponding to your choice: ")
        summary_type = "Meeting/Call" if choice == "1" else "Interview"

        # Base file names
        summary_base = os.path.join(os.path.dirname(pdf_path), "summary")

        # Generate summaries in sequence based on the user's choice
        summaries = []
        
        if summary_type == "Meeting/Call":
            combined_text = " ".join(transcription_chunks)  # Combine all chunks into one text
            summary_1 = generate_summary(combined_text, summary_type, 1)
            summary_2 = generate_summary(combined_text, summary_type, 2)
            summaries.append(summary_1)
            summaries.append(summary_2)
        elif summary_type == "Interview":
            combined_text = " ".join(transcription_chunks)  # Combine all chunks into one text
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

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
