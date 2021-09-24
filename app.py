from datetime import datetime, timedelta
import re
from flask import g, json, render_template, request, jsonify, make_response,session,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_oauthlib.provider import OAuth2Provider
from werkzeug.security import gen_salt
import json
from flask import Flask
from werkzeug.utils import header_property
from commons import get_config
import hashlib
app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
app.config.update({
        'SQLALCHEMY_DATABASE_URI': get_config('client-cred','sqlalchemey_conn'),
        'SQLALCHEMY_TRACK_MODIFICATIONS':True
    })

db = SQLAlchemy(app)

app.config.update({'OAUTH2_CACHE_TYPE': 'simple',
                   'OAUTH2_PROVIDER_TOKEN_EXPIRES_IN':5000})

oauth = OAuth2Provider(app)


def hash_password(password):
    password=bytes(password,'utf-8')
    pass_hash = hashlib.md5()
    pass_hash.update(password)
    password=pass_hash.hexdigest()
    print(password)
    return password

def current_user():
    if "user" in session:
        return session["user"]
    return None

@oauth.clientgetter
def get_client(client_id):    
    return Client.query.filter_by(client_id=client_id).first()

@oauth.grantgetter
def get_grant(client_id, code):
    
    return Grant.query.filter_by(client_id=client_id, code=code).first()

@oauth.tokengetter
def get_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    if refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()
    return None

@oauth.grantsetter
def set_grant(client_id, code, request, *args, **kwargs):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        scope=' '.join(request.scopes),
        user_id=session["user"]["id"],
        expires=expires,
        )
    db.session.add(grant)
    db.session.commit()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    from model import db
    toks = Token.query.filter_by(client_id=request.client.client_id,
                                 user_id=request.user.id).all()
    # make sure that every client has only one token connected to a user
    # session["client"]=
    for t in toks:
        db.session.delete(t)

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        scope=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    session["token"]=token['access_token']
    db.session.add(tok)
    db.session.commit()
    return tok


@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user=User.query.filter_by(username=username).first()
    if user==None:
        return user
    if user.password!=hash_password(password):
        return None
    
    session["user"]={"username":user.username,"id":user.id}
    return User.query.filter_by(username=username).first()

@app.errorhandler(401)
def not_found(e):
  return  render_template("401.html",error=e)

@app.route("/")
def welcome():
    # return redirect("/home/")
    return render_template("access_token.html")

@app.route("/onload/")
def onload():
    consumer_key=get_config('client-cred','client_key')
    consumer_secret=get_config('client-cred','client_secret')
    client={"client_key":consumer_key,"client_secret":consumer_secret}
    return jsonify(client)
    

@app.route('/home/')
def home():
    
    return render_template('login.html')

@app.route('/remove_token/')
@oauth.require_oauth()
def logout():
    from model import db
    oauth=request.oauth
    try:
        toks = Token.query.filter_by(client_id=oauth.client.client_id,
                                    user_id=oauth.user.id).all()
        for t in toks:
            db.session.delete(t)
        
        
        return jsonify({"message":"token removed"})
    except:
        return jsonify({"error":"internel server error"})

# @app.route('/client')
# def client():
#     # from model import db
#     username="admin"
#     password=hash_password("admin12")
#     user=User(username=username,password=password)
#     db.session.add(user)
#     db.session.commit()
    
#     client = Client(
#         client_id=get_config('client-cred','client_key'),
#         client_secret=get_config('client-cred','client_secret'),
#         _redirect_uris='/',
#         user_id=1
#     )
#     db.session.add(client)
#     db.session.commit()
#     return jsonify(
#         client_key=client.client_id,
#         client_secret=client.client_secret
#     )


@app.route('/oauth/token', methods=['POST', 'GET'])
@oauth.token_handler
def access_token():
    return {}

@app.route('/oauth/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token():    
    pass

@app.route("/register/",methods=["POST"])
def resgister_user():
    from model import db
    data=request.get_json(force=True)
    username=data["username"]
    password=hash_password(data["password"])
    user=User.query.filter_by(username=username).first()
    if user!=None:
        return jsonify({"message":"user already register"})
    user=User(username=username)
    db.session.add(user)
    db.session.commit()
    user=User.query.filter_by(username=username).first()
    return jsonify({"username":user.username,"user_id":user.id})
    
    
@app.route('/user_detail')
@oauth.require_oauth()
def user_detail():
    oauth=request.oauth
    return jsonify({"username":oauth.user.username,"uid":oauth.user.id})

@app.route('/api/email')
@oauth.require_oauth('email')
def email_api():
    oauth = request.oauth
    return jsonify(email='me@oauth.net', username=oauth.user.username)

@app.route('/api/client')
@oauth.require_oauth()
def client_api():
    oauth = request.oauth
    client={"client_name":oauth.client.name,"client_id":oauth.client.client_id}
    return jsonify(client)

@app.route('/api/address/<city>')
@oauth.require_oauth('address')
def address_api(city):
    oauth = request.oauth
    return jsonify(address=city, username=oauth.user.username)

@app.route('/api/method', methods=['GET', 'POST', 'PUT', 'DELETE'])
@oauth.require_oauth()
def method_api():
    return jsonify(method=request.method)

@oauth.invalid_response
def require_oauth_invalid(req):
    if req.error_message=="Bearer token not found.":
        return jsonify(message="Unauthorized access of URL"), 401
        # return render_template("unoauth.html",error="Unauthorized access of URL")



if __name__=="__main__":
    from model import db,User,Client,Token,Grant
    db.create_all()
    app.run(debug=True)