from flask import render_template, request, url_for, flash, redirect, session
from models import db,User,Influencer,Sponsor,Campaign,AdRequest,Flagged
from app import app
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import matplotlib.pyplot as plt
import re

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not password or not username or not role:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('danger','Username does not exist')
            return redirect(url_for('login'))
        flagged_user = Flagged.query.filter(Flagged.item_id == user.user_id, Flagged.item_type.in_(['Influencer', 'Sponsor'])).first()
        if flagged_user:
            flash('danger','Your account has been flagged')
            return redirect(url_for('login'))
        
        if not check_password_hash(user.passhash,password):
            flash('danger','Password is incorrect')
            return redirect(url_for('login'))
        
        if role != user.role:
            flash('danger','Role is incorrect')
            return redirect(url_for('login'))
        
        session['user_id'] = user.user_id
        flash('success','Login Successful')
        return redirect(url_for('index'))
    
    return render_template('login.html')

#INFLUENCER
@app.route('/influencer_register', methods=['GET', 'POST'])
def influencer_register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        category = request.form.get('category')
        platform = request.form.get('platform')
        reach = request.form.get('reach')
        phone = request.form.get('phone')
        if not re.match("^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$",phone):
            flash('danger','Phone number not according to Indian standards')
            return redirect(url_for('influencer_register'))
        
        if not name or not username or not password or not confirm_password or not category or not platform or not reach:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('influencer_register'))
        
        if password != confirm_password:
            flash('danger','Passwords do not match')
            return redirect(url_for('influencer_register'))
        
        if User.query.filter_by(username=username).first():
            flash('danger','Username not available. Please choose a different username')
            return redirect(url_for('influencer_register'))
        
        pass_hash=generate_password_hash(password)
        user = User(username=username, passhash=pass_hash,role='Influencer') #type:ignore
        db.session.add(user)
        db.session.commit()

        user_id=user.user_id
        influencer = Influencer(user_id=user_id, name=name, category=category, platform=platform, reach=reach, phone=phone)
        db.session.add(influencer)
        db.session.commit()
        flash('success','User successfully registered')
        return redirect(url_for('login'))
    return render_template('influencer_register.html')

#SPONSOR
@app.route('/sponsor_register', methods=['GET', 'POST'])
def sponsor_register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        industry = request.form.get('industry')
        budget = request.form.get('budget')

        if not name or not username or not password or not confirm_password or not industry or not budget:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('sponsor_register'))
        
        if password != confirm_password:
            flash('danger','Passwords do not match')
            return redirect(url_for('sponsor_register'))
        
        if User.query.filter_by(username=username).first():
            flash('danger','Username not available. Please choose a different username')
            return redirect(url_for('sponsor_register'))
        
        pass_hash=generate_password_hash(password)
        user = User(username=username, passhash=pass_hash,role='Sponsor') #type:ignore
        db.session.add(user)
        db.session.commit()

        user_id=user.user_id
        sponsor = Sponsor(user_id=user_id, name=name, industry=industry, budget=budget)
        db.session.add(sponsor)
        db.session.commit()
        flash('success','User successfully registered')
        return redirect(url_for('login'))
    return render_template('sponsor_register.html')

#DECORATORS
#AUTH-REQUIRED
def auth_required(f):
    @wraps(f)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('danger','You must be logged in to view this page')
            return redirect(url_for('login'))
        return f(*args,**kwargs) 
    return inner

#ADMIN-REQUIRED
def admin_required(f):
    @wraps(f)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('danger','You must be logged in to view this page')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'Admin':
            flash('danger','You must be an admin to view this page')
            return redirect(url_for('index'))
        return f(*args,**kwargs)
    return inner

#INFLUENCER-REQUIRED
def influencer_required(f):
    @wraps(f)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('danger','You must be logged in to view this page')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'Influencer':
            flash('danger','You must be an influencer to view this page')
            return redirect(url_for('index'))
        return f(*args,**kwargs)
    return inner

#SPONSOR-REQUIRED
def sponsor_required(f):
    @wraps(f)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash('danger','You must be logged in to view this page')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'Sponsor':
            flash('danger','You must be a sponsor to view this page')
            return redirect(url_for('index'))
        return f(*args,**kwargs)
    return inner


