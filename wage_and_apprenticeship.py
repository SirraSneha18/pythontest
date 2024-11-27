import fitz  # PyMuPDF

def extract_pages(file_path):
    """
    Extract pages from a PDF and return a dictionary with page numbers and their text content.
    """
    document = fitz.open(file_path)
    image_reply_pairs = {}

    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text()
        image_reply_pairs[f"page_{page_num + 1}"] = text

    return image_reply_pairs
