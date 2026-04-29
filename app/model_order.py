from datetime import datetime
import random
import string
import pytz
from app import order_collection


def create_order_db(order_data):
    try:
        order_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        order_data["order_id"] = order_id
        utc = pytz.utc
        indian = pytz.timezone("Asia/Kolkata")
        eastern = pytz.timezone("US/Eastern")

        now_utc = datetime.now(utc)
        order_data["created_at_utc"] = now_utc
        order_data["created_at_ist"] = now_utc.astimezone(indian)
        order_data["created_at_est"] = now_utc.astimezone(eastern)
        
        order_collection.insert_one(order_data)

        return {
            "success": True,
            "message": "Order created successfully",
            "data": {
                "order_id": order_id
            }
        }, 201

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating order: {str(e)}"
        }, 500