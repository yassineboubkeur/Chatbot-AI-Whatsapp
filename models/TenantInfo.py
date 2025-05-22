from enum import unique

from app import db
from pgvector.sqlalchemy import VECTOR
from config import OPENAI_API_KEY
from openai import OpenAI


class TenantInfo(db.Model):
    __tablename__ = 'tenant_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    embedding = db.Column(VECTOR(1536), nullable=True)


    def generate_embedding(self):
        text = f"Tenant Information: {self.name} {self.email} {self.phone_number} {self.address} {self.city}"
        client = OpenAI(api_key=OPENAI_API_KEY)

        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002",
            )
            self.embedding = response.data[0].embedding
        except Exception as e:
            # LOGGING
            raise e
        return self.embedding