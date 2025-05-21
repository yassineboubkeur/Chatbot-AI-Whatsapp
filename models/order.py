from app import db



class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offre_requested = db.Column(db.String(255), nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)