import os
import string
import random
import pytz
from datetime import date, datetime, timedelta
import requests as re
from pymongo import MongoClient

# Constants
DB_URI = os.environ.get("DATABASE_URL")
DB_NAME = os.environ.get("DATABASE_NAME")
VERIFY_EXPIRATION_HOURS = 24

async def verify_user(user_id, token):
    try:
        # Connect to the MongoDB database
        client = MongoClient(DB_URI)
        db = client[DB_NAME]

        # Access the 'verification_collection' (replace with your collection name)
        collection = db.verification_collection

        # Find the user's verification data in the collection
        user_data = collection.find_one({"user_id": user_id, "token": token, "status_of_token": "ACTIVE"})

        if user_data:
            # Calculate the expiration time (24 hours from the current time)
            tz = pytz.timezone('Asia/Kolkata')
            expiration_time = datetime.now(tz) + timedelta(hours=VERIFY_EXPIRATION_HOURS)

            # Update the expiration time for the verified user
            collection.update_one(
                {"user_id": user_id, "token": token},
                {"$set": {"expiration_time": expiration_time}}
            )

            # Close the MongoDB connection
            client.close()

            # User is verified
            return True
    except Exception as e:
        # Handle any exceptions (e.g., MongoDB connection issues)
        return False

if __name__ == "__main__":
    # Replace 'your_user_id' and 'your_token' with actual user ID and token
    user_id = "your_user_id"
    token = "your_token"

    is_verified = verify_user(user_id, token)

    if is_verified:
        print("User is verified.")
    else:
        print("User is not verified.")
