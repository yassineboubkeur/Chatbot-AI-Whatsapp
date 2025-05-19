from models.product import Product
from app import db

def query_product(name):
    return Product.query.filter(Product.name.ilike(f'%{name}%')).all() # TODO:  we should add some limits