import PyPDF2
import docx2txt
import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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