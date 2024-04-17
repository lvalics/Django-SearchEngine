import os
import pdfplumber
import PyPDF2
from django.http import JsonResponse
import logging

logging.getLogger("pdfminer").setLevel(logging.WARNING)
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
        temp_pdf_path = (
            "/tmp/uploaded_file.pdf"  # Consider using a more dynamic path or handling
        )
        with open(temp_pdf_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Execute the PDF workflow with the path of the uploaded file
        workflow_results = OCRView.pdfworkflow(temp_pdf_path).content
        text = {workflow_results.decode("utf-8")}

        return Response({"extracted_text": text}, status=200)

    @staticmethod
    def pdfworkflow(pdf_path):
        """
        The `OCRView.pdfworkflow()` method in `app/pdfocrapi/views.py` is
        designed to process a PDF file and extract various types of content
        from it, including text, images, and tables. Here's a step-by-step
        description of what happens inside this method:

        1. **Initialization and Logging**: The method starts by logging the
        beginning of the PDF workflow and the path of the PDF file being processed.

        2. **Opening the PDF File**: It opens the PDF file using
        `PyPDF2.PdfReader` to create a PDF reader object for accessing
        the pages of the PDF.

        3. **Preparing for Content Extraction**: Initializes a dictionary
        `text_per_page` to store the extracted content from each page. It then
        iterates through each page of the PDF using `extract_pages` from `pdfminer`.

        4. **Processing Each Page**: For each page, it initializes several
        lists to hold different types of extracted content (`page_text`, `line_format`,
        `text_from_images`, `text_from_tables`, `page_content`) and flags for
        table extraction control.

        5. **Element Analysis and Extraction**:
           - **Text Extraction**: For text elements (`LTTextContainer`), it extracts
           the text and its format using the `text_extraction` function and appends
           this information to the respective lists.
           - **Image Extraction and OCR**: For image elements (`LTFigure`), it crops
           the image from the PDF, converts the cropped PDF to an image file, and then
           uses OCR (Optical Character Recognition) to extract text from the image,
           appending the results to the lists.
           - **Table Extraction**: For table elements (`LTRect`), it identifies tables,
           extracts their content using `extract_table` and `table_converter` functions,
           and appends the structured string format of the table content to the lists.

        6. **Compiling Page Content**: After processing all elements on a page,
        it compiles the extracted content into the `text_per_page` dictionary,
        keyed by page number.

        7. **Cleanup**: Closes the PDF file object and deletes any temporary files
        created during the process (e.g., cropped images).

        8. **Logging and Returning Results**: Logs the completion of the process for
        each page and the entire workflow. Finally, it returns a JSON response indicating
        the completion of the PDF workflow.

        This method is a comprehensive approach to handling PDF content, utilizing both
        `pdfminer` for text and layout analysis and `PyPDF2` for PDF manipulation, along
        with `pdfplumber` for table extraction and `PIL`/`pdf2image` for image handling
        and OCR via `pytesseract`.
        """
        logger.debug("Starting PDF workflow")
        logger.debug(f"PDF path: {pdf_path}")
        workflow_results = {"text_extraction": []}  # Initialize workflow results

        # create a PDF file object
        pdfFileObj = open(pdf_path, "rb")
        # create a PDF reader object
        pdfReaded = PyPDF2.PdfReader(pdfFileObj)

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
                        workflow_results["text_extraction"].append(
                            {
                                "page": pagenum,
                                "text": line_text,
                                # "format": format_per_line,
                            }
                        )
                    else:
                        # Omit the text that appeared in a table
                        logger.debug("Omitted text in a table")
                        pass

                # Check the elements for images
                if isinstance(element, LTFigure):
                    try:
                        logger.debug("Found an image element, starting OCR process.")
                        # Crop the image from the PDF
                        crop_image(element, pageObj)
                        logger.debug("Cropped image from PDF.")
                        # Convert the cropped pdf to an image
                        convert_to_images("cropped_image.pdf")
                        logger.debug("Converted cropped PDF to image.")
                        # Extract the text from the image
                        image_text = image_to_text("PDF_image.png")
                        logger.debug(f"Extracted text from image: {image_text}")
                        text_from_images.append(image_text)
                        page_content.append(image_text)
                        # Indicate that OCR was successfully performed on an image
                        logger.debug("OCR process completed successfully.")
                    except Exception as e:
                        logger.error(f"Error during OCR process: {str(e)}")
                        # Append error message to indicate OCR process failure
                        text_from_images.append("Error during OCR process.")
                        page_content.append("Error during OCR process.")

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
        if os.path.exists("cropped_image.pdf"):
            os.remove("cropped_image.pdf")
        if os.path.exists("PDF_image.png"):
            os.remove("PDF_image.png")

        # Display the content of the page
        result = ""
        for page_key in text_per_page:
            result += "".join(text_per_page[page_key][4]) + "\n\n"
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

        return JsonResponse({"RESULT": result}, status=200)


if __name__ == "__main__":
    OCRView.pdfworkflow()
