from app import db
from pgvector.sqlalchemy import VECTOR
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    embedding = db.Column(VECTOR(1536), nullable=True)