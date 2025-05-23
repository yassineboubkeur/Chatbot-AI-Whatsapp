from app import db



class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offre_requested = db.Column(db.String(255), nullable=True)
    fullname = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)


    @classmethod
    def create_from_ai_extraction(cls, data):
        try:
            new_order = cls(
                offre_requested=data.get('offre_requested'),
                fullname=data.get('fullname'),
                phone_number=data.get('phone_number'),
                email=data.get('email'),
                client_id=data.get('client_id')
            )

            db.session.add(new_order)
            db.session.commit()
            return new_order
        except Exception as e:
            print(f"Error creating order: {e}")
            db.session.rollback()
            return None