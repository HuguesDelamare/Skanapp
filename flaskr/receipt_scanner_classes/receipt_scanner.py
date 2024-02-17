import fitz  # PyMuPDF
import io
from PIL import Image
import os
import pytesseract
import re
from datetime import datetime

class ReceiptScanner:
    def __init__(self, pdf_content):
        self.pdf_content = pdf_content
        current_directory = os.path.dirname(os.path.realpath(__file__))
        self.uploads_folder = os.path.join(current_directory, '..', 'uploads')
        self.save_pdf_as_images(self.pdf_content)

        # Configuration du chemin vers Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        self.custom_config = r'--oem 3 --psm 6 -l fra'  # Configuration de Tesseract OCR

        self.price_pattern = r'\b\d+[.,]?\d*\b'
        self.quantity_pattern = r'(\d+)\s?(st\.?|stk\.?|pcs\.?)\*?\b(?!\s*(g|kg|l))'
        self.remove_pattern = r'\*\d+[\.,]?\s?\d+'
        self.ignore_words = ["Extrapris", "+PANT ALUMINIUMBURK", "Rabat", "+PANT ENG PET"]

    def save_pdf_as_images(self, pdf_content):
        try:
            # Convert PDF to images
            pdf = fitz.open(stream=pdf_content, filetype="pdf")
            zoom_x = 2.0  
            zoom_y = 2.0
            mat = fitz.Matrix(zoom_x, zoom_y)  # zoom factor 2 in each dimension

            # Get the current date
            current_date = datetime.now().strftime('%d-%m-%Y')

            for i in range(len(pdf)):
                # Read the page
                page = pdf[i]
                pix = page.get_pixmap(matrix=mat)  # use 'mat' instead of the default value

                # Construct the image file path with the current date and index
                image_path = os.path.join(self.uploads_folder, f'{current_date}_{i}.png')
                print("Saving image to:", image_path)

                # Convert to PIL image and save
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img.save(image_path)

            print(f"Saved {len(pdf)} images in {self.uploads_folder}")
        except Exception as e:
            print(f"Error: {e}")
    
    def _extract_product_info(self, line):
        product_name = ""
        price = ""
        quantity = 1

        # Split the line by spaces
        parts = line.split()

        if len(parts) > 1:
            try:
                # Parse the raw price and format it with two digits after the decimal point
                raw_price = parts[-1].replace(',', '.')
                price = '{:.2f}'.format(float(raw_price))
            except ValueError:
                return None, None, None  # Skip if price is not a valid float

            # The product name is all parts except the last one
            product_name = " ".join(parts[:-1])

        found_quantity = re.search(self.quantity_pattern, product_name, flags=re.IGNORECASE)

        if found_quantity:
            quantity = int(found_quantity.group(1))
            # Remove quantity and associated characters from the product name
            product_name = re.sub(self.quantity_pattern, '', product_name).strip()

        if any(word in product_name for word in self.ignore_words):
            return None, None, None

        return product_name, price, quantity

    def read_images_with_ocr(self):
        try:
            # Get the number of images
            num_images = len([name for name in os.listdir(self.uploads_folder) if os.path.isfile(os.path.join(self.uploads_folder, name))])
            
            for i in range(num_images):
                image_path = os.path.join(self.uploads_folder, 'image_{}.png'.format(i))
                text = pytesseract.image_to_string(Image.open(image_path), config=self.custom_config)
                
                # Split the text into lines
                lines = text.split('\n')
                
                # Initialize a flag to indicate whether we are between "Start Självscanning" and "Slut Självscanning"
                start_scanning = False
                
                for line in lines:
                    if "Start Självscanning" in line:
                        start_scanning = True
                    elif "Slut Självscanning" in line:
                        start_scanning = False
                    
                    # Only print the line if we are between "Start Självscanning" and "Slut Självscanning"
                    if start_scanning:
                        print(line)
        except Exception as e:
            print("Error: {}".format(e))

    def extract_products_info(self):
        products_info = []
        for i in range(len(self.pdf_content)):
            image_path = os.path.join(self.uploads_folder, 'image_{}.png'.format(i))
            text = pytesseract.image_to_string(Image.open(image_path), config=self.custom_config)
            
            # Split the text into lines
            lines = text.split('\n')
            
            # Initialize a flag to indicate whether we are between "Start Självscanning" and "Slut Självscanning"
            start_scanning = False
            
            for line in lines:
                if "Start Självscanning" in line:
                    start_scanning = True
                elif "Slut Självscanning" in line:
                    start_scanning = False
                
                # Only process the line if we are between "Start Självscanning" and "Slut Självscanning"
                if start_scanning:
                    product_name, price, quantity = self._extract_product_info(line)
                    if product_name and price and quantity:
                        products_info.append({'product_name': product_name, 'price': price, 'quantity': quantity})

        return products_info
