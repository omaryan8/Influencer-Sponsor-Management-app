from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db=SQLAlchemy(app)

class User(db.Model):
    __tablename__="User"
    user_id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True)
    passhash=db.Column(db.String(256),nullable=False)
    role = db.Column(db.String(100),nullable=False)

class Influencer(db.Model):
    __tablename__="Influencer"
    influencer_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('User.user_id'),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    category=db.Column(db.String(100),nullable=False)
    platform=db.Column(db.String(100),nullable=False)
    reach=db.Column(db.Integer)
    phone=db.Column(db.String(20))

    user = db.relationship("User", backref="influencer", lazy=True)

class Sponsor(db.Model):
    __tablename__="Sponsor"
    sponsor_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('User.user_id'),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    industry=db.Column(db.String(100),nullable=False)
    budget=db.Column(db.DECIMAL(10,2))

    user = db.relationship("User", backref="sponsor", lazy=True)
    
class Campaign(db.Model):
    __tablename__="Campaign"
    campaign_id=db.Column(db.Integer,primary_key=True)
    sponsor_id=db.Column(db.Integer,db.ForeignKey('Sponsor.sponsor_id'),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    description=db.Column(db.Text,nullable=False)
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date,nullable=False)
    budget=db.Column(db.Integer)
    visibility=db.Column(db.String(20),nullable=False)

    sponsor = db.relationship("Sponsor", backref="campaigns", lazy=True)

class AdRequest(db.Model):
    __tablename__="AdRequest"
    ad_request_id=db.Column(db.Integer,primary_key=True)
    influencer_id=db.Column(db.Integer,db.ForeignKey('Influencer.influencer_id'),nullable=False)
    campaign_id=db.Column(db.Integer,db.ForeignKey('Campaign.campaign_id'),nullable=False)
    name=db.Column(db.Text,nullable=False)
    messages=db.Column(db.Text,nullable=False)
    payment_amount=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(20),nullable=False)
    sender = db.Column(db.String(20), nullable=False)

    campaign = db.relationship("Campaign", backref="ad_requests", lazy=True)
    influencer = db.relationship("Influencer", backref="ad_requests", lazy=True)

class Flagged(db.Model):
    __tablename__="Flagged"
    flagged_id=db.Column(db.Integer,primary_key=True)
    item_id=db.Column(db.Integer,nullable=False)
    item_type=db.Column(db.String(100),nullable=False)
    flagged_at = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()
    #Create admin if not already there
    admin=User.query.filter_by(role='Admin').first()
    if not admin:
        passhash=generate_password_hash('admin0811')
        admin=User(username='admin',passhash=passhash,role='Admin')
        db.session.add(admin)
        db.session.commit()