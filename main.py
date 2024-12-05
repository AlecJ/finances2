# read in pdf file
from PyPDF2 import PdfReader

# Load the PDF file
reader = PdfReader("example.pdf")

# Extract text from each page
for page in reader.pages:
    print(page.extract_text())
