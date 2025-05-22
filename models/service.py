from openai import OpenAI

from app import db
from pgvector.sqlalchemy import VECTOR
from config import OPENAI_API_KEY
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    periode = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    embedding = db.Column(VECTOR(1536), nullable=True)

    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    def generate_embedding(self):
        text = f"Offer: {self.name} {self.description} {self.price} {self.periode}"
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
