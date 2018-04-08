from flask import Flask, redirect, request, abort, render_template, url_for, flash, sessionfrom flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, url_for_security, current_userfrom flask_security.forms import RegisterForm, LoginForm, StringField, Requiredfrom flask_sqlalchemy import SQLAlchemyimport datetimeimport configapp = Flask(__name__)app.config['SQLALCHEMY_DATABASE_URI'] = config.dbLocationapp.config['SECRET_KEY'] = config.secretKeyapp.config['SECURITY_PASSWORD_HASH'] = "pbkdf2_sha512"app.config['SECURITY_PASSWORD_SALT'] = config.passwordSaltapp.config['SECURITY_REGISTERABLE'] = Trueapp.config['SECURITY_RECOVERABLE'] = Trueapp.config['SECURITY_CHANGABLE'] = Trueapp.config['SECURITY_CONFIRMABLE'] = Falseapp.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['username']app.config['SECURITY_FLASH_MESSAGES'] = Truedb = SQLAlchemy(app)class Stream(db.Model):    __tablename__="Stream"    id = db.Column(db.Integer, primary_key=True)    linkedChannel = db.Column(db.Integer,db.ForeignKey('Channel.id'))    streamKey = db.Column(db.String)    streamName = db.Column(db.String)    currentViewers = db.Column(db.Integer)    def __init__(self, streamKey, streamName, linkedChannel):        self.streamKey = streamKey        self.streamName = streamName        self.linkedChannel = linkedChannel        self.currentViewers = 0    def __repr__(self):        return '<id %r>' % self.id    def add_viewer(self):        self.currentViewers = self.currentViewers + 1        db.session.commit()    def remove_viewer(self):        self.currentViewers = self.currentViewers - 1        db.session.commit()class Channel(db.Model):    __tablename__="Channel"    id = db.Column(db.Integer, primary_key=True)    owningUser = db.Column(db.String(255))    streamKey = db.Column(db.String(255), unique=True)    channelName = db.Column(db.String(255), unique=True)    views = db.Column(db.Integer)    stream = db.relationship('Stream', backref='channel', lazy="joined")    def __init__(self, owningUser, streamKey, channelName):        self.owningUser = owningUser        self.streamKey = streamKey        self.channelName = channelName        self.views = 0    def __repr__(self):        return '<id %r>' % self.idclass ExtendedRegisterForm(RegisterForm):    username = StringField('username', [Required()])roles_users = db.Table('roles_users',        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))class Role(db.Model, RoleMixin):    id = db.Column(db.Integer(), primary_key=True)    name = db.Column(db.String(80), unique=True)    description = db.Column(db.String(255))class User(db.Model, UserMixin):    id = db.Column(db.Integer, primary_key=True)    username = db.Column(db.String(255), unique=True)    email = db.Column(db.String(255), unique=True)    password = db.Column(db.String(255))    active = db.Column(db.Boolean())    confirmed_at = db.Column(db.DateTime())    roles = db.relationship('Role', secondary=roles_users,                            backref=db.backref('users', lazy='dynamic'))# Setup Flask-Securityuser_datastore = SQLAlchemyUserDatastore(db, User, Role)security = Security(app, user_datastore, register_form=ExtendedRegisterForm)db.create_all()def ChannelNameeToKey(channelName):    channel = Channel.query.filter_by(channelName=channelName).first()    if channel is None:        return "*Unknown User*"    else:        return channel.streamKey@app.context_processordef inject_user_info():    return dict(user=current_user)@app.template_filter('normalize_url')def full_name_filter(url):    return url.replace(" ","_")@app.route('/')def main_page():    activeStreams = Stream.query.all()    return render_template('index.html',streamList=activeStreams)@app.route('/view/<user>/')def view_page(user):    streamData = Stream.query.filter_by(streamName=user).first()    streamURL = 'http://' + config.ipAddress + '/live/' + user + '/index.m3u8'    streamData.channel.views = streamData.channel.views + 1    db.session.commit()    return render_template('player.html', stream=streamData, streamURL=streamURL)@app.route('/settings/channels', methods=['POST','GET'])@login_requireddef settings_channels_page():    if request.method == 'GET':        if request.args.get("action") is not None:            action = request.args.get("action")            streamKey = request.args.get("streamkey")            requestedChannel = Channel.query.filter_by(streamKey=streamKey).first()            if action == "delete":                if current_user.username == requestedChannel.owningUser:                    db.session.delete(requestedChannel)                    db.session.commit()                    flash("Channel Deleted")                else:                    flash("Invalid Deletion Attempt","Error")    elif request.method == 'POST':        type = request.form['type']        channelName = request.form['channelName']        streamKey = request.form['streamKey']        if type == 'new':            newChannel = Channel(current_user.username, streamKey, channelName)            db.session.add(newChannel)            db.session.commit()        elif type == 'change':            origStreamKey = request.form['origStreamKey']            requestedChannel = Channel.query.filter_by(streamKey=origStreamKey).first()            if current_user.username == requestedChannel.owningUser:                requestedChannel.channelName = channelName                requestedChannel.streamKey = streamKey                db.session.commit()            else:                flash("Invalid Change Attempt","Error")    user_channels = Channel.query.filter_by(owningUser = current_user.username).all()    return render_template('user_channels.html', channels = user_channels)@app.route('/auth-key', methods=['POST'])def streamkey_check():    key = request.form['name']    ipaddress = request.form['addr']    channelRequest = Channel.query.filter_by(streamKey=key).first()    channelName = channelRequest.channelName.replace(" ","_")    if channelRequest is not None:        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Successful Key Auth', 'key':str(key), 'channelName': str(channelName), 'userName':str(channelRequest.owningUser), 'ipAddress': str(ipaddress)}        print(returnMessage)        newStream = Stream(key,str(channelRequest.channelName),int(channelRequest.id))        db.session.add(newStream)        db.session.commit()        return redirect('rtmp://' + config.ipAddress + '/stream-data/' + channelName, code=302)    else:        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Failed Key Auth', 'key':str(key), 'ipAddress': str(ipaddress)}        print(returnMessage)        return abort(400)@app.route('/auth-user', methods=['POST'])def user_auth_check():    key = request.form['name']    ipaddress = request.form['addr']    channelName = key.replace("_"," ")    streamKey = ChannelNameeToKey(channelName)    authedStream = Stream.query.filter_by(streamKey=streamKey).first()    if authedStream is not None:        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Successful Channel Auth', 'key': str(streamKey), 'channelName': str(channelName), 'ipAddress': str(ipaddress)}        print(returnMessage)        return 'OK'    else:        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Failed Channel Auth. No Authorized Stream Key', 'channelName': str(channelName), 'ipAddress': str(ipaddress)}        print(returnMessage)        return abort(400)@app.route('/deauth-user', methods=['POST'])def user_deauth_check():    key = request.form['name']    ipaddress = request.form['addr']    authedStream = Stream.query.filter_by(streamKey=key).first()    channelRequest = Channel.query.filter_by(streamKey=key).first()    if authedStream is not None:        db.session.delete(authedStream)        db.session.commit()        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Stream Closed', 'key': str(key), 'channelName': str(channelRequest.channelName), 'userName':str(channelRequest.owningUser), 'ipAddress': str(ipaddress)}        print(returnMessage)        return 'OK'    else:        returnMessage = {'time': str(datetime.datetime.now()), 'status': 'Stream Closure Failure - No Such Stream', 'key': str(key), 'ipAddress': str(ipaddress)}        print(returnMessage)        return abort(400)if __name__ == '__main__':    app.jinja_env.auto_reload = True    app.config['TEMPLATES_AUTO_RELOAD'] = True    app.run(debug=False, port=5000)