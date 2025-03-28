import streamlit as st
import fitz  # PyMuPDF for PDF manipulation
from PIL import Image
from io import BytesIO

# Function to compress the PDF by optimizing images and removing metadata
def compress_pdf(uploaded_pdf):
    # Load the original PDF into memory using PyMuPDF
    original_doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    
    # Create a new PDF document to store the optimized content
    new_doc = fitz.open()  # New empty PDF document
    
    # Iterate through each page of the original PDF
    for page_num in range(len(original_doc)):
        page = original_doc.load_page(page_num)
        
        # Get the text and images from the page
        text = page.get_text("text")  # Extract text content
        images = page.get_images(full=True)  # Extract images
        
        # Create a new page in the new PDF with the same dimensions as the original
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        
        # Add the text content to the new page
        if text:
            new_page.insert_text((50, 50), text, fontsize=12)  # Insert extracted text
        
        # Process and add compressed images to the new page
        for img_index in images:
            xref = img_index[0]  # XREF of the image
            base_image = original_doc.extract_image(xref)
            image_data = base_image["image"]

            # Open the image using PIL to reduce its size
            img = Image.open(BytesIO(image_data))

            # Resize image to 70% of original resolution
            img = img.convert("RGB")
            width, height = img.size
            new_width = int(width * 0.7)  # Resize to 70%
            new_height = int(height * 0.7)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save the image with JPEG compression at 50% quality (more aggressive)
            img_buffer = BytesIO()
            img.save(img_buffer, format="JPEG", quality=50)  # Adjust quality here
            img_buffer.seek(0)

            # Insert the compressed image into the new page
            new_page.insert_image(page.rect, stream=img_buffer.read())

    # Save the optimized PDF to a buffer
    pdf_output = BytesIO()
    new_doc.save(pdf_output, garbage=4, deflate=True, clean=True)  # Optimize the new PDF
    pdf_output.seek(0)

    return pdf_output

# Streamlit app layout
st.title("PDF File Size Reducer by Hossein Ahmadi")
st.write("Upload a PDF file to reduce its size by compressing images and optimizing the PDF structure.")

# File uploader for PDF
uploaded_pdf_file = st.file_uploader("Choose a PDF file", type="pdf")

# Process the PDF file if uploaded
if uploaded_pdf_file is not None:
    # Compress the uploaded PDF
    reduced_pdf = compress_pdf(uploaded_pdf_file)

    # Provide the download button for the reduced PDF
    st.download_button(
        label="Download Reduced PDF",
        data=reduced_pdf,
        file_name="reduced_pdf.pdf",
        mime="application/pdf"
    )
