import re
from flask import Flask, redirect, url_for, session, request, jsonify, abort
from flask_oauthlib.client import OAuth
from commons import get_config

def create_client(app):
    oauth = OAuth(app)
    
    client={
            "client_key": "0BIL4LcSPStMo3uaTg0P08poicpRHvz0JaOvnRQe", 
            "client_secret": "txXZjoeldivE3QLM1N2Z4C0k7BjKLv6A6OZG2JPygTiU4jJeuK"
            }
    remote = oauth.remote_app(
        get_config('client-cred','client_name'),
        consumer_key=get_config('client-cred','client_key'),
        consumer_secret=get_config('client-cred','client_secret'),
        request_token_params={'scope': 'email'},
        base_url=get_config('client-cred','base-url'),
        request_token_url=None,
        access_token_method='POST',
        access_token_url=get_config('client-cred','access_token_url'),
        authorize_url=get_config('client-cred','authorize_url')
    )
    

    @app.route('/')
    def index():
        if 'dev_token' in session:
            token=session['dev_token']
            return redirect(f"{get_config('client-cred','base-url')}")
        return redirect(url_for('login'))

    @app.route('/login')
    def login():
        return remote.authorize(callback=url_for('authorized', _external=True))

    @app.route('/logout')
    def logout():
        session.pop('dev_token', None)
        return redirect(url_for('index'))

    @app.route('/authorized')
    def authorized():
        
        resp = remote.authorized_response()
        if resp is None:
            return 'Access denied: error=%s' % (
                request.args['error']
            )
        if isinstance(resp, dict) and 'access_token' in resp:
            session['dev_token'] = (resp['access_token'], '')
            # return redirect(url_for('index'))
            return jsonify(resp)
        return str(resp)

    @app.route('/client')
    def client_method():
        ret = remote.get("client")
        if ret.status not in (200, 201):
            return abort(ret.status)
        return ret.raw_data

    @app.route('/address')
    def address():
        ret = remote.get('address/hangzhou')
        if ret.status not in (200, 201):
            return ret.raw_data, ret.status
        return ret.raw_data

    @app.route('/method/<name>')
    def method(name):
        func = getattr(remote, name)
        ret = func('method')
        return ret.raw_data

    @remote.tokengetter
    def get_oauth_token():
        return session.get('dev_token')
         
    return remote


if __name__ == '__main__':
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    # DEBUG=1 python oauth2_client.py
    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'development'
    create_client(app)
    app.run( port=8000)
