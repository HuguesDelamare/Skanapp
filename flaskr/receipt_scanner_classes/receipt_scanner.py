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

        self.custom_config = r'--oem 3 --psm 6 -l swe'
        self.price_pattern = r'\b\d+[.,]?\d*\b'
        self.quantity_pattern = r'(\d+)\s?(st\.?|stk\.?|pcs\.?)'  # Regex to find quantity pattern like "2st"
        self.remove_pattern = r'\*\d+[\.,]?\s?\d+'  # Regex to find pattern like "*19,60"
        self.ignore_words = ["Extrapris", "+PANT ALUMINIUMBURK", "Rabat", "+PANT ENG PET"]

        # Configuration du chemin vers Tesseract OCR
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def preprocess_image(self):
        # Convert the image to gray scale
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

        # Performing OTSU threshold
        ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        # Specify structure shape and kernel size.
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

        # Applying dilation on the threshold image
        dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)

        # Finding contours
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Creating a copy of image
        im2 = gray.copy()

        # A bounding box is created around the contour area.
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Drawing a rectangle on copied image
            rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Resizing the image
        resized_img = cv2.resize(im2, (700, 800))

        return resized_img


    def process_receipt(self):
        # Preprocess the image
        preprocessed_image = self.preprocess_image()

        text = pytesseract.image_to_string(preprocessed_image, config=self.custom_config)
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
                print(f"Found start line at index {idx}: {line}")
            if "seeeeecess Slut SJalvscanning SRSUSseanee" in line and start_line != -1:
                end_line = idx
                print(f"Found end line at index {idx}: {line}")
                break

        return start_line, end_line

    def _extract_product_info(self, line):
        product_name = ""
        price = ""
        quantity = 1  # Default quantity is 1

        # Split the line by spaces
        parts = line.split()

        if len(parts) > 1:
            # The last part should be the price
            try:
                price = float(parts[-1].replace(',', '.'))
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