@app.route('/')
@auth_required
def index():
    user=User.query.get(session['user_id'])
    if user.role == 'Admin':
        return redirect(url_for('admin'))
    if user.role == 'Sponsor':
        return redirect(url_for('sponsor_profile'))
    if user.role == 'Influencer':
        return redirect(url_for('influencer_profile'))
    return render_template('sponsor/sponsor_profile.html',user=user)

#SPONSOR_PROFILE
@app.route('/sponsor_profile')
@sponsor_required
def sponsor_profile():
    user=User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.user_id).first().sponsor_id
    campaigns=Campaign.query.filter_by(sponsor_id=sponsor).all()
    progress_list = []
    for campaign in campaigns:
        today = datetime.datetime.today().date()
        start_date = campaign.start_date
        end_date = campaign.end_date
        
        total_duration = (end_date - start_date).days
        elapsed_time = (today - start_date).days
        
        if elapsed_time < 0:
            progress = 0
        elif elapsed_time > total_duration:
            progress = 100
        else:
            progress = (elapsed_time / total_duration) * 100
        progress_list.append(progress)

    ad_requests = []
    for campaign in campaigns:
        ad_requests.extend(AdRequest.query.filter_by(campaign_id=campaign.campaign_id).all())

    return render_template('sponsor/sponsor_profile.html',user=user,campaigns=campaigns, ad_requests=ad_requests,progress_list=progress_list, zip=zip, date=datetime.date,sponsor=sponsor)

#INFLUENCER_PROFILE
@app.route('/influencer_profile')
@influencer_required
def influencer_profile():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.filter_by(user_id=user.user_id).first()
    influencer_id = influencer.influencer_id
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id).all()
    campaigns = Campaign.query.filter_by(visibility="public").all()
    progress_list = []
    for campaign in campaigns:
        today = datetime.datetime.today().date()
        start_date = campaign.start_date
        end_date = campaign.end_date
        
        total_duration = (end_date - start_date).days
        elapsed_time = (today - start_date).days
        
        if elapsed_time < 0:
            progress = 0
        elif elapsed_time > total_duration:
            progress = 100
        else:
            progress = (elapsed_time / total_duration) * 100
        progress_list.append(progress)
    return render_template('influencer/influencer_profile.html',user=user,campaigns=campaigns, ad_requests=ad_requests,progress_list=progress_list, zip=zip, date=datetime.date,influencer=influencer)

@app.route('/influencer/<int:influencer_id>/update',methods=['GET','POST'])
@auth_required
def update_influencer(influencer_id):
    influencer = Influencer.query.get(influencer_id)
    user = User.query.get(influencer.user.user_id)
    if request.method == 'POST':
        new_username = request.form['username']
        influencer.name = request.form['name']
        influencer.category = request.form['category']
        influencer.platform = request.form['platform']
        influencer.reach = request.form['reach']
        password = request.form['password']
        influencer.password = generate_password_hash(request.form['password'])
        confirm_password = request.form['confirm_password']

        if not influencer.name or not new_username or not influencer.password or not confirm_password or not influencer.category or not influencer.platform or not influencer.reach:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('influencer_profile'))
        
        if password != confirm_password:
            flash('danger','Passwords do not match')
            return redirect(url_for('influencer_profile'))
        
        if new_username != user.username:
            user.username = new_username
        
        db.session.commit()
        flash('success','Influencer updated successfully')
        return redirect(url_for('influencer_profile'))
    return render_template('influencer/update.html', influencer=influencer)

#ADMIN PROFILE
@app.route('/admin')
@admin_required
def admin():
    user=User.query.get(session['user_id'])
    campaigns=Campaign.query.all()
    progress_list = []
    for campaign in campaigns:
        today = datetime.datetime.today().date()
        start_date = campaign.start_date
        end_date = campaign.end_date
        
        total_duration = (end_date - start_date).days
        elapsed_time = (today - start_date).days
        
        if elapsed_time < 0:
            progress = 0
        elif elapsed_time > total_duration:
            progress = 100
        else:
            progress = (elapsed_time / total_duration) * 100
        progress_list.append(progress)
    
    flagged_users = db.session.query(Flagged, User).join(User, Flagged.item_id == User.user_id).filter(Flagged.item_type.in_(['Influencer', 'Sponsor'])).all()
    flagged_campaigns = db.session.query(Flagged, Campaign).join(Campaign, Flagged.item_id == Campaign.campaign_id).filter(Flagged.item_type=="Campaign").all()

    return render_template('admin/admin.html',user=user,campaigns=campaigns,progress_list=progress_list, zip=zip, date=datetime.date,flagged_users=flagged_users,flagged_campaigns=flagged_campaigns)

