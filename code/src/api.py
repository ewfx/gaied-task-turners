from flask import Flask, request, jsonify
import os
import json
import logging
from dotenv import load_dotenv
import email
from email import policy
import PyPDF2
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Email Processing Functions (from main.txt and email_processor.txt)
def read_email_from_file(file_path):
    """Reads an email from an .eml file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f, policy=policy.default)
        return msg
    except Exception as e:
        logging.error(f"Error reading email from {file_path}: {e}")
        return None

def get_email_body(msg):
    """Extracts the email's text body."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()

def get_email_details(msg):
    """Gets sender, subject, and body."""
    sender = msg['from']
    subject = msg['subject']
    body = get_email_body(msg)
    return sender, subject, body

def get_email_attachments(msg, output_dir="C:/Users/TaskTurners/Downloads/TaskTurners/data/Attachment/"):
    """Extracts and saves attachments."""
    attachments = list()
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename:
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(filepath)
    return attachments

# Attachment Extraction Functions (from document_parser.txt)
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                try:
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "
                    else:
                        logging.warning(f"No text from page {page_num + 1} in {pdf_path}")
                except Exception as e:
                    logging.error(f"Error extracting from page {page_num + 1} in {pdf_path}: {e}")
            return text.strip()
    except FileNotFoundError:
        logging.error(f"PDF not found: {pdf_path}")
        return None
    except PyPDF2.errors.PdfReadError as e:
        logging.error(f"Error reading PDF: {pdf_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {pdf_path}: {e}")
        return None

def extract_text_from_docx(docx_path):
    """Extracts text from a DOCX."""
    try:
        text = docx2txt.process(docx_path)
        return text
    except FileNotFoundError:
        logging.error(f"DOCX not found: {docx_path}")
        return None
    except Exception as e:
        logging.error(f"Error extracting from DOCX {docx_path}: {e}")
        return None

# Gemini API Interaction Functions (from main.txt and llm_handler.txt)
def classify_email(email_text, request_types):
    """Classifies an email using the Gemini API."""
    model = genai.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"""Classify this email into one of the following types: {request_types}.
    Provide the request type, sub-request type, reasoning, and a confidence score (0-1).
    Email: {email_text}"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error classifying email: {e}")
        return None

def extract_data(email_text, request_type):
    """Extracts data from an email based on request type using Gemini API."""
    model = genai.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"""Extract the following fields from this email related to {request_type}.
    If a field is not present, return 'N/A'.
    Fields: Deal Name, Amount, Expiration Date.
    Email: {email_text}"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error extracting data: {e}")
        return None

def detect_primary_intent(email_text):
    """Detects the primary intent of an email using Gemini API."""
    model = genai.GenerativeModel('models/gemini-1.5-pro')
    prompt = f"What is the primary intent of this email: {email_text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error detecting primary intent: {e}")
        return None

# Duplicate Detection Function (from main.txt and duplicate_detector.txt)
def detect_duplicate_emails(email_list):
    """Detects duplicate emails using TF-IDF and cosine similarity."""
    if len(email_list) < 2:
        return# Return an empty list if there are fewer than 2 emails

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(email_list)
    cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    duplicates = list()
    for i in range(len(email_list)):
        for j in range(i + 1, len(email_list)):
            if cosine_sim_matrix[i][j] > 0.8:  # Adjust threshold as needed
                duplicates.append((i, j, "High text similarity"))
    return duplicates

# API Endpoints
@app.route('/process_email', methods=['POST'])
def process_email_route():
    """
    API endpoint to process a single email.
    Receives an email file, processes it, and returns the extracted information.
    """
    if 'email_file' not in request.files:
        return jsonify({'error': 'No email file provided'}), 400

    email_file = request.files['email_file']
    email_path = "temp_email.eml"  # Save the file temporarily
    email_file.save(email_path)

    request_types = ["Adjustment", "Fee Payment", "AU Transfer",
                     "Money Movement-Outbound", "Commitment Change",
                     "Money Movement-Inbound", "Closing Notice"]  # Define your request types

    try:
        result = process_email(email_path, request_types)
        os.remove(email_path)  # Remove the temporary file
        if result:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Email processing failed'}), 500
    except Exception as e:
        logging.error(f"Error processing email: {e}")
        return jsonify({'error': f'Email processing failed: {str(e)}'}), 500

@app.route('/detect_duplicates', methods=['POST'])
def detect_duplicates_route():
    """
    API endpoint to detect duplicate emails.
    Receives a list of email texts and returns the duplicate email pairs.
    """
    email_texts = request.json.get('email_texts')
    if not email_texts:
        return jsonify({'error': 'No email texts provided'}), 400

    try:
        duplicates = detect_duplicate_emails(email_texts)
        if duplicates:
            duplicate_output = {
                "duplicate_emails_detected": True,
                "duplicates": [{"email1_index": i, "email2_index": j, "reason": reason}
                               for i, j, reason in duplicates]
            }
        else:
            duplicate_output = {
                "duplicate_emails_detected": False,
                "duplicates": list()
            }
        return jsonify(duplicate_output), 200
    except Exception as e:
        logging.error(f"Error detecting duplicates: {e}")
        return jsonify({'error': f'Error detecting duplicates: {str(e)}'}), 500

# Main function to process email (from main.txt, with modifications)
def process_email(email_path, request_types):
    """Processes a single email and its attachments."""
    try:
        msg = read_email_from_file(email_path)
        if not msg:
            return None

        sender, subject, body = get_email_details(msg)
        attachments = get_email_attachments(msg)

        email_text = body
        for attachment in attachments:
            if attachment.endswith(".pdf"):
                email_text += " " + extract_text_from_pdf(attachment)
            elif attachment.endswith(".docx"):
                email_text += " " + extract_text_from_docx(attachment)

        classification_result = classify_email(email_text, request_types)
        if not classification_result:
            return None

        primary_intent = detect_primary_intent(email_text)
        # Assuming classification_result directly contains the request type
        request_type = classification_result
        extraction_result = extract_data(email_text, request_type)

        return {
            "sender": sender,
            "subject": subject,
            "classification": classification_result,
            "primary_intent": primary_intent,
            "extracted_data": extraction_result,
            "email_text": email_text,
        }
    except Exception as e:
        logging.error(f"Error in process_email: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)