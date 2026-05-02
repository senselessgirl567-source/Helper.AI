import sys, os

# Add Helper.Ai directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Helper.Ai', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Helper.Ai'))

from app import app
from flask import Flask, render_template, request, jsonify, session, send_file
# from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_bcrypt import Bcrypt
import os, uuid, json, datetime
from functools import wraps
from db import db, User, Document, SharedDocument
from ai_engine import generate_ppt, generate_report, generate_notes
from io import BytesIO


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'helperai-secret-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'helperai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db.init_app(app)
bcrypt = Bcrypt(app)
# socketio = SocketIO(app, cors_allowed_origins="*")

# ── Auth decorator ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Pages ────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# ── Auth API ─────────────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    pw_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(name=data['name'], email=data['email'], password=pw_hash)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    session['user_name'] = user.name
    return jsonify({'success': True, 'name': user.name})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    session['user_name'] = user.name
    return jsonify({'success': True, 'name': user.name})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me')
@login_required
def me():
    user = User.query.get(session['user_id'])
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email})

# ── AI Generation API ─────────────────────────────────────────────
@app.route('/api/generate/ppt', methods=['POST'])
@login_required
def gen_ppt():
    data = request.json
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    result = generate_ppt(topic)
    doc = Document(
        user_id=session['user_id'],
        title=f"{topic} — Presentation",
        doc_type='ppt',
        content=json.dumps(result),
        is_private=data.get('private', False)
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'success': True, 'doc_id': doc.id, 'data': result})

@app.route('/api/generate/report', methods=['POST'])
@login_required
def gen_report():
    data = request.json
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    result = generate_report(topic)
    doc = Document(
        user_id=session['user_id'],
        title=f"{topic} — Report",
        doc_type='report',
        content=json.dumps(result),
        is_private=data.get('private', False)
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'success': True, 'doc_id': doc.id, 'data': result})

@app.route('/api/generate/notes', methods=['POST'])
@login_required
def gen_notes():
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Input text is required'}), 400
    result = generate_notes(text)
    doc = Document(
        user_id=session['user_id'],
        title=f"Notes — {text[:40]}{'…' if len(text)>40 else ''}",
        doc_type='notes',
        content=json.dumps(result),
        is_private=data.get('private', False)
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'success': True, 'doc_id': doc.id, 'data': result})

# ── Document API ──────────────────────────────────────────────────
@app.route('/api/documents')
@login_required
def get_documents():
    docs = Document.query.filter_by(user_id=session['user_id'])\
                         .order_by(Document.created_at.desc()).limit(20).all()
    return jsonify([d.to_dict() for d in docs])

@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != session['user_id']:
        shared = SharedDocument.query.filter_by(doc_id=doc_id, shared_with=session['user_id']).first()
        if not shared:
            return jsonify({'error': 'Access denied'}), 403
    return jsonify(doc.to_dict())

@app.route('/api/documents/<int:doc_id>/share', methods=['POST'])
@login_required
def share_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    share_token = str(uuid.uuid4())
    doc.share_token = share_token
    db.session.commit()
    return jsonify({'share_url': f'/shared/{share_token}', 'token': share_token})

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/shared/<token>')
def shared_doc(token):
    doc = Document.query.filter_by(share_token=token).first_or_404()
    return render_template('shared.html', doc=doc)

# ── Real-time collaboration (Socket.IO) ────────────────────────────
# @socketio.on('join_room')
# def on_join(data):
#     room = data['room']
#     join_room(room)
#     emit('user_joined', {'user': session.get('user_name', 'Guest'), 'room': room}, to=room)

# @socketio.on('leave_room')
# def on_leave(data):
#     room = data['room']
#     leave_room(room)
#     emit('user_left', {'user': session.get('user_name', 'Guest')}, to=room)

# @socketio.on('note_update')
# def on_note_update(data):
#     emit('note_changed', {
#         'content': data['content'],
#         'user': session.get('user_name', 'Guest'),
#         'cursor': data.get('cursor')
#     }, to=data['room'], include_self=False)

# @socketio.on('voice_signal')
# def on_voice(data):
#     emit('voice_data', data, to=data['room'], include_self=False)

# ── Init & run ────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    print("✓ Database ready")

# For Vercel deployment
app.run() if __name__ == '__main__' else None
