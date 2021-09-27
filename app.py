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
from commons import get_config,mysl_pool_connection,logger
import hashlib
import pandas as pd 

logger=logger()
pool_cnxn=mysl_pool_connection("mysql_web_data")
mycursor=pool_cnxn.cursor

app = Flask(__name__)
app.debug = True
app.secret_key = 'development'
app.config.update({
        'SQLALCHEMY_DATABASE_URI': get_config('client-cred','sqlalchemey_conn',"oauth2_cred.cfg"),
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
    consumer_key=get_config('client-cred','client_key',"oauth2_cred.cfg")
    consumer_secret=get_config('client-cred','client_secret',"oauth2_cred.cfg")
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


@app.route("/dashboard/")
@oauth.require_oauth()
def dashboard():
    return render_template("about_us.html")

# @app.route("/test/",methods=["GET","POST"])
# def test():
#     if request.method=="POST":
        
#         data=request.get_json(force=True)
#         return data
#     return render_template("table.html")
#     # return data


@app.route("/student/",methods=["GET"])
@oauth.require_oauth()
def get_student():
    if request.args:            
        mycursor=pool_cnxn.cursor()
        query_params_dict=request.args.to_dict()
        sql="select * from  web_data.student " 
        no_of_cond=0
        for i in list(query_params_dict.keys()):
            if no_of_cond==0:
                if (query_params_dict[i]).isalpha:
                    sql=sql+f"  where {i}='{query_params_dict[i]}' "
                else:
                    sql=sql+f" and {i}=int({query_params_dict[i]})"
                no_of_cond=1
            else:
                if (query_params_dict[i]).isalpha:
                    sql=sql+f" and {i}='{query_params_dict[i]}' "
                else:
                    sql=sql+f" and {i}=int({query_params_dict[i]})"
        try:
            mycursor.execute(sql)
            student=mycursor.fetchall()
        except Exception as error:
            return jsonify({"error":"internal server error"}),500
        if student==[]:
            message=f"error :'record at {query_params_dict} not found '"
            return jsonify({"error":message}),400
        else:
            # if request.content_type=="application/json":
            df=pd.read_sql(con=pool_cnxn, sql=sql)
            student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
            response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","data":student}}
            return jsonify(response)   
            # return render_template("student.html",**locals())         
    else:
        sql="select * from  web_data.student "
        # if request.content_type=="application/json":
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
        response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","data":student}}
        return jsonify(response)  ,200
    
@app.route("/student/",methods=["POST"])
@oauth.require_oauth()
def create_student():  
    student_data=request.get_json(force=True)
    mycursor=pool_cnxn.cursor()  
    try:
        
        student_name=student_data['student_name']
        student_age=student_data['student_age']
    except KeyError as error:
        example_data={"student_name":"name","student_age":54}
        return jsonify({"error":"data contain wrong keys","sample_data":example_data}),400

    val=(student_name,student_age)
    try:
        sql=f"insert into web_data.student(student_name, student_age) values {val}"
        mycursor.execute(sql)
        pool_cnxn.commit()
        logger.debug(f"data {val} successfully inserted")
        print("data inserted")
    except Exception as error:
        logger.error(f"exception arise : {error}")
        # print(f"Exception arise : {error}")
        return jsonify({"error":"internal server error"}),500
    df=pd.read_sql(con=pool_cnxn, sql='SELECT * FROM web_data.student ORDER BY student_id DESC LIMIT 1')
    student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
    return jsonify(student[0])

@app.route("/student/",methods=['DELETE'])
@oauth.require_oauth()
def remove_student():
    if request.method=='DELETE':        
        mycursor=pool_cnxn.cursor()
        try:
            student_data=request.get_json(force=True)
            student_id=student_data["student_id"]
        except KeyError as error:
            return jsonify({"error":"key error in data","sample_data":{"student_id":34}}),500
        sql=f"""select student_id,student_name,student_age from web_data.student where student_id={student_id}"""
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
        if student==[]:
            error=f"student with id {student_id} not exist"
            return jsonify({"error":error}),400
        try:
            sql=f"delete from  web_data.student where student_id={student_id} "
            mycursor.execute(sql)
            pool_cnxn.commit()            
            logger.debug(f"record of id = {id} is deleted from the database")
        except Exception as error:
            logger.error(f"exception arise : {error}")
            print(f"Exception arise : {error}")
            return jsonify({"error":"internal server error"}),500             
    return jsonify({"response":"student is successfully removed from database","removed_student_record":student})

@app.route("/student/",methods=["PUT"])
@oauth.require_oauth()
def student_update(): 
    mycursor=pool_cnxn.cursor()
    student_data=request.get_json(force=True)
    try:
        student_name=student_data["student_name"]
        student_age=student_data['student_age']
        student_id=student_data['student_id']
        logger.debug(student_id)
    except Exception as error:
        logger.error(error)
        return jsonify({"error":error})
    mycursor.execute(f"select student_id from web_data.student where student_id={student_id}")
    if mycursor.fetchone()==None:
        error=f"student with id {student_id} not exist"
        return jsonify({"error":error}),400
    try:
        sql=f"""update web_data.student set student_name='{student_name}',
        student_age={student_age} where student_id={student_id}"""
        mycursor.execute(sql)
        pool_cnxn.commit()
        print(f"Data updatated successfully")
    except Exception as error:
        logger.error(f"error arise : {error}")
        return jsonify({"error":"internal server error"})
    df=pd.read_sql(con=pool_cnxn, sql=f'SELECT * FROM web_data.student where student_id={student_id}')
    student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
    res={"response_msg":"student record successfully updated",
        "data":student[0]}
    return jsonify(res)

@oauth.invalid_response
def require_oauth_invalid(req):
    if req.error_message=="Bearer token not found.":
        return jsonify(message="Unauthorized access of URL"), 401
        # return render_template("unoauth.html",error="Unauthorized access of URL")

    
if __name__=="__main__":
    from model import db,User,Client,Token,Grant
    # 
    db.create_all()
    # from student_bp import student_bp
    # app.register_blueprint(student_bp,url_prefix="/student")
    # 
    app.run(debug=True)
    