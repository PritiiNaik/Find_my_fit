import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Suppresses noisy TensorFlow logs

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

@app.route('/clear_model')
def clear_model():
    if 'user_id' in session and 'user_model' in session:
        try:
            os.remove(session['user_model'])
        except:
            pass
        session.pop('user_model')
    return redirect(url_for('upload_file'))


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

# Update the upload_file route in main.py

# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         model_image = request.files.get('model_image')
#         clothes_image = request.files.get('clothes_image')
#         garment_type = request.form.get('garment_type')
#         preselected_garment = request.form.get('preselected_garment')

#         # Validate model image is always required
#         if not model_image:
#             return jsonify({'error': 'Model image is required'}), 400

#         # Handle clothes image - either uploaded or preselected
#         if not clothes_image and not preselected_garment:
#             return jsonify({'error': 'Clothes image is required'}), 400

#         # Prepare file paths
#         model_filename = secure_filename(model_image.filename)
#         model_image_path = os.path.join(app.config['UPLOAD_FOLDER'], model_filename)
#         model_image.save(model_image_path)

#         # Handle clothes image
#         if clothes_image:
#             clothes_filename = secure_filename(clothes_image.filename)
#             clothes_image_path = os.path.join(app.config['UPLOAD_FOLDER'], clothes_filename)
#             clothes_image.save(clothes_image_path)
#         else:
#             # Use preselected garment
#             clothes_filename = os.path.basename(preselected_garment)
#             clothes_image_path = os.path.join(app.config['UPLOAD_FOLDER'], clothes_filename)
            
#             # Copy preselected garment to upload folder
#             try:
#                 import shutil
#                 shutil.copy2(preselected_garment, clothes_image_path)
#             except Exception as e:
#                 return jsonify({'error': f'Failed to use preselected garment: {str(e)}'}), 500

#         # Process the images
#         clothes_no_bg_path = os.path.join(app.config['UPLOAD_FOLDER'], 'no_bg_' + clothes_filename)
#         output_filename = 'output_' + model_filename
#         output_image_path = os.path.join(app.config['STATIC_FOLDER'], output_filename)

#         # Remove background from clothes image
#         if not remove_background(clothes_image_path, clothes_no_bg_path):
#             return jsonify({'error': 'Background removal failed'}), 500

#         # Perform the overlay based on garment type
#         if garment_type == 'lower_body':
#             output_path, message = overlay_lower_body_garment(model_image_path, clothes_no_bg_path, output_image_path)
#         elif garment_type == 'upper_body':
#             output_path, message = overlay_cloth_on_model(model_image_path, clothes_no_bg_path, output_image_path)
#         else:
#             return jsonify({'error': 'Invalid garment type'}), 400

#         if output_path:
#             with open(output_image_path, "rb") as img_file:
#                 img_data = base64.b64encode(img_file.read()).decode('utf-8')
#             return render_template('result.html', img_data=img_data)
#         else:
#             return jsonify({'error': message}), 500

#     # GET request handling
#     garment_path = request.args.get('garment')
    
#     # If coming from Try On button with a garment preselected
#     if garment_path:
#         # Verify the garment exists
#         if not os.path.exists(garment_path):
#             return "Selected garment not found", 404
            
#         # Determine garment type based on filename or path (simple heuristic)
#         garment_type = 'upper_body'  # default
#         lower_body_keywords = ['pant', 'skirt', 'lower', 'jeans']
#         if any(keyword in garment_path.lower() for keyword in lower_body_keywords):
#             garment_type = 'lower_body'
        
#         return render_template('upload.html', 
#                             preselected_garment=garment_path,
#                             garment_type=garment_type)
    
#     # Regular GET request without preselected garment
#     return render_template('upload.html')

# Add this helper function
def get_user_upload_folder(user_id):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

# Update the upload_file route
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_folder = get_user_upload_folder(user_id)
    
    if request.method == 'POST':
        model_image = request.files.get('model_image')
        clothes_image = request.files.get('clothes_image')
        garment_type = request.form.get('garment_type')
        preselected_garment = request.form.get('preselected_garment')
        change_model = 'change_model' in request.form  # Changed to check presence

        # Handle model image
        if change_model or 'user_model' not in session:
            # Need new model image
            if not model_image:
                return jsonify({'error': 'Model image is required when changing or first time'}), 400
            model_filename = secure_filename(f"user_{user_id}_model.png")
            model_image_path = os.path.join(user_folder, model_filename)
            model_image.save(model_image_path)
            session['user_model'] = model_image_path
        else:
            # Use existing model
            model_image_path = session['user_model']
            if not os.path.exists(model_image_path):
                session.pop('user_model')
                return jsonify({'error': 'Saved model image not found, please upload again'}), 400

        # Handle clothes image
        if not clothes_image and not preselected_garment:
            return jsonify({'error': 'Clothes image is required'}), 400

        if clothes_image:
            clothes_filename = secure_filename(clothes_image.filename)
            clothes_image_path = os.path.join(user_folder, clothes_filename)
            clothes_image.save(clothes_image_path)
        else:
            clothes_filename = os.path.basename(preselected_garment)
            clothes_image_path = os.path.join(user_folder, clothes_filename)
            try:
                import shutil
                shutil.copy2(preselected_garment, clothes_image_path)
            except Exception as e:
                return jsonify({'error': f'Failed to use preselected garment: {str(e)}'}), 500

        # Rest of the processing remains the same...
        clothes_no_bg_path = os.path.join(user_folder, 'no_bg_' + clothes_filename)
        output_filename = f"output_{user_id}_{os.path.basename(model_image_path)}"
        output_image_path = os.path.join(app.config['STATIC_FOLDER'], output_filename)

        if not remove_background(clothes_image_path, clothes_no_bg_path):
            return jsonify({'error': 'Background removal failed'}), 500

        if garment_type == 'lower_body':
            output_path, message = overlay_lower_body_garment(model_image_path, clothes_no_bg_path, output_image_path)
        elif garment_type == 'upper_body':
            output_path, message = overlay_cloth_on_model(model_image_path, clothes_no_bg_path, output_image_path)
        else:
            return jsonify({'error': 'Invalid garment type'}), 400

        if output_path:
            with open(output_image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            return render_template('result.html', img_data=img_data)
        return jsonify({'error': message}), 500

    # GET request handling remains the same...
    garment_path = request.args.get('garment')
    
    if garment_path:
        if not os.path.exists(garment_path):
            return "Selected garment not found", 404
            
        garment_type = 'upper_body'
        lower_body_keywords = ['pant', 'skirt', 'lower', 'jeans']
        if any(keyword in garment_path.lower() for keyword in lower_body_keywords):
            garment_type = 'lower_body'
        
        return render_template('upload.html', 
                            preselected_garment=garment_path,
                            garment_type=garment_type,
                            has_model='user_model' in session)
    
    return render_template('upload.html', has_model='user_model' in session)
if __name__ == '__main__':
    app.run(debug=True, port=5002)
