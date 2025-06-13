import fitz  # PyMuPDF
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
import io
import os

def parse_pdf(file_input):
    """
    Parses the content of a PDF file into plain text.
    
    Args:
        file_input: Either a file path (str) or a file stream (bytes/io.BytesIO)
        
    Returns:
        str: The extracted text from the PDF
    """
    all_text = []
    
    try:
        # Handle both file paths and file streams
        if isinstance(file_input, str):
            # If it's a file path, open the file
            doc = fitz.open(file_input)
        else:
            # If it's a stream, use it directly
            doc = fitz.open(stream=file_input, filetype="pdf")
        
        # Extract normal text
        for page_num, page in enumerate(doc):
            text = page.get_text()
            all_text.append(f"\n--- Page {page_num + 1} (Normal Text) ---\n{text}")
            
            # Extract text from images in the page
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():  # Only add if there's actual text
                    all_text.append(f"\n--- Page {page_num + 1} (Image {img_index + 1} OCR Text) ---\n{ocr_text}")
        
        doc.close()
        return "\n".join(all_text)
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")