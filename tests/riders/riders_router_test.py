import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from unittest.mock import patch, MagicMock

# Import the router for direct testing
from riders.riders_router import router as riders_router

@pytest.fixture
def client():
    """
    Fixture to initialize a test FastAPI application with just the riders router
    and proper validation error handling.
    """
    app = FastAPI()
    
    # Add validation exception handler to convert 422 to 400 status codes
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.errors()}
        )
    
    # Include only the riders router for focused testing
    app.include_router(riders_router)
    
    return TestClient(app)

def test_create_rider_endpoint_success(client):
    """
    Test the rider creation endpoint with valid data.
    Expects 201 status and a success response structure.
    """
    # Arrange
    expected_result = {
        "id": 1,
        "name": "John Doe",
        "phone_number": "1234567890",
        "payment_method": "credit_card"
    }
    
    request_data = {
        "name": "John Doe",
        "phone_number": "1234567890",
        "payment_method": "credit_card"
    }
    
    # Patch the create_rider function used in the endpoint
    with patch("riders.riders_router.create_rider", return_value=expected_result) as mock_create_rider:
        # Act
        response = client.post("/riders", json=request_data)
        
        # Assert
        assert response.status_code == 201, f"Expected 201 Created but got {response.status_code}"
        assert response.json()["id"] == 1
        mock_create_rider.assert_called_once_with(
            name="John Doe",
            phone_number="1234567890",
            payment_method="credit_card"
        )


def test_create_rider_endpoint_bad_request(client):
    """
    Test the rider creation endpoint with incomplete data.
    Expects a 400 Bad Request for invalid payload.
    """
    request_data = {
        # 'name' is missing
        "phone_number": "1234567890",
        "payment_method": "credit_card"
    }

    response = client.post("/riders", json=request_data)

    # The endpoint should validate input and return 400
    assert response.status_code == 400, f"Expected 400 Bad Request but got {response.status_code}"


def test_get_rider_profile_endpoint_success(client):
    """
    Test the get rider profile endpoint with an existing rider ID.
    Expects 200 status and correct rider data in the response.
    """
    expected_result = {
        "id": 2,
        "name": "Jane Roe",
        "phone_number": "0987654321",
        "payment_method": "paypal"
    }
    rider_id = 2

    with patch("riders.riders_router.fetch_rider", return_value=expected_result) as mock_fetch_rider:
        response = client.get(f"/riders/{rider_id}")

        assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
        assert response.json()["id"] == 2
        assert response.json()["name"] == "Jane Roe"
        mock_fetch_rider.assert_called_once_with(rider_id=2)


def test_get_rider_profile_endpoint_not_found(client):
    """
    Test the get rider profile endpoint with a non-existent rider ID.
    Expects 404 status when the rider is not found.
    """
    rider_id = 999  # Non-existent rider ID for testing

    with patch("riders.riders_router.fetch_rider", return_value=None) as mock_fetch_rider:
        response = client.get(f"/riders/{rider_id}")

        assert response.status_code == 404, f"Expected 404 Not Found but got {response.status_code}"
        mock_fetch_rider.assert_called_once_with(rider_id=999)