from app import app
from flask import request, jsonify
from app.service_paypal import create_paypal_order_service, capture_paypal_order_service
from app.model_order import create_order_db
from app.service_stripe import create_stripe_payment_intent, verify_stripe_payment_intent


@app.route('/api/health', methods = ['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200


@app.route('/api/paypal', methods =['POST'])
def create_paypal_order():
    data = request.get_json() or {}
    response, status_code = create_paypal_order_service(data)

    if not response.get("success"):
        return jsonify(response), status_code
    
    return ({
        "success": True,
        "message": "PayPal order created successfully",
        "data": {
            "paypal_order_id": response.get("paypal_order_id"),
            "paypal_status": response.get("paypal_status"),
            "approval_url": response.get("approval_url")
        }
        
    }), status_code

@app.route("/api/paypal/success", methods = ["POST"])
def paypal_payment_success():
    try:
        data = request.get_json() or {}
        paypal_order_id = str(data.get("paypal_order_id", "")).strip()
        order_payload = data.get("order_data", {})

        if not paypal_order_id:
            return jsonify({
                "success": False,
                "message": "PayPal order ID is required"
            }), 400
        if not order_payload:
            return jsonify({
                "success": False,
                "message": "Order data is required"
            }), 400
        
        # Capture the PayPal Order
        try:
            capture_response , status_code = capture_paypal_order_service(paypal_order_id)
            if not capture_response.get("success"): 
                return jsonify(capture_response), status_code
            capture_data = capture_response.get("capture_response", {})
            if capture_data.get("status") != "COMPLETED":
                    return jsonify({
                        "success": False,
                        "message": "Payment not completed",
                        "details": capture_data
                    }), 400
            paypal_order_id = capture_data.get("id", "")
            order_payload["paypal_status"] = capture_data.get("status", "")

            payer = capture_data.get("payer", {})
            paypal_payer_email = payer.get("email_address", "")
            paypal_payer_id = payer.get("payer_id", "")

            purchase_units = capture_data.get("purchase_units", [])
            capture_id = ""
            capture_status = ""

            if purchase_units:
                payments = purchase_units[0].get("payments", {})
                captures = payments.get("captures", [])
                if captures:
                    capture_id = captures[0].get("id", "")
                    capture_status = captures[0].get("status", "")
            
            order_payload["paypal_payer_id"] = payer.get("payer_id", "")
            order_payload["paypal_order_id"] = capture_data.get("id", "")
            order_payload["paypal_payer_email"] = paypal_payer_email
            order_payload["paypal_capture_id"] = capture_id
            order_payload["paypal_capture_status"] = capture_status
            order_payload["paypal_payer_id"] = payer.get("payer_id", "")
            order_response, order_status_code = create_order_db(order_payload)
            return jsonify(order_response), order_status_code
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Error capturing PayPal order: {str(e)}"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing PayPal success callback: {str(e)}"
        }), 500
    

@app.route("/api/stripe", methods=["POST"])
def create_stripe_payment():
    
    data = request.get_json() or {}
    response, status_code = create_stripe_payment_intent(data)

    if not response.get("success"):
            return jsonify(response), status_code
    
    return jsonify(
            {
            "success": True,
            "message": "Stripe PaymentIntent created successfully",
            "data": {
                "payment_intent_id": response.get("payment_intent_id"),
                "stripe_status": response.get("stripe_status"),
                "client_secret": response.get("client_secret"),
                "return_url": response.get("return_url")
            }
        }
    ), status_code

@app.route("/api/stripe/success", methods = ["POST"])
def stripe_payment_success():
    try:
        data = request.get_json() or {}
        # payment_intent_id = str(data.get("payment_intent_id", "")).strip()
        order_payload = data.get("order_data", {})

        # if not payment_intent_id:
        #     return jsonify({
        #         "success": False,
        #         "message": "Stripe PaymentIntent ID is required"

        #     }),400
        
        # if not order_payload:
        #     return jsonify({
        #         "success": False,
        #         "message": "Order data is required"
        #     }), 400
        
        # verify_response, status_code = verify_stripe_payment_intent(payment_intent_id)

        # if not verify_response.get("success"):
        #     return jsonify(verify_response), status_code
        # payment_intent_id = verify_response.get("payment_intent_id", "")
        # order_payload["stripe_payment_intent_id"] = payment_intent_id
        # order_payload["stripe_status"] = verify_response.get("stripe_status", "")
        # order_payload["stripe_amount_received"] = verify_response.get("amount_received", 0)
        # order_payload["stripe_customer_email"] = verify_response.get("customer_email", "")
        
        order_response, order_status_code = create_order_db(order_payload)
        return jsonify(order_response), order_status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing Stripe success callback: {str(e)}"
        }), 500


