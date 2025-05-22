from app import db


class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), index=True, unique=True)
    phone_number_id = db.Column(db.String(20))
    whatsapp_token = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    tenants_info = db.relationship('TenantInfo', backref='tenants', lazy=True, uselist=False)
    clients = db.relationship('Client', backref='clients', lazy=True)
    services = db.relationship('Service', backref='services', lazy=True)
    products = db.relationship('Product', backref='products', lazy=True)
