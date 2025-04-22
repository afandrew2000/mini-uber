import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import from project root based on provided structure
from rides.rides_service import create_ride, assign_driver_to_ride, update_ride_status, RideServiceError


@pytest.fixture(scope="module")
def client():
    """
    Fixture to initialize the FastAPI application and return a test client.
    """
    from main import create_app
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_db():
    """
    Fixture to provide a mocked database session or in-memory DB for testing.
    """
    # You would typically set up an in-memory SQLite DB or a mock Session here.
    # For demonstration, we'll return a MagicMock to stand in for a Session.
    return MagicMock(spec=Session)


# Reset the in-memory database before each test
@pytest.fixture(autouse=True)
def reset_rides_db():
    """Reset the in-memory RIDES_DB and CURRENT_RIDE_ID before each test"""
    from rides.rides_service import RIDES_DB, AVAILABLE_DRIVERS
    import copy
    
    # Store original values
    original_drivers = copy.deepcopy(AVAILABLE_DRIVERS)
    
    # Clear for testing
    RIDES_DB.clear()
    AVAILABLE_DRIVERS.clear()
    AVAILABLE_DRIVERS.extend(["driver123", "driver456", "driver789"])
    
    yield
    
    # Cleanup
    RIDES_DB.clear()
    AVAILABLE_DRIVERS.clear()
    AVAILABLE_DRIVERS.extend(original_drivers)


def test_create_ride_success(test_db):
    """
    Test that create_ride successfully creates a new ride record when valid inputs are provided.
    """
    # Arrange
    rider_id = "123"  # String as per implementation
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}

    # Act
    new_ride_id = create_ride(rider_id, pickup_location, dropoff_location)

    # Assert
    assert isinstance(new_ride_id, int)
    from rides.rides_service import RIDES_DB
    assert new_ride_id in RIDES_DB
    assert RIDES_DB[new_ride_id]["rider_id"] == rider_id
    assert RIDES_DB[new_ride_id]["pickup_location"] == pickup_location
    assert RIDES_DB[new_ride_id]["dropoff_location"] == dropoff_location


def test_create_ride_failure_invalid_rider(test_db):
    """
    Test that create_ride raises an exception or handles errors when the rider_id is invalid.
    For demonstration, we assume an invalid rider_id triggers a ValueError.
    """
    # Arrange
    invalid_rider_id = None  # Missing rider ID
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}

    # Act & Assert
    with pytest.raises(RideServiceError):
        create_ride(invalid_rider_id, pickup_location, dropoff_location)


def test_assign_driver_to_ride_success(test_db):
    """
    Test that assign_driver_to_ride assigns an available driver to an existing ride successfully.
    """
    # Arrange - Create a ride first
    rider_id = "123"
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}
    ride_id = create_ride(rider_id, pickup_location, dropoff_location)
    
    # Act
    driver_id = assign_driver_to_ride(ride_id)

    # Assert
    assert driver_id is not None
    from rides.rides_service import RIDES_DB
    assert RIDES_DB[ride_id]["driver_id"] == driver_id
    assert RIDES_DB[ride_id]["status"] == "driver_assigned"


def test_assign_driver_to_ride_no_available_driver(test_db):
    """
    Test that assign_driver_to_ride handles the case where no drivers are available.
    """
    # Arrange - Create a ride first and exhaust all drivers
    rider_id = "123"
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}
    ride_id = create_ride(rider_id, pickup_location, dropoff_location)
    
    # Exhaust all drivers
    from rides.rides_service import AVAILABLE_DRIVERS
    AVAILABLE_DRIVERS.clear()
    
    # Act
    driver_id = assign_driver_to_ride(ride_id)

    # Assert
    assert driver_id is None
    from rides.rides_service import RIDES_DB
    assert RIDES_DB[ride_id]["driver_id"] is None


def test_assign_driver_to_ride_ride_not_found(test_db):
    """
    Test that assign_driver_to_ride handles the case when the ride does not exist.
    """
    # Arrange
    ride_id = 999  # Non-existent ride ID

    # Act & Assert
    with pytest.raises(RideServiceError):
        assign_driver_to_ride(ride_id)


def test_update_ride_status_success(test_db):
    """
    Test that update_ride_status successfully updates the ride status when provided valid ride_id and status.
    """
    # Arrange - Create a ride first
    rider_id = "123"
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}
    ride_id = create_ride(rider_id, pickup_location, dropoff_location)
    
    # Act
    update_ride_status(ride_id, "in-progress")

    # Assert
    from rides.rides_service import RIDES_DB
    assert RIDES_DB[ride_id]["status"] == "in-progress"


def test_update_ride_status_invalid_ride(test_db):
    """
    Test that update_ride_status raises an error when the ride does not exist in the database.
    """
    # Arrange
    ride_id = 9999  # Non-existent ride ID
    new_status = "canceled"

    # Act & Assert
    with pytest.raises(RideServiceError):
        update_ride_status(ride_id, new_status)


def test_update_ride_status_invalid_status(test_db):
    """
    Test that update_ride_status handles invalid status strings appropriately.
    For demonstration, we assume an invalid status triggers a ValueError.
    """
    # Arrange - Create a ride first
    rider_id = "123"
    pickup_location = {"lat": 40.7128, "lng": -74.0060}
    dropoff_location = {"lat": 40.73061, "lng": -73.935242}
    ride_id = create_ride(rider_id, pickup_location, dropoff_location)
    
    invalid_status = "invalid-status"

    # Act & Assert
    with pytest.raises(RideServiceError):
        update_ride_status(ride_id, invalid_status)