@app.route('/admin/find',methods=['GET','POST'])
@admin_required
def admin_find():
    if request.method == 'POST':
        search_query = request.form.get('search')
        campaigns = Campaign.query.filter(Campaign.name.ilike(f'%{search_query}%')).all()
        sponsors = Sponsor.query.filter(Sponsor.name.ilike(f'%{search_query}%')).all()
        influencers = Influencer.query.filter(Influencer.name.ilike(f'%{search_query}%')).all()
    else:
        campaigns = Campaign.query.all()
        sponsors = Sponsor.query.all()
        influencers = Influencer.query.all()

    return render_template('admin/admin_find.html', campaigns=campaigns, sponsors=sponsors, influencers=influencers)

@app.route('/flag/<int:item_id>/<string:item_type>')
@admin_required
def flag(item_id,item_type):
    if item_type == 'Influencer':
        item = User.query.get(item_id)
        existing_flag = Flagged.query.filter_by(item_id=item.user_id, item_type=item_type).first()
        if existing_flag:
            flash('danger',f'This {item_type} is already flagged')
            return redirect(url_for('admin_find'))
        flagged_item = Flagged(item_id=item.user_id, item_type=item_type)
    elif item_type == 'Sponsor':
        item = User.query.get(item_id)
        existing_flag = Flagged.query.filter_by(item_id=item.user_id, item_type=item_type).first()
        if existing_flag:
            flash(f'This {item_type} is already flagged', 'danger')
            return redirect(url_for('admin_find'))
        flagged_item = Flagged(item_id=item.user_id, item_type=item_type)
    elif item_type == 'Campaign':
        item = Campaign.query.get(item_id)
        existing_flag = Flagged.query.filter_by(item_id=item.campaign_id, item_type=item_type).first()
        if existing_flag:
            flash('danger',f'This {item_type} is already flagged')
            return redirect(url_for('admin_find'))
        flagged_item = Flagged(item_id=item.campaign_id, item_type=item_type)
    else:
        flash('danger','Invalid item type')
        return redirect(url_for('admin_find'))

    if item:
        db.session.add(flagged_item)
        db.session.commit()
        flash('success',f'{item_type} flagged successfully')
    else:
        flash('danger',f'{item_type} not found')
    return redirect(url_for('admin_find'))


@app.route('/remove_flag/<int:flagged_id>')
@admin_required
def remove_flag(flagged_id):
    flag = Flagged.query.get(flagged_id)
    if flag:
        db.session.delete(flag)
        db.session.commit()
        flash('success','Flag removed successfully')
    return redirect(url_for('admin'))

@app.route('/find/search_campaigns',methods=['POST'])
@influencer_required
def search_campaigns():
    search = request.form.get('search')
    budget = request.form.get('budget')
    if not search and not budget:
        flash('Please enter a search query')
        return redirect(url_for('find'))
    if budget:
        campaigns = Campaign.query.filter(Campaign.name.like('%' + search + '%'), Campaign.budget >= budget).all()
    else:
        campaigns = Campaign.query.filter(Campaign.name.like('%' + search + '%')).all()
    user = User.query.get(session['user_id'])
    if user.role == 'Influencer':
        return render_template('influencer/inf_campaign_find.html',campaigns=campaigns, date=datetime.date)
    return render_template('campaign/campaign_find.html', campaigns=campaigns, date=datetime.date)

@app.route('/find_campaign')
@auth_required
def find_campaigns():
    campaigns = Campaign.query.filter_by(visibility="public").all()
    return render_template('campaign/campaign_find.html',campaigns=campaigns,date=datetime.date)

@app.route('/campaign', methods=['GET', 'POST'])
@sponsor_required
def campaign():
    user=User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.user_id).first().sponsor_id
    campaigns=Campaign.query.filter_by(sponsor_id=sponsor).all()
    return render_template('campaign/show.html',campaigns=campaigns,date=datetime.date)

