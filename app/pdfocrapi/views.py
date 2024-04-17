import os
import pdfplumber
import PyPDF2
from django.http import JsonResponse
import logging
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

# https://towardsdatascience.com/extracting-text-from-pdf-files-with-python-a-comprehensive-guide-9fc4003d517

# To analyze the PDF layout and extract text
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
from api.utils.pdfhandler import (
    text_extraction,
    crop_image,
    convert_to_images,
    image_to_text,
    extract_table,
    table_converter,
)

logger = logging.getLogger(__name__)


class OCRView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        # This is where you would handle the uploaded file and perform OCR
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded."}, status=400)

        # Execute the PDF workflow
        # Save the uploaded file to a temporary path
        temp_pdf_path = "/tmp/uploaded_file.pdf"  # Consider using a more dynamic path or handling
        with open(temp_pdf_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Execute the PDF workflow with the path of the uploaded file
        OCRView.pdfworkflow(temp_pdf_path)
        text = "PDF workflow executed. Replace this with actual output if needed."

        return Response({"extracted_text": text}, status=200)

    @staticmethod
    def pdfworkflow(pdf_path):
        logger.debug("Starting PDF workflow")


        logger.debug(f"PDF path: {pdf_path}")

        # create a PDF file object
        pdfFileObj = open(pdf_path, "rb")
        logger.debug("PDF file opened")
        # create a PDF reader object
        pdfReaded = PyPDF2.PdfReader(pdfFileObj)

        logger.debug("PDF reader object created")

        # Create the dictionary to extract text from each image
        text_per_page = {}
        logger.debug("Initialized dictionary for text per page")
        # We extract the pages from the PDF
        for pagenum, page in enumerate(extract_pages(pdf_path)):

            logger.debug(f"Processing page number: {pagenum}")

            # Initialize the variables needed for the text extraction from the page
            pageObj = pdfReaded.pages[pagenum]
            logger.debug("Initialized page object for text extraction")
            page_text = []
            line_format = []
            text_from_images = []
            text_from_tables = []
            page_content = []
            # Initialize the number of the examined tables
            table_num = 0
            first_element = True
            table_extraction_flag = False
            # Open the pdf file
            pdf = pdfplumber.open(pdf_path)
            logger.debug("Opened PDF with pdfplumber for table extraction")
            # Find the examined page
            page_tables = pdf.pages[pagenum]
            # Find the number of tables on the page
            tables = page_tables.find_tables()
            logger.debug(f"Found {len(tables)} tables on the page")
            lower_side = 0
            upper_side = 0

            # Find all the elements
            page_elements = [(element.y1, element) for element in page._objs]
            # Sort all the elements as they appear in the page
            page_elements.sort(key=lambda a: a[0], reverse=True)
            logger.debug("Sorted page elements by their y1 position")

            # Find the elements that composed a page
            for i, component in enumerate(page_elements):
                logger.debug(f"Processing component {i} of the page")
                # Extract the position of the top side of the element in the PDF
                pos = component[0]
                # Extract the element of the page layout
                element = component[1]

                # Check if the element is a text element
                if isinstance(element, LTTextContainer):
                    logger.debug("Found a text element")
                    # Check if the text appeared in a table
                    if table_extraction_flag == False:
                        # Use the function to extract the text and format for each text element
                        (line_text, format_per_line) = text_extraction(element)
                        logger.debug(f"Extracted text: {line_text}")
                        # Append the text of each line to the page text
                        page_text.append(line_text)
                        # Append the format for each line containing text
                        line_format.append(format_per_line)
                        page_content.append(line_text)
                    else:
                        # Omit the text that appeared in a table
                        logger.debug("Omitted text in a table")
                        pass

                # Check the elements for images
                if isinstance(element, LTFigure):
                    logger.debug("Found an image element")
                    # Crop the image from the PDF
                    crop_image(element, pageObj)
                    logger.debug("Cropped image from PDF")
                    # Convert the cropped pdf to an image
                    convert_to_images("cropped_image.pdf")
                    logger.debug("Converted cropped PDF to image")
                    # Extract the text from the image
                    image_text = image_to_text("PDF_image.png")
                    logger.debug(f"Extracted text from image: {image_text}")
                    text_from_images.append(image_text)
                    page_content.append(image_text)
                    # Add a placeholder in the text and format lists
                    page_text.append("image")
                    line_format.append("image")

                # Check the elements for tables
                if isinstance(element, LTRect):
                    logger.debug("Found a table element")
                    # If the first rectangular element
                    if first_element == True and (table_num + 1) <= len(tables):
                        # Find the bounding box of the table
                        lower_side = page.bbox[3] - tables[table_num].bbox[3]
                        upper_side = element.y1
                        logger.debug(f"Extracting table {table_num}")
                        # Extract the information from the table
                        table = extract_table(pdf_path, pagenum, table_num)
                        # Convert the table information in structured string format
                        table_string = table_converter(table)
                        logger.debug(f"Converted table to string: {table_string}")
                        # Append the table string into a list
                        text_from_tables.append(table_string)
                        page_content.append(table_string)
                        # Set the flag as True to avoid the content again
                        table_extraction_flag = True
                        # Make it another element
                        first_element = False
                        # Add a placeholder in the text and format lists
                        page_text.append("table")
                        line_format.append("table")

                    # Check if we already extracted the tables from the page
                    if element.y0 >= lower_side and element.y1 <= upper_side:
                        logger.debug(
                            "Element within the bounds of the extracted table, skipping"
                        )
                        pass
                    elif not isinstance(page_elements[i + 1][1], LTRect):
                        logger.debug("No more tables to extract, resetting flags")
                        table_extraction_flag = False
                        first_element = True
                        table_num += 1

            # Create the key of the dictionary
            dctkey = "Page_" + str(pagenum)
            # Add the list of list as the value of the page key
            text_per_page[dctkey] = [
                page_text,
                line_format,
                text_from_images,
                text_from_tables,
                page_content,
            ]
            logger.debug(f"Completed processing for page {pagenum}")

        # Closing the pdf file object
        pdfFileObj.close()

        logger.debug("Closed PDF file object")

        # Deleting the additional files created
        os.remove("cropped_image.pdf")
        os.remove("PDF_image.png")

        # Display the content of the page
        result = "".join(text_per_page["Page_0"][4])
        logger.debug(f"Final result: {result}")

        for pagenum, page in enumerate(extract_pages(pdf_path)):

            # Iterate the elements that composed a page
            for element in page:

                # Check if the element is a text element
                if isinstance(element, LTTextContainer):
                    # Function to extract text from the text block
                    logger.debug("Placeholder for text extraction from text block")
                    pass
                    # Function to extract text format
                    pass

                # Check the elements for images
                if isinstance(element, LTFigure):
                    # Function to convert PDF to Image
                    logger.debug("Placeholder for PDF to image conversion")
                    pass
                    # Function to extract text with OCR
                    pass

                # Check the elements for tables
                if isinstance(element, LTRect):
                    # Function to extract table
                    logger.debug("Placeholder for table extraction")
                    pass
                    # Function to convert table content into a string
                    pass

        logger.debug("PDF workflow completed")
        return JsonResponse({"message": "PDF workflow completed."}, status=200)


if __name__ == "__main__":
    OCRView.pdfworkflow()
