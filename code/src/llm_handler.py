import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

load_dotenv()  # Load .env file
#GOOGLE_API_KEY=AIzaSyBYdyPDdqP34b0Q4blSZJxbNcExdxXWV9s
google_api_key = os.getenv("GOOGLE_API_KEY")  # Get your Google API key

def classify_email(email_text, request_types):
    """Classifies an email using Gemini."""
    chat = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=google_api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant classifying emails."),
        ("user", f"""Classify this email into one of the following types: {", ".join(request_types)}.
        Provide the request type, sub-request type, reasoning, and a confidence score (0-1).
        Email: {email_text}""")
    ])
    messages = prompt.format_messages(request_types=request_types, email_text=email_text)
    try:
        response = chat.invoke(messages)
        return response.content
    except Exception as e:
        print(f"Error classifying email: {e}")
        return None

def extract_data(email_text, request_type):
    """Extracts data from an email based on request type using Gemini."""
    chat = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=google_api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant extracting data from emails."),
        ("user", f"""Extract the following fields from this email related to {request_type}.
        If a field is not present, return 'N/A'.
        Fields: Deal Name, Amount, Expiration Date.
        Email: {email_text}""")
    ])
    messages = prompt.format_messages(request_type=request_type, email_text=email_text)
    try:
        response = chat.invoke(messages)
        return response.content
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None

def detect_primary_intent(email_text):
    """Detects the primary intent of an email using Gemini."""
    chat = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro", google_api_key=google_api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant determining the primary intent of an email."),
        ("user", f"What is the primary intent of this email: {email_text}""")
    ])
    messages = prompt.format_messages(email_text=email_text)
    try:
        response = chat.invoke(messages)
        return response.content
    except Exception as e:
        print(f"Error detecting primary intent: {e}")
        return None