@app.route('/campaign/add', methods=['GET', 'POST'])
@sponsor_required
def add_campaign():
    if request.method=='POST':
        name = request.form['name']
        start_date = datetime.datetime.strptime(request.form['startdate'], '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(request.form['enddate'], '%Y-%m-%d').date()
        budget = request.form['budget']
        description = request.form['description']
        visibility = request.form['visibility']

        user_id=session['user_id']
        user = User.query.get(user_id)
        sponsor = Sponsor.query.filter_by(user_id=user.user_id).first()
        sponsor_id = sponsor.sponsor_id

        if end_date<start_date:
            flash('End date must be after start date')
            return redirect(url_for('add_campaign'))
        if not name or not start_date or not end_date or not budget or not description or not visibility:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('add_campaign'))
        
        campaign = Campaign(sponsor_id=sponsor_id, name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, visibility=visibility)
        db.session.add(campaign)
        db.session.commit()
        flash('success','Campaign added successfully')
        return redirect(url_for('campaign'))
    return render_template('campaign/add.html')

@app.route('/campaign/<int:campaign_id>/delete')
def delete_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        flash('danger','Campaign not found')
        return redirect(url_for('campaign'))
    db.session.delete(campaign)
    db.session.commit()
    flash('success','Campaign deleted successfully')
    return redirect(url_for('campaign'))

@app.route('/campaign/<int:campaign_id>/update', methods=['GET', 'POST'])
@auth_required
def update_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if request.method == 'POST':
        campaign.name = request.form['name']
        campaign.description = request.form['description']
        campaign.start_date = datetime.datetime.strptime(request.form['startdate'], '%Y-%m-%d').date()
        campaign.end_date = datetime.datetime.strptime(request.form['enddate'], '%Y-%m-%d').date()
        campaign.budget = request.form['budget']
        campaign.visibility = request.form['visibility']

        if campaign.end_date<campaign.start_date:
            flash('End date must be after start date')
            return redirect(url_for('update_campaign'))
        if not campaign.name or not campaign.start_date or not campaign.end_date or not campaign.budget or not campaign.description or not campaign.visibility:
            flash('danger','Fields cannot be empty')
            return redirect(url_for('update_campaign'))
        
        db.session.commit()
        flash('success','Campaign updated successfully')
        return redirect(url_for('view_campaign', id=campaign_id))
    
    return render_template('campaign/update.html', campaign=campaign)

