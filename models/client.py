from enum import unique

from app import db


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    orders = db.relationship('Order', backref='orders', lazy=True)

    @classmethod
    def get_client_id_from_phone(cls, phone_number):
        client = cls.query.filter_by(phone_number=phone_number).first()
        return client.id if client else None

    @classmethod
    def insert_client_data(cls, phone_number, client_name, tenant_id):
        existing_client = Client.query.filter_by(phone_number=phone_number).first()
        if not existing_client:
            new_client = Client(phone_number=phone_number, fullname=client_name, tenant_id=tenant_id)

            db.session.add(new_client)
            db.session.commit()

            return new_client
        return None