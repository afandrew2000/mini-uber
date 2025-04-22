import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from main import create_app
from config import load_config

# NOTE: We assume that the FastAPI application in main.py includes the rides router
# (from rides.rides_router) so that these endpoints are available at runtime.

@pytest.fixture
def client():
    """
    Fixture to provide a TestClient for the FastAPI app.
    """
    # Create a test-specific FastAPI app
    app = FastAPI()
    
    # Add validation exception handler for test compatibility
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    # Import the rides router
    from rides.rides_router import router as rides_router
    app.include_router(rides_router)
    
    return TestClient(app)

@pytest.fixture
def test_db():
    """
    Fixture for providing a mock or test database session, if needed.
    This can be replaced with a real database session setup if desired.
    """
    # In a real scenario, you might set up an in-memory SQLite or a mock
    # For now, we'll just yield a MagicMock to fulfill the signature
    db_session = MagicMock(spec=Session)
    yield db_session

# -------------------------
# request_ride_endpoint
# -------------------------

def test_request_ride_success(client, test_db):
    """
    Test successful ride request with valid data.
    Expects a 200 or 201 response indicating ride creation.
    """
    request_data = {
        "pickup": "Point A",
        "dropoff": "Point B",
        "additional_info": "Test ride"
    }
    response = client.post("/rides/request_ride", json=request_data)
    assert response.status_code in [200, 201]
    response_json = response.json()
    assert "ride_id" in response_json
    assert response_json["ride_id"] is not None

def test_request_ride_missing_data(client, test_db):
    """
    Test ride request with missing fields.
    Expects a 422 or 400 response due to invalid data.
    """
    # Force a validation error by sending an invalid type for a required field
    request_data = {
        "pickup": 123,  # Should be a string
        "dropoff": "Point B"
    }
    response = client.post("/rides/request_ride", json=request_data)
    assert response.status_code in [400, 422]

# -------------------------
# update_ride_status_endpoint
# -------------------------

def test_update_ride_status_success(client, test_db):
    """
    Test a valid ride status update.
    Expects a 200 response and confirmation of new status.
    """
    # First, create a ride to update
    request_data = {
        "pickup": "Point A",
        "dropoff": "Point B"
    }
    create_response = client.post("/rides/request_ride", json=request_data)
    ride_id = create_response.json()["ride_id"]
    
    # Now update the status with a proper JSON body
    response = client.put(f"/rides/{ride_id}/status", json={"status": "completed"})
    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("ride_id") == ride_id
    assert response_json.get("new_status") == "completed"

def test_update_ride_status_not_found(client, test_db):
    """
    Test ride status update for a non-existent ride.
    Expects a 404 response.
    """
    ride_id = 999999  # Non-existent ride ID
    # Use JSON body with the correct structure
    response = client.put(f"/rides/{ride_id}/status", json={"status": "completed"})
    assert response.status_code == 404

# -------------------------
# get_ride_details_endpoint
# -------------------------

def test_get_ride_details_success(client, test_db):
    """
    Test fetching ride details for a valid ride ID.
    Expects a 200 response and valid ride detail fields in the JSON.
    """
    # First, create a ride to get details for
    request_data = {
        "pickup": "Point A",
        "dropoff": "Point B"
    }
    create_response = client.post("/rides/request_ride", json=request_data)
    ride_id = create_response.json()["ride_id"]
    
    # Now get the details
    response = client.get(f"/rides/{ride_id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json.get("ride_id") == ride_id
    assert "pickup" in response_json
    assert "dropoff" in response_json
    assert "status" in response_json

def test_get_ride_details_not_found(client, test_db):
    """
    Test fetching ride details for a ride ID that does not exist.
    Expects a 404 response.
    """
    ride_id = 999999
    response = client.get(f"/rides/{ride_id}")
    assert response.status_code == 404