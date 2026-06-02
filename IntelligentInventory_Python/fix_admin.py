from app import app, db, User

with app.app_context():
    # Find the user 'admin' if it exists, or create it
    user = User.query.filter_by(username='admin').first()
    if user:
        user.password = '123' # Setting a very simple password
        print("Existing admin password updated to: 123")
    else:
        new_user = User(username='admin', password='123')
        db.session.add(new_user)
        print("New admin user created with password: 123")
    
    db.session.commit()
    