from models.client import Client
from app import db

def insert_client_data(phone_number, client_name, tenant_id):

    new_client = Client(phone_number=phone_number, fullname=client_name, tenant_id=tenant_id)

    db.session.add(new_client)
    db.session.commit()

    return new_client