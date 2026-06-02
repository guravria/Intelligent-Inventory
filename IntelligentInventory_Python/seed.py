from app import app, db, Product

with app.app_context():
    # Clear existing data
    db.drop_all()
    db.create_all()

    # Add Test Products (Module 3)
    p1 = Product(name="Oreo Biscuits", barcode="123456789", quantity=10, price=30.0)
    p2 = Product(name="Amul Milk", barcode="987654321", quantity=3, price=27.0)
    
    db.session.add(p1)
    db.session.add(p2)
    db.session.commit()

    print("Success! Test products added to Module 5 Dashboard.")