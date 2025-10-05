import uuid
#from loguru import logger
from app.core.newrelic_logger import logger
from typing import Optional
from app.models.customer import Customer

class CustomerManager:
    COLLECTION = "customers"

    @property
    def collection(self):   
        from app.core.mongodb_client import db
        if db is None:
            raise RuntimeError("MongoDB not initialized yet")
        return db[self.COLLECTION]
      
    async def get_or_create_customer(self, phone_number: str) -> str:
        """
        Validate phone number via Pydantic model and ensure a persistent customer record.
        Returns the customer_id (string).
        Raises ValidationError if phone is invalid.
        """

        # Validate and normalize phone number with Customer model (temporary id used)
        temp_id = str(uuid.uuid4())
        validated = Customer(_id=temp_id, phone_number=phone_number)
        normalized_phone =  validated.phone_number

        customer = await self.collection.find_one({"phone_number": normalized_phone})
        if customer:
            log = logger.bind(customer_id=customer["_id"], phone_number=phone_number)
            log.info(f"Found existing customer.")
            return customer["_id"]
        
        # Create new customer
        customer_id = str(uuid.uuid4())
        new_customer = {
            "_id": customer_id, 
            "phone_number": phone_number, 
            "name": None, 
            "email": None, 
            "address": None
        }
        await self.collection.insert_one(new_customer)
        log = logger.bind(customer_id=customer_id, phone_number=phone_number)
        log.info(f"Created new customer.")
        return customer_id
    
    async def get_customer(self, phone_number: str) -> Optional[dict]:
        """Fetch full customer record by phone number."""

        customer = await self.collection.find_one({"phone_number": phone_number})
        if customer:
            logger.bind(customer_id=customer["_id"], phone_number=phone_number).info("Fetched customer record.")
            return customer
        return None
    
    async def update_customer(self, customer_id: str, updates: dict) -> None:
        await self.collection.update_one(
            {"_id": customer_id},
            {"$set": updates}
        )
        logger.bind(customer_id=customer_id).info(f"Updated customer with {updates}")