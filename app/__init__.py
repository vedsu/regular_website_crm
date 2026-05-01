from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
import json
import boto3

app = Flask(__name__)
CORS(app)
secret_name = "aws-model" # Update with aws secret name
region_name = "us-east-1"
def get_secret(secret_name, region_name):

    try:

        session = boto3.session.Session()
        client = session.client(
            service_name = "secretsmanager",
            region_name = region_name
        )

        response = client.get_secret_value(SecretId = secret_name)
        secret_string = response["SecretString"]
        return json.loads(secret_string)
    
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return {}
    

secret_data = get_secret(secret_name, region_name)

#--- MONGODB CONFIGURATION ---

app.config["MONGO_URI"] = secret_data["MONGODB_RW"]
mongo = PyMongo(app)
db = mongo.db
order_collection = db["order_data"]

#--- AWS S3 CONFIGURATION ---
s3_client = boto3.client(
    service_name = "s3",
    region_name = region_name
)

#--- APP ROUTES CONFIGURATION ---
from app import routes
