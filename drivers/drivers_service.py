import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# TODO: Replace this in-memory storage with a persistent database solution
DRIVERS_DB: Dict[int, Dict[str, Any]] = {}
CURRENT_ID = 1

class DriverObject:
    """Object representation of a driver."""
    def __init__(self, id: int, name: str, license_number: str, vehicle_info: Dict[str, Any]):
        self.id = id
        self.name = name
        self.license_number = license_number
        self.vehicle_info = vehicle_info

def create_driver(name: str, license_number: str, vehicle_info: Dict[str, Any]) -> DriverObject:
    """
    Persists a new driver record.

    Creates a new driver record with the provided name, license number,
    and vehicle information.

    :param name: The name of the driver.
    :param license_number: The driver's license number.
    :param vehicle_info: Dictionary containing vehicle information.
    :return: The newly created driver object.
    :raises ValueError: If the provided license number is invalid or name is empty.
    """
    # TODO: Implement license verification logic

    if not name:
        raise ValueError("Driver name cannot be empty.")
    if not license_number:
        raise ValueError("License number cannot be empty.")

    global CURRENT_ID

    logger.info("Creating driver entry in the database.")
    driver_id = CURRENT_ID
    DRIVERS_DB[driver_id] = {
        "name": name,
        "license_number": license_number,
        "vehicle_info": vehicle_info,
    }
    CURRENT_ID += 1
    logger.info("Driver created successfully with ID %s.", driver_id)

    return DriverObject(driver_id, name, license_number, vehicle_info)

def update_vehicle_details(driver_id: int, vehicle_info: Dict[str, Any]) -> DriverObject:
    """
    Updates the driver's vehicle data.

    Updates the vehicle information of an existing driver record.

    :param driver_id: The unique identifier of the driver.
    :param vehicle_info: Dictionary containing vehicle information to update.
    :return: The updated driver object or None if driver not found.
    :raises KeyError: If the driver ID does not exist in the database.
    """
    logger.info("Updating vehicle details for driver with ID %s.", driver_id)

    if driver_id not in DRIVERS_DB:
        return None

    DRIVERS_DB[driver_id]["vehicle_info"] = vehicle_info
    logger.info("Vehicle details updated for driver with ID %s.", driver_id)
    
    driver_data = DRIVERS_DB[driver_id]
    return DriverObject(
        driver_id, 
        driver_data["name"], 
        driver_data["license_number"], 
        driver_data["vehicle_info"]
    )