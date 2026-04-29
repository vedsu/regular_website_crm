import base64
import requests
import json
import stripe

from app import secret_data

def get_stripe_config():
    try:
        stripe.api_key = secret_data.get("STRIPE_SECRET_KEY", "")
        return  {
            "success": True,
            "message": "Stripe configuration loaded successfully"
        }, 200
    except Exception as e:
        stripe.api_key = ""
        return {
            "success": False,       
            "message": f"Error loading Stripe configuration: {str(e)}"
        }, 500  
    


def create_stripe_payment_intent(data):
    
    config_response, status_code = get_stripe_config()
    if not config_response.get("success"):
        return config_response, status_code
    customer_email = data.get("customeremail", "")
    webinar_name = str(data.get("webinar_name", "WEBINAR")).strip()
    amount = data.get("amount_value", 0)
    customer_name = data.get("customername", "")
    currency = data.get("currency_code", "USD").lower()
    country = data.get("country", "")
    return_url = data.get("return_url", "")
    zip_code = data.get("zip_code", "")

    try:
        intent = stripe.PaymentIntent.create(
            amount = int(float(amount) * 100), # Convert to cents
            currency = currency,
            receipt_email = customer_email,
            description = f"Payment for {webinar_name}",
            metadata = {
                "customer_name": customer_name,
                "country": country,
                "zip_code": zip_code}
            )

        return {
            "success": True,
            "message": "Stripe PaymentIntent created successfully",
            "payment_intent_id": intent.get("id"),
            "stripe_status": intent.get("status"),
            "client_secret": intent.get("client_secret"),
            "return_url": return_url
            }, 200
    
    except stripe.error.StripeError as e:
        return {
            "success": False,
            "message": getattr(e, "user_message", None) or str(e)
        }, 400
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in create_stripe_payment_intent_service: {str(e)}"
        }, 500


def verify_stripe_payment_intent(payment_intent_id):
    try:
        if not payment_intent_id:
            return {
                "success": False,
                "message": "Stripe PaymentIntent ID is required"
            }, 400
        stripe.api_key = secret_data.get("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            return {
                "success": False,
                "message": "Stripe API key is not configured"
            }, 500 
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.get("status") == "succeeded":
            return {
                "success": True,
                "message": "PaymentIntent verified successfully",
                "payment_intent_id": intent.get("id"),
                "stripe_status": intent.get("status"),
                "amount_received": intent.get("amount_received"),
                "customer_email": intent.get("receipt_email"),
                
            }, 200
        else:
            return {
                "success": False,
                "message": f"PaymentIntent status is {intent.get('status')}, expected 'succeeded'"
            }, 400
        
    except stripe.error.StripeError as e:
        return {
            "success": False,
            "message": getattr(e, "user_message", None) or str(e)
        }, 400
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in verify_stripe_payment_intent_service: {str(e)}"
        }, 500