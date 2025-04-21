from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import base64
from rembg import remove
from verify import overlay_cloth_on_model
from verify2 import overlay_lower_body_garment

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))  # Hashed password

# One-time: create DB (or use Flask shell)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/homw')
def homw():
    if 'user_id' in session:
        return render_template('homw.html')
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already registered!'}), 409

    hashed_password = generate_password_hash(password)
    user = User(name=name, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully!'})

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})


# Upload & Try-on logic
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = os.path.join('static', 'results')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

def remove_background(input_path, output_path):
    try:
        with open(input_path, 'rb') as input_file:
            input_bytes = input_file.read()
        output_bytes = remove(input_bytes)
        with open(output_path, 'wb') as output_file:
            output_file.write(output_bytes)
        return True
    except Exception as e:
        print(f"Background removal error: {e}")
        return False

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        model_image = request.files.get('model_image')
        clothes_image = request.files.get('clothes_image')
        garment_type = request.form.get('garment_type')

        if model_image and clothes_image:
            model_filename = secure_filename(model_image.filename)
            clothes_filename = secure_filename(clothes_image.filename)

            model_image_path = os.path.join(app.config['UPLOAD_FOLDER'], model_filename)
            clothes_image_path = os.path.join(app.config['UPLOAD_FOLDER'], clothes_filename)
            clothes_no_bg_path = os.path.join(app.config['UPLOAD_FOLDER'], 'no_bg_' + clothes_filename)
            output_filename = 'output_' + model_filename
            output_image_path = os.path.join(app.config['STATIC_FOLDER'], output_filename)

            model_image.save(model_image_path)
            clothes_image.save(clothes_image_path)

            if not remove_background(clothes_image_path, clothes_no_bg_path):
                return jsonify({'error': 'Background removal failed'})

            if garment_type == 'lower_body':
                output_path, message = overlay_lower_body_garment(model_image_path, clothes_no_bg_path, output_image_path)
            elif garment_type == 'upper_body':
                output_path, message = overlay_cloth_on_model(model_image_path, clothes_no_bg_path, output_image_path)
            else:
                return jsonify({'error': 'Invalid garment type'})

            if output_path:
                with open(output_image_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                return render_template('result.html', img_data=img_data)
            else:
                return jsonify({'error': message})

    return render_template('upload.html')



if __name__ == '__main__':
    app.run(debug=True, port=5002)
