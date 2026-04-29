import base64
import requests
import json

from app import secret_data


def get_paypal_config():
    
    try:
        mode = secret_data.get("PAYPAL_MODE", "sandbox").strip().lower()
        client_id = secret_data.get("PAYPAL_CLIENT_ID", "").strip()
        client_secret = secret_data.get("PAYPAL_CLIENT_SECRET", "").strip()
        
        if mode == "live":
            base_url = "https://api-m.paypal.com"
        else:
            base_url = "https://api-m.sandbox.paypal.com"
            
        return {
            "mode": mode,
            "client_id" : client_id,
            "client_secret" : client_secret,
            "base_url": base_url
        }, 200
    except Exception as e:
        print(f"Error retrieving PayPal config: {e}")
        return (str(e)), 500
    
def get_paypal_access_token():
    try:
        config, status_code = get_paypal_config()
        client_id  = config.get("client_id")
        client_secret = config.get("client_secret")
        base_url = config.get("base_url")

        if not client_id  or not client_secret:
            return {
                "success":False,
                "message": "Paypal Credentials missing"
            }, 500
        
        auth_string = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        headers ={
            "Authorization" : f"Basic {encoded_auth}",
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(
                f"{base_url}/v1/oauth2/token" ,
                headers = headers,
                data = data,
                timeout = 30
            )

            response_data = response.json()
            if response.status_code != 200:
                return {
                    "success" :False,
                    "message" : response_data.get("error_description", "Failed to retrieve access token"),
                    "details" : response_data
                }, response.status_code
            
            return {
                "success": True,
                "access_token": response_data.get("access_token"),
                "token_type": response_data.get("token_type"),
                "expires_in": response_data.get("expires_in"),
                "app_id": response_data.get("app_id")
            }, 200
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during token request: {str(e)}"
            }, 500

    except Exception as e:
        return {
            "success": False,
            "message": f"Error in get_paypal_access_token: {str(e)}"
        }, 500

def create_paypal_order_service(data):
    try:
        token_response, status_code = get_paypal_access_token()
        if not token_response.get("success"):
            return token_response, status_code

        config, status_code = get_paypal_config()
        base_url = config.get("base_url")
        access_token = token_response.get("access_token")

        # Extract order details from route data
        amount_value = str(data.get("amount_value", "0")).strip()
        currency_code = data.get("currency_code", "USD").strip().upper()
        webinar_name = data.get("webinar_name", "WEBINAR").strip() # Replace with Billing Email
        return_url = data.get("return_url", "").strip()
        cancel_url = data.get("cancel_url", "").strip()


        if not amount_value or amount_value == "0":
            return {
                "success": False,
                "message": "Invalid amount value"
            }, 400
        if not return_url or not cancel_url:
            return {
                "success": False,
                "message": "Return URL and Cancel URL are required" 
            }, 400
        
        headers = {
            "Content-Type" : "application/json",
            "Authorization": f"Bearer {access_token}",

        }

        payload = {
            "intent": "CAPTURE",
            "purchase_units":[
                {
                    "description": webinar_name, # Replace with Billing Email
                    "amount": {
                        "currency_code": currency_code,
                        "value": amount_value
                    }
                }
            ],
            "application_context":{
                "return_url" : return_url,
                "cancel_url" : cancel_url
            }
        }


        try:
            response = requests.post(
                f"{base_url}/v2/checkout/orders",
                headers = headers,
                json = payload,
                timeout = 30
            )

            response_data = response.json()

            if response.status_code not in [200, 201]:
                return {
                    "success": False,
                    "message": response_data.get("message", "Failed to create PayPal order"),
                    "details": response_data
                }, response.status_code
            
            approval_url =""
            for link in response_data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href", "")
                    break

            return {
                "success": True,
                "paypal_order_id": response_data.get("id"),
                "paypal_status": response_data.get("status"),
                "approval_url": approval_url,
                "raw_response": response_data
            }, 200
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during order creation: {str(e)}"
            }, 500
        

    except Exception as e:
        return {
            "success": False,
            "message": f"Error in create_paypal_order_service: {str(e)}"
        }, 500
    

def capture_paypal_order_service(paypal_order_id):
    if not paypal_order_id:
        return {
            "success": False,
            "message": "PayPal order ID is required for capture"
            }, 400
    token_response, status_code = get_paypal_access_token()
    if not token_response.get("success"):
        return token_response, status_code
    config, status_code = get_paypal_config()
    access_token = token_response.get("access_token")
    base_url = config.get("base_url")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.post(
            f"{base_url}/v2/checkout/orders/{paypal_order_id}/capture",
            headers = headers,
            timeout = 30
        )

        response_data = response.json()

        if response.status_code not in [200, 201]:
            return {
                "success": False,
                "message": response_data.get("message", "Failed to capture PayPal order"),
                "details": response_data
            }, response.status_code
        
        return {
            "success": True,
            "paypal_order_id": paypal_order_id,
            "capture_response": response_data
        }, 200
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during order capture: {str(e)}"
        }, 500




        