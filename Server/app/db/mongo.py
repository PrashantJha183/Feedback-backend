import motor.motor_asyncio
from beanie import init_beanie
from app.models.user import User
from app.models.feedback import Feedback
from app.models.feedback_request import FeedbackRequest
from app.models.notification import Notification
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def init_db():
    # Create MongoDB client using URI from .env
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    
    # Get default database from the URI
    database = client.get_default_database()
    
    # Initialize Beanie ODM with your models
    await init_beanie(
        database=database,
        document_models=[
            User,
            Feedback,
            FeedbackRequest,
            Notification
        ]
    )
