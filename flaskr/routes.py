from flask import render_template, request, redirect, url_for
from flaskr.receipt_scanner_classes.receipt_scanner import ReceiptScanner
from flaskr import app
from flaskr.models import db, Receipts, Product, ReceiptProducts
from datetime import datetime


@app.route('/')
def index():
    stored_tickets = Receipts.query.all()
    return render_template('index.html', stored_tickets=stored_tickets)


@app.route('/scan_receipt', methods=['POST'])
def scan_receipt():
    if 'file' not in request.files or 'city' not in request.form or 'shop' not in request.form:
        return 'Invalid request data'

    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    # Process the uploaded image using the ReceiptScanner class
    image_content = file.read()  # Read the content of the file
    scanner = ReceiptScanner(image_content=image_content)
    products_info = scanner.extract_products_info()

    # Extract city and shop from the form
    city = request.form['city']
    shop = request.form['shop']

    # Insert data into the database
    try:
        new_receipt = Receipts(shop_name=shop, shop_city=city, receipt_date=datetime.utcnow(), receipt_amount=0.0)
        db.session.add(new_receipt)
        db.session.commit()

        total_amount = 0.0

        for product_info in products_info:
            product_name = product_info['product_name']
            price = product_info['price']
            quantity = product_info['quantity']

            # Check if the product already exists in the database
            existing_product = Product.query.filter_by(name=product_name).first()

            if existing_product is None:
                new_product = Product(name=product_name, price=price)
                db.session.add(new_product)
                db.session.commit()
            else:
                new_product = existing_product

            # Associate the product with the receipt using foreign keys
            receipt_product = ReceiptProducts(receipt_id=new_receipt.id, product_id=new_product.id, quantity=quantity)
            db.session.add(receipt_product)
            db.session.commit()

            # Update the total amount
            total_amount += float(price) * int(quantity)

        # Update the receipt_amount field
        new_receipt.receipt_amount = total_amount
        db.session.commit()

        # Use PRG pattern: redirect to the index page after a successful submission
        return redirect(url_for('index'))

    except Exception as e:
        return f'Failed to insert data into the database. {str(e)}'



@app.route('/ticket_details/<int:receipt_id>')
def receipt_details(receipt_id):
    receipt = Receipts.query.get(receipt_id)
    if not receipt:
        return 'Receipt not found'

    # Fetch associated products for the receipt
    products = db.session.query(Product, ReceiptProducts).\
        join(ReceiptProducts, ReceiptProducts.product_id == Product.id).\
        filter(ReceiptProducts.receipt_id == receipt_id).all()

    return render_template('receipt_details.html', receipt=receipt, products=products)


@app.route('/remove_ticket', methods=['POST'])
def remove_ticket():
    ticket_id = request.form.get('ticket_id')
    if not ticket_id:
        return 'Invalid request data'
    try:
        associated_products = ReceiptProducts.query.filter_by(receipt_id=ticket_id).all()
        for associated_product in associated_products:
            db.session.delete(associated_product)
             
        Receipts.query.filter_by(id=ticket_id).delete()

        db.session.commit()

        stored_tickets = Receipts.query.all()
        return render_template('index.html', stored_tickets=stored_tickets)
    except Exception as e:
        return f'Failed to delete the receipt. {str(e)}'
