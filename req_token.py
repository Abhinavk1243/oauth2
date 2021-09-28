import requests
import base64 
from commons import get_config

def get_token(base_url):
    API_CLIENT=get_config('client-cred','client_key',"oauth2_cred.cfg")
    API_SECRET=get_config('client-cred','client_secret',"oauth2_cred.cfg")
        
    # Encode ID and SECRET in Base64
    base64_basicAuth = (API_CLIENT + ':'+ API_SECRET) .encode("ascii")
    base64_basicAuth = base64.b64encode(base64_basicAuth) 
        
        # Decode ID and SECRET in Base64 for getting 
    base64_basicAuth = base64_basicAuth.decode("ascii") 
    base64_basicAuth = 'Basic ' + base64_basicAuth
    headers = {
        'authorization': base64_basicAuth,
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded'
        }

    params = {
        'grant_type': 'password',
        'username' : 'admin',
        'password': 'admin12'
        }

    auth_url = f"{base_url}/oauth/token"
    api_request = requests.request("POST", auth_url, headers=headers, params = params)
    api_request = api_request.json()
    return api_request["access_token"]

def get_employee(base_url):
    
    res=requests.get(f"{base_url}/employee/",
    headers = {
                'Authorization': f'Bearer {get_token(base_url)}',
                'Content-Type': "application/json"
            }
    )
    
    return res.json()
    
def main():
    
    base_url="http://127.0.0.1:5000"
    print(get_employee(base_url))
    
if __name__ == '__main__':
    main()
    
