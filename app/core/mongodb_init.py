import app.core.mongodb_client as mongo_client
from loguru import logger

async def init_mongodb():
    """
    Initialize MongoDB collections and indexes.
    Run this during app startup.
    """
    if mongo_client.db is None:
        await mongo_client.connect_to_mongo()

    # Customers collection index (already present)
    customers = mongo_client.db["customers"]
    await customers.create_index("phone_number", unique=True)

    # Conversations collection: index for queries by customer_id, session_id and created_at
    conversations = mongo_client.db["conversation"]
    await conversations.create_index("conversation_id", unique=True)
    await conversations.create_index([("customer_id", 1), ("created_at", -1)])
    await conversations.create_index("session_id")


    logger.info("MongoDB initialized: 'customers' + 'conversations' collection with unique index on phone_number")
