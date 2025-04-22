import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# In-memory database for riders
_in_memory_riders_db: Dict[int, Dict[str, Any]] = {}
_next_id = 1

def create_rider(name: str, phone_number: str, payment_method: str) -> dict:
    """
    Persists a new rider record in the database.
    
    :param name: Full name of the rider
    :param phone_number: The rider's phone number
    :param payment_method: Selected payment method for the rider
    :return: A dictionary representing the newly created rider
    :raises ValueError: If required parameters are invalid
    :raises Exception: For any other unexpected database or application errors
    """
    if not name or not phone_number or not payment_method:
        raise ValueError("Invalid input. 'name', 'phone_number' and 'payment_method' are required.")
    
    try:
        global _next_id
        
        rider_id = _next_id
        _next_id += 1
        
        new_rider = {
            "id": rider_id,
            "name": name,
            "phone_number": phone_number,
            "payment_method": payment_method
        }
        
        # Store in our in-memory database
        _in_memory_riders_db[rider_id] = new_rider
        
        logger.info("Rider created successfully.")
        return new_rider
    except Exception as e:
        logger.error("Error creating rider: %s", str(e))
        raise


def fetch_rider(rider_id: int) -> Optional[dict]:
    """
    Retrieves a rider record from the database by rider_id.
    
    :param rider_id: The unique identifier of the rider
    :return: A dictionary representing the rider if found, otherwise None
    :raises ValueError: If the rider_id is invalid
    :raises Exception: For any other unexpected database or application errors
    """
    if rider_id <= 0:
        raise ValueError("Invalid 'rider_id'. It must be a positive integer.")
    
    try:
        # Get the rider from our in-memory database

        return _in_memory_riders_db.get(rider_id)
    except Exception as e:
        logger.error("Error fetching rider with ID %d: %s", rider_id, str(e))
        raise
