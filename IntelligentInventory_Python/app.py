import cv2
import requests  # Module 10: For Telegram Alerts
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

# Utility Function for Alerts
def send_telegram_alert(msg):
    token = "8461798671:AAHa5n4eeBP4Uaw2AAG3LQ3R0X42ZZGqyxc"
    chat_id = "8015367469"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Telegram Failed: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'business-secret-key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    products = db.relationship('Product', backref='owner', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    expiry_date = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not User.query.filter_by(username=username).first():
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- UPDATED DASHBOARD: PROACTIVE AUDIT FOR EXPIRE & RESTOCK ---
@app.route('/dashboard')
@login_required 
def dashboard():
    all_products = Product.query.filter_by(user_id=current_user.id).all()
    
    # 1. Check for Low Stock (like your Oreo Biscuits)
    low_stock_list = Product.query.filter_by(user_id=current_user.id).filter(Product.quantity < 5).all()
    if low_stock_list:
        low_names = ", ".join([p.name for p in low_stock_list])
        send_telegram_alert(f"⚠️ RESTOCK ALERT: {low_names} are low (under 5 units)!")

    # 2. Check for Expired Items
    today_str = datetime.now().strftime('%Y-%m-%d')
    expired_list = Product.query.filter_by(user_id=current_user.id).filter(Product.expiry_date <= today_str).all()
    if expired_list:
        expired_names = ", ".join([p.name for p in expired_list])
        send_telegram_alert(f"🚨 EXPIRED ALERT: {expired_names} have expired!")

    return render_template('dashboard.html', 
                           products=all_products, 
                           low_stock_count=len(low_stock_list),
                           expired_count=len(expired_list))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        barcode = request.form['barcode']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        expiry = request.form['expiry'] 
        existing = Product.query.filter_by(barcode=barcode, user_id=current_user.id).first()
        if existing:
            existing.quantity += quantity
        else:
            new_item = Product(name=name, barcode=barcode, quantity=quantity, 
                               price=price, expiry_date=expiry, user_id=current_user.id)
            db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_product.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        product.name = request.form['name']
        product.quantity = int(request.form['quantity'])
        product.price = float(request.form['price'])
        product.expiry_date = request.form['expiry']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.user_id == current_user.id:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/start_scanner')
@login_required 
def start_scanner():
    cap = cv2.VideoCapture(0)
    detector = cv2.barcode.BarcodeDetector()
    while True:
        success, frame = cap.read()
        if not success: break
        retval, decoded_info, points = detector.detectAndDecode(frame)
        if retval and len(decoded_info) > 0:
            scanned_code = decoded_info[0]
            product = Product.query.filter_by(barcode=scanned_code, user_id=current_user.id).first()
            if product and product.quantity > 0:
                product.quantity -= 1
                db.session.commit()
                if product.quantity < 5:
                    send_telegram_alert(f"⚠️ ALERT: {product.name} is low! Only {product.quantity} left.")
                cap.release()
                cv2.destroyAllWindows()
                return redirect(url_for('dashboard'))
        cv2.imshow('AI Scanner - Press Q to Close', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
