import time

from app import create_app, db
from models import Service


def update_all_service_embeddings():
    print("Hello")
    app = create_app()
    with app.app_context():
        services = Service.query.all()
        print(services)
        for service in services:
            print(f"Generating embedding for service {service.id}: {service.name}")

            service.generate_and_save_embedding()

            time.sleep(0.5)



if __name__ == "__main__":
    update_all_service_embeddings()