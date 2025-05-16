from models.product import Product
from app import db

def query_products(name):
    return Product.query.filter(Product.name.ilike(f'%{name}%')).all() # we should add LIMIT