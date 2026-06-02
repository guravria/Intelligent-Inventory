from app import app, db, User

with app.app_context():
    # This creates a user in the database
    new_user = User(username="admin", password="password123")
    db.session.add(new_user)
    db.session.commit()
    print("Success! You can now log in with 'admin' and 'password123'.")