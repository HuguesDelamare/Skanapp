import cv2
import pytesseract
import re
from PIL import Image
from io import BytesIO
import numpy as np


class ReceiptScanner:
    def __init__(self, image_content):
        # Open the image using PIL
        self.image = Image.open(BytesIO(image_content))

        # Decode the image using OpenCV
        self.frame = cv2.imdecode(np.frombuffer(image_content, np.uint8), -1)

        self.custom_config = r'--oem 3 --psm 6'
        self.price_pattern = r'\b\d+[\.,]?\s?\d+\b'
        self.quantity_pattern = r'(\d+)\s?st'  # Regex to find quantity pattern like "2st"
        self.remove_pattern = r'\*\d+[\.,]?\s?\d+'  # Regex to find pattern like "*19,60"
        self.ignore_words = ["Extrapris", "+PANT ALUMINIUMBURK", "Rabat"]

        # Configuration du chemin vers Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def process_receipt(self):
        text = pytesseract.image_to_string(self.image, config=self.custom_config)
        lines = text.split('\n')
        start_line, end_line = self._find_start_end_lines(lines)

        for line in lines[start_line + 1:end_line]:
            product_name, price, quantity = self._extract_product_info(line)
            if product_name and price:
                print(f"{product_name} | Price: {price} | Quantity: {quantity}")

    def _find_start_end_lines(self, lines):
        start_line = -1
        end_line = len(lines) - 1

        for idx, line in enumerate(lines):
            if "Start Sjalvscanning" in line:
                start_line = idx
            if "seeeeecess Slut SJalvscanning SRSUSseanee" in line and start_line != -1:
                end_line = idx
                break

        return start_line, end_line

    def _extract_product_info(self, line):
        product_name = ""
        price = ""
        quantity = 1  # Default quantity is 1
        found_prices = re.findall(self.price_pattern, line)
        found_quantity = re.search(self.quantity_pattern, line)

        if found_prices:
            price = found_prices[-1].replace(' ', '')
            product_name = line.split(price)[0].strip()
            price_str = price.replace(',', '.')
            price = float(price_str)

        if found_quantity:
            quantity = int(found_quantity.group(1))

        # Remove quantity and associated characters from the product name
        product_name = re.sub(self.quantity_pattern, '', product_name).strip()

        # Handle case where product name contains both quantity and price
        if '*' in product_name:
            parts = product_name.split('*')
            if len(parts) == 2:
                # If there are exactly two parts separated by '*', set the price to the second part
                try:
                    price = float(parts[1].replace(',', '.'))
                except ValueError:
                    pass  # Handle the case where the second part is not a valid float

        # Remove the pattern like "*19,60" from the product name
        product_name = re.sub(self.remove_pattern, '', product_name).strip()

        if any(word in product_name for word in self.ignore_words):
            return None, None, None

        return product_name, price, quantity

    def extract_products_info(self):
        # Assuming you want to return the products_info as a list
        products_info = []
        text = pytesseract.image_to_string(self.image, config=self.custom_config)
        lines = text.split('\n')
        start_line, end_line = self._find_start_end_lines(lines)

        for line in lines[start_line + 1:end_line]:
            product_name, price, quantity = self._extract_product_info(line)
            if product_name and price:
                products_info.append({'product_name': product_name, 'price': price, 'quantity': quantity})

        return products_info