@app.route('/campaign/<int:id>')
@auth_required
def view_campaign(id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(id)
    if user.role == 'Admin':
        return render_template('admin/admin_view_campaign.html',campaign=campaign)
    if user.role == 'Influencer':
        return render_template('influencer/inf_view_campaign.html',campaign=campaign)
    return render_template('sponsor/view_campaign.html',campaign=campaign)

@app.route('/find/view/<int:influencer_id>')
@auth_required
def view_influencer(influencer_id):
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(influencer_id)
    if user.role == 'Admin':
        return render_template('admin/admin_view_influencer.html',influencer=influencer)
    return render_template('sponsor/view_influencer.html',influencer=influencer)

@app.route('/find/view_sponsor/<int:sponsor_id>')
@auth_required
def view_sponsor(sponsor_id):
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(sponsor_id)
    if user.role == 'Admin':
        return render_template('admin/admin_view_sponsor.html',sponsor=sponsor)
    return render_template('view_sponsor.html',sponsor=sponsor)

@app.route('/user/<string:user_type>/<int:id>')
@auth_required
def view_user(user_type,id):
    user = User.query.get(id)
    if user_type == 'Influencer':
        influencer = Influencer.query.filter_by(user_id=user.user_id).first()
        return render_template('admin/admin_view_influencer.html', influencer=influencer)
    elif user_type == 'Sponsor':
        sponsor = Sponsor.query.filter_by(user_id=user.user_id).first()
        return render_template('admin/admin_view_sponsor.html',sponsor=sponsor)

@app.route('/send_ad_request/<int:campaign_id>', methods=['GET', 'POST'])
@influencer_required
def send_ad_request(campaign_id):
    if request.method == 'POST':
        user_id = session['user_id']
        user = User.query.get(user_id)
        influencer = Influencer.query.filter_by(user_id=user.user_id).first()
        influencer_id = influencer.influencer_id
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            flash('danger','Campaign not found')
            return redirect(url_for('influencer_profile'))
        
        flagged_campaign = Flagged.query.filter_by(item_id=campaign.campaign_id, item_type='Campaign').first()
        if flagged_campaign:
            flash('danger','This campaign is flagged and cannot send ad requests')
            return redirect(url_for('influencer_profile'))


        ad_request = AdRequest.query.filter_by(influencer_id=influencer_id, campaign_id=campaign_id).first()
        name = request.form.get('name')
        message = request.form.get('message')
        payment_amount = request.form.get('payment')
        
        if not name or not message or not payment_amount:
            flash('danger','Please fill in all the fields')
            return redirect(url_for('influencer_profile'))
        
        ad_request = AdRequest(influencer_id=influencer_id, campaign_id=campaign_id, name=name, messages=message, payment_amount=payment_amount, status='Pending', sender="Influencer")
        db.session.add(ad_request)
        db.session.commit()
        
        flash('success','Ad request sent successfully')
        return redirect(url_for('influencer_profile'))
    
    return render_template('influencer/send_ad_request.html', campaign_id=campaign_id)

@app.route('/view_request/<int:ad_request_id>')
@auth_required
def view_request(ad_request_id):
    adrequest = AdRequest.query.get(ad_request_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user.role=="Influencer":
        return render_template('influencer/inf_view_request.html',adrequest=adrequest)
    return render_template('sponsor/sponsor_view_request.html',adrequest=adrequest)

@app.route('/accept_request/<int:ad_request_id>')
@auth_required
def accept_request(ad_request_id):
    ad_request = AdRequest.query.get(ad_request_id)
    ad_request.status = 'Accepted'
    db.session.commit()
    flash('success','Ad Request accepted successfully')
    if ad_request.sender=="Sponsor":
        return redirect(url_for('influencer_profile'))
    return redirect(url_for('sponsor_profile'))

@app.route('/reject_request/<int:ad_request_id>')
@auth_required
def reject_request(ad_request_id):
    ad_request = AdRequest.query.get(ad_request_id)
    ad_request.status = 'Rejected'
    db.session.commit()
    flash('success','Ad Request rejected successfully')
    if ad_request.sender=="Sponsor":
        return redirect(url_for('influencer_profile'))
    return redirect(url_for('sponsor_profile'))

@app.route('/delete_request/<int:ad_request_id>')
@auth_required
def delete_request(ad_request_id):
    user_id = session['user_id']
    user = User.query.get(user_id)
    ad_request = AdRequest.query.get(ad_request_id)
    db.session.delete(ad_request)
    db.session.commit()
    flash('success','Ad Request deleted successfully')
    if user.role == 'Sponsor':
        return redirect(url_for('sponsor_profile'))
    return redirect(url_for('influencer_profile'))

@app.route('/update_request/<int:ad_request_id>', methods=['GET', 'POST'])
@auth_required
def update_request(ad_request_id):
    ad_request = AdRequest.query.get(ad_request_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    if request.method == 'POST':
        ad_request.name = request.form['name']
        ad_request.messages = request.form['message']
        ad_request.payment_amount = request.form['payment']
        ad_request.status = 'Pending'
        db.session.commit()
        flash('success','Ad Request updated successfully')
        if user.role == 'Sponsor':
            return redirect(url_for('sponsor_profile'))
        return redirect(url_for('influencer_profile'))
    return render_template('update_request.html', ad_request=ad_request,user_role=user.role)

@app.route('/find')
@auth_required
def find():
    influencers = Influencer.query.all()
    return render_template('sponsor/influencer_find.html',influencers=influencers)

@app.route('/find/search_influencers',methods=['POST'])
@sponsor_required
def search_influencers():
    search = request.form.get('search')
    category = request.form.get('category')
    reach = request.form.get('reach')
    if search:
        query = Influencer.query.filter(Influencer.name.like('%' + search + '%'))
    if category:
        query = Influencer.query.filter(Influencer.category.ilike(f'%{category}%'))
    if reach:
        query = Influencer.query.filter(Influencer.reach >= int(reach))
    if not search and not category and not reach:
        flash('Please enter a search query')
        return redirect(url_for('find'))
    influencers = query.all()
    return render_template('sponsor/influencer_find.html', influencers=influencers)

@app.route('/find/new_ad_request', methods=['GET','POST'])
@auth_required
def new_ad_request():
    user=User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.user_id).first().sponsor_id
    campaigns=Campaign.query.filter_by(sponsor_id=sponsor).all()
    influencer_id = request.args.get('influencer_id') or request.form.get('influencer_id')
    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        name = request.form.get('name')
        messages = request.form.get('message')
        payment_amount = request.form.get('payment')
        print(influencer_id,campaign_id,name,messages,payment_amount)
        status = 'Pending'

        flagged_campaign = Flagged.query.filter_by(item_id=campaign_id, item_type='Campaign').first()
        if flagged_campaign:
            flash('danger','This campaign is flagged and cannot send ad requests')
            return redirect(url_for('sponsor_profile'))

        if not influencer_id or not campaign_id or not name or not messages or not payment_amount:
            print(influencer_id,campaign_id,name,messages,payment_amount)
            flash('danger','Fields cannot be empty')
            return redirect(url_for('new_ad_request', influencer_id=influencer_id, campaigns=campaigns, date=datetime.date))

        ad_request = AdRequest(influencer_id=influencer_id, campaign_id=campaign_id, name=name, messages=messages, payment_amount=payment_amount, status=status, sender="Sponsor")
        db.session.add(ad_request)
        db.session.commit()
        flash('success','Ad Request sent successfully')
        return redirect(url_for('sponsor_profile'))
    return render_template('campaign/new_ad_request.html', influencer_id=influencer_id, campaigns=campaigns, date=datetime.date)

@app.route('/admin_stats')
@admin_required
def admin_stats():
    influencers = Influencer.query.all()
    categories = [influencer.category for influencer in influencers]
    category_counts = {category: categories.count(category) for category in set(categories)}
    labels = list(category_counts.keys())
    values = list(category_counts.values())

    total_users = User.query.count()
    flagged_users = Flagged.query.filter(Flagged.item_type.in_(['Influencer', 'Sponsor'])).count()

    total_campaigns = Campaign.query.count()
    flagged_campaigns = Flagged.query.filter(Flagged.item_type=="Campaign").count()

    platforms = [influencer.platform for influencer in influencers]
    platform_counts = {platform: platforms.count(platform) for platform in set(platforms)}
    platform_labels = list(platform_counts.keys())
    platform_values = list(platform_counts.values())
    
    return render_template('admin/stats.html',labels=labels,values=values,total_users=total_users-1,flagged_users=flagged_users,
                           total_campaigns=total_campaigns,flagged_campaigns=flagged_campaigns,platform_labels=platform_labels,platform_values=platform_values)

@app.route('/influencer_stats')
@influencer_required
def influencer_stats():
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    accepted_requests = AdRequest.query.filter_by(influencer_id=influencer.influencer_id,status='Accepted').count()
    rejected_requests = AdRequest.query.filter_by(influencer_id=influencer.influencer_id,status='Rejected').count()
    pending_requests = AdRequest.query.filter_by(influencer_id=influencer.influencer_id,status='Pending').count()

    accepted_budget = 0
    rejected_budget = 0
    pending_budget = 0

    ad_requests = AdRequest.query.all()
    for ad_request in ad_requests:
        if (ad_request.status == 'Accepted' and ad_request.influencer_id==influencer.influencer_id):
            accepted_budget += ad_request.payment_amount
        elif (ad_request.status == 'Rejected' and ad_request.influencer_id==influencer.influencer_id):
            rejected_budget += ad_request.payment_amount
        elif (ad_request.status == 'Pending' and ad_request.influencer_id==influencer.influencer_id):
            pending_budget += ad_request.payment_amount

    
    return render_template('influencer/stats.html',accepted_requests=accepted_requests,rejected_requests=rejected_requests,
                           pending_requests=pending_requests,accepted_budget=accepted_budget, rejected_budget=rejected_budget, pending_budget=pending_budget)

@app.route('/sponsor_stats')
@sponsor_required
def sponsor_stats():
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    accepted_requests = AdRequest.query.filter_by(sender="Sponsor",status='Accepted').count()
    rejected_requests = AdRequest.query.filter_by(sender="Sponsor",status='Rejected').count()
    pending_requests = AdRequest.query.filter_by(sender="Sponsor",status='Pending').count()
    private_campaigns = Campaign.query.filter_by(visibility='private', sponsor_id=sponsor.sponsor_id).count()
    public_campaigns = Campaign.query.filter_by(visibility='public', sponsor_id=sponsor.sponsor_id).count()

    return render_template('sponsor/stats.html', accepted_requests=accepted_requests, rejected_requests=rejected_requests,
                           pending_requests=pending_requests, private_campaigns=private_campaigns, public_campaigns=public_campaigns)


@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))



    