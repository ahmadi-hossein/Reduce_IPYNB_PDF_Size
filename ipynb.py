import streamlit as st
import nbformat
from io import StringIO
import base64
from PIL import Image
from io import BytesIO
import json

# Function to reduce the size of an IPython notebook
def reduce_ipynb_size(uploaded_file):
    # Read the notebook file
    notebook = nbformat.read(uploaded_file, as_version=4)

    # To convert images to base64 with minimal formatting
    def image_to_base64(img_data):
        # Check if image data is a base64 string, if so, decode it
        if isinstance(img_data, str):
            # If the data is in the "data:image/png;base64," format, remove the prefix
            if img_data.startswith("data:image/png;base64,"):
                img_data = img_data.split(",")[1]
            try:
                img_data = base64.b64decode(img_data)
            except Exception as e:
                print(f"Error decoding base64 image: {e}")
                return None

        # Re-encode the image to base64 with minimal formatting
        buffered = BytesIO()
        Image.open(BytesIO(img_data)).save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8").replace("\n", "")

    # Process each cell
    for cell in notebook.cells:
        # Remove empty cells
        if cell.source.strip() == "":
            continue

        # Handle outputs
        if 'outputs' in cell:
            filtered_outputs = []
            for output in cell['outputs']:
                # Handle display_data and execute_result outputs
                if output.output_type in ['display_data', 'execute_result']:
                    if 'data' in output and 'image/png' in output.data:
                        # Convert images to base64
                        base64_image = image_to_base64(output.data['image/png'])
                        if base64_image:
                            output.data['image/png'] = f"data:image/png;base64,{base64_image}"
                    elif 'data' in output and 'text/plain' in output.data:
                        # Keep only text/plain representation
                        output.data = {'text/plain': output.data['text/plain']}
                    filtered_outputs.append(output)

                # Handle stream outputs
                elif output.output_type == 'stream':
                    if 'text' in output and len(output.text) > 10000:  # Truncate large text outputs
                        output.text = output.text[:10000] + "\n... [Output truncated]"
                    filtered_outputs.append(output)

                # Handle error outputs
                elif output.output_type == 'error':
                    if 'traceback' in output and len(output.traceback) > 10000:  # Truncate large traceback
                        output.traceback = output.traceback[:10000] + ["... [Traceback truncated]"]
                    filtered_outputs.append(output)

            # Update the cell with the filtered outputs
            cell['outputs'] = filtered_outputs

    # Save the reduced notebook to a string buffer with compact JSON formatting
    output = StringIO()
    json.dump(notebook, output, separators=(',', ':'))  # Compact JSON
    return output.getvalue()

# Streamlit app layout
st.title("IPYNB File Size Reducer by Hossein Ahmadi")
st.write("Upload a Jupyter Notebook (.ipynb) file to reduce its size without removing outputs, metadata, or images.")

# File uploader widget
uploaded_file = st.file_uploader("Choose a .ipynb file", type="ipynb")

# Check if a file is uploaded
if uploaded_file is not None:
    # Reduce the size of the uploaded notebook
    reduced_ipynb = reduce_ipynb_size(uploaded_file)

    # Provide the download button for the reduced file
    st.download_button(
        label="Download Reduced File",
        data=reduced_ipynb,
        file_name="reduced_notebook.ipynb",
        mime="application/octet-stream"
    )