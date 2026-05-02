from flask_sqlalchemy import SQLAlchemy
import datetime, json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    documents  = db.relationship('Document', backref='owner', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}


class Document(db.Model):
    __tablename__ = 'documents'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    doc_type    = db.Column(db.String(20), nullable=False)   # ppt | report | notes
    content     = db.Column(db.Text, nullable=False)
    is_private  = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(36), unique=True, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                            onupdate=datetime.datetime.utcnow)
    shares      = db.relationship('SharedDocument', backref='document', lazy=True)

    def to_dict(self):
        return {
            'id':         self.id,
            'title':      self.title,
            'doc_type':   self.doc_type,
            'content':    json.loads(self.content),
            'is_private': self.is_private,
            'share_token':self.share_token,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M'),
        }


class SharedDocument(db.Model):
    __tablename__ = 'shared_documents'
    id           = db.Column(db.Integer, primary_key=True)
    doc_id       = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    shared_with  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    can_edit     = db.Column(db.Boolean, default=False)
    shared_at    = db.Column(db.DateTime, default=datetime.datetime.utcnow)
