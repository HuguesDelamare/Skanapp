from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


"""
class ShopCities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(255), nullable=False)


class ShopsList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(255), nullable=False)
    shop_city_id = db.Column(db.Integer, db.ForeignKey('shop_cities.id'), nullable=False)
    shop_city = db.relationship('ShopCities', backref=db.backref('shops_list', lazy=True))
"""


class Receipts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(255), nullable=False)
    shop_city = db.Column(db.String(255), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False)
    receipt_amount = db.Column(db.Float, nullable=False)
    receipt_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)


class ReceiptProducts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
