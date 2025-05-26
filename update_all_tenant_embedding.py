import time

from app import create_app, db
from models import TenantInfo

def update_all_tenant_embedding():
    app = create_app()
    with app.app_context():
        tenants = TenantInfo.query.all()
        print(tenants)
        for tenant in tenants:
            print(f"Generating embedding for tenant {tenant.id}: {tenant.name}")

            tenant.generate_embedding()

            db.session.commit()
            time.sleep(0.5)


if __name__ == '__main__':
    update_all_tenant_embedding()