import pytest
from unittest.mock import patch, MagicMock
import sys

# Import the service functions
from riders.riders_service import create_rider, fetch_rider, _in_memory_riders_db

@pytest.fixture
def reset_db():
    """
    Fixture to reset the in-memory database before each test
    """
    # Store original values
    original_db = _in_memory_riders_db.copy()
    
    # Clear the database for the test
    _in_memory_riders_db.clear()
    
    # Reset the _next_id directly in the module
    riders_service_module = sys.modules['riders.riders_service']
    original_next_id = riders_service_module._next_id
    riders_service_module._next_id = 1
    
    yield
    
    # Restore original values after test
    _in_memory_riders_db.clear()
    _in_memory_riders_db.update(original_db)
    riders_service_module._next_id = original_next_id


def test_create_rider_success(reset_db):
    """
    Test that create_rider successfully persists a new rider with valid data.
    """
    # Act
    created_rider = create_rider(
        name="John Doe", 
        phone_number="1234567890", 
        payment_method="CreditCard"
    )

    # Assert
    assert created_rider is not None
    assert created_rider["id"] == 1
    assert created_rider["name"] == "John Doe"
    assert created_rider["phone_number"] == "1234567890"
    assert created_rider["payment_method"] == "CreditCard"
    
    # Verify it was added to the in-memory database
    assert 1 in _in_memory_riders_db
    assert _in_memory_riders_db[1]["name"] == "John Doe"


def test_create_rider_error_invalid_phone(reset_db):
    """
    Test that create_rider handles an invalid phone number scenario (e.g. empty).
    """
    # In our implementation, empty phone_number should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        create_rider(name="Jane Doe", phone_number="", payment_method="CreditCard")
    
    assert "Invalid input" in str(exc_info.value)
    assert len(_in_memory_riders_db) == 0  # Database should remain empty


def test_fetch_rider_success(reset_db):
    """
    Test that fetch_rider returns the correct rider when the rider exists.
    """
    # Setup: Create a test rider first
    test_rider = create_rider(
        name="Alice",
        phone_number="9876543210",
        payment_method="PayPal"
    )
    rider_id = test_rider["id"]
    
    # Act
    rider = fetch_rider(rider_id=rider_id)
    
    # Assert
    assert rider is not None
    assert rider["id"] == rider_id
    assert rider["name"] == "Alice"
    assert rider["phone_number"] == "9876543210"
    assert rider["payment_method"] == "PayPal"


def test_fetch_rider_not_found(reset_db):
    """
    Test that fetch_rider returns None when no rider is found.
    """
    # Act: Try to fetch a non-existent rider ID
    rider = fetch_rider(rider_id=999)
    
    # Assert
    assert rider is None, "Expected None when rider does not exist"