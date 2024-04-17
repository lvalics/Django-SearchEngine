from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import PyPDF2
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
import pdfplumber


# Create a function to extract text
def text_extraction(element):
    # Extracting the text from the in-line text element
    line_text = element.get_text()

    # Find the formats of the text
    # Initialize the list with all the formats that appeared in the line of text
    line_formats = []
    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            # Iterating through each character in the line of text
            for character in text_line:
                if isinstance(character, LTChar):
                    # Append the font name of the character
                    line_formats.append(character.fontname)
                    # Append the font size of the character
                    line_formats.append(character.size)
    # Find the unique font sizes and names in the line
    format_per_line = list(set(line_formats))

    # Return a tuple with the text in each line along with its format
    return (line_text, format_per_line)


# Create a function to crop the image elements from PDFs
def crop_image(element, pageObj):
    # Get the coordinates to crop the image from the PDF
    [image_left, image_top, image_right, image_bottom] = [
        element.x0,
        element.y0,
        element.x1,
        element.y1,
    ]
    # Crop the page using coordinates (left, bottom, right, top)
    pageObj.mediabox.lower_left = (image_left, image_bottom)
    pageObj.mediabox.upper_right = (image_right, image_top)
    # Save the cropped page to a new PDF
    cropped_pdf_writer = PyPDF2.PdfWriter()
    cropped_pdf_writer.add_page(pageObj)
    # Save the cropped PDF to a new file
    with open(
        "cropped_image.pdf", "wb"
    ) as cropped_pdf_file:  # todo rename to random filename
        cropped_pdf_writer.write(cropped_pdf_file)


# Create a function to convert the PDF to images
def convert_to_images(
    input_file,
):
    images = convert_from_path(input_file)
    image = images[0]
    output_file = "PDF_image.png"  # todo rename to random filename
    image.save(output_file, "PNG")


# Create a function to read text from images
def image_to_text(image_path):
    # Read the image
    img = Image.open(image_path)
    # Extract the text from the image
    text = pytesseract.image_to_string(img)
    return text


# Extracting tables from the page
def extract_table(pdf_path, page_num, table_num):
    # Open the pdf file
    pdf = pdfplumber.open(pdf_path)
    # Find the examined page
    table_page = pdf.pages[page_num]
    # Extract the appropriate table
    table = table_page.extract_tables()[table_num]
    return table


# Convert table into the appropriate format
def table_converter(table):
    table_string = ""
    # Iterate through each row of the table
    for row_num in range(len(table)):
        row = table[row_num]
        # Remove the line breaker from the wrapped texts
        cleaned_row = [
            (
                item.replace("\n", " ")
                if item is not None and "\n" in item
                else "None" if item is None else item
            )
            for item in row
        ]
        # Convert the table into a string
        table_string += "|" + "|".join(cleaned_row) + "|" + "\n"
    # Removing the last line break
    table_string = table_string[:-1]
    return table_string
