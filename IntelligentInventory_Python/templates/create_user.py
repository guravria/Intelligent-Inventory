from app import app, db, User

with app.app_context():
    # Delete existing user to avoid duplicates
    User.query.filter_by(username="admin").delete()
    # Create new admin user
    new_user = User(username="admin", password="password123")
    db.session.add(new_user)
    db.session.commit()
    print("User 'admin' with password 'password123' created!")