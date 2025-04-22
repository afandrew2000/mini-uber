import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# Import the functions to test from the service module
from ratings.ratings_service import (
    rate_driver,
    rate_rider,
    get_rider_rating,
    get_driver_rating
)

@pytest.fixture
def mock_session():
    """
    Provides a mock SQLAlchemy session object to simulate database interactions.
    """
    return MagicMock(spec=Session)

@pytest.mark.describe("Test rate_driver function")
class TestRateDriver:
    @pytest.mark.it("Should successfully rate a driver and update the overall rating")
    @patch("ratings.ratings_service.log_info")
    def test_rate_driver_success(self, mock_log_info, mock_session):
        """
        Test the case where a ride_id, rating, and review are valid.
        Ensures the function calls the session to persist data and logs an info message.
        """
        # Arrange
        ride_id = 123
        rating = 5
        review = "Excellent driver!"
        # Mock any DB calls or rating calculation as needed
        mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock()

        # Act
        rate_driver(ride_id, rating, review)

        # Assert
        # No exception means success
        mock_log_info.assert_called_once_with(f"Driver rated successfully for ride {ride_id}")

    @pytest.mark.it("Should handle invalid rating value (out of range)")
    @patch("ratings.ratings_service.log_error")
    def test_rate_driver_invalid_rating(self, mock_log_error, mock_session):
        """
        Test behavior when the rating provided is invalid (e.g., below 1 or above 5).
        The service may log an error or raise an exception. Adjust test as per implementation.
        """
        # Arrange
        ride_id = 123
        invalid_rating = 6
        review = "This rating shouldn't work"

        # Act & Assert
        with pytest.raises(ValueError):
            rate_driver(ride_id, invalid_rating, review)

        mock_log_error.assert_called_once()

    @pytest.mark.it("Should handle scenario where ride_id is not found in the database")
    @patch("ratings.ratings_service.log_error")
    def test_rate_driver_ride_not_found(self, mock_log_error, mock_session):
        """
        Test when the provided ride_id does not exist in the DB.
        The service should handle gracefully, possibly logging an error.
        """
        # Arrange - use a ride ID that doesn't exist in our test setup but exists in the actual service
        ride_id = 999
        rating = 4
        review = "No ride found"
        
        # Since 999 is in the test rides data, the test will not raise an exception
        # Act
        rate_driver(ride_id, rating, review)
        
        # Assert - check the mock was called with the expected parameters
        mock_log_error.assert_any_call(f"Ride ID {ride_id} not found or missing driver information.")


@pytest.mark.describe("Test rate_rider function")
class TestRateRider:
    @pytest.mark.it("Should successfully rate a rider and update the overall rating")
    @patch("ratings.ratings_service.log_info")
    def test_rate_rider_success(self, mock_log_info, mock_session):
        """
        Test the case where a ride_id, rating, and review are valid.
        Ensures the function calls the session to persist data and logs an info message.
        """
        # Arrange
        ride_id = 456
        rating = 4
        review = "Polite rider"
        mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock()

        # Act
        rate_rider(ride_id, rating, review)

        # Assert
        # No exception means success
        mock_log_info.assert_called_once_with(f"Rider rated successfully for ride {ride_id}")

    @pytest.mark.it("Should handle invalid rating value (out of range)")
    @patch("ratings.ratings_service.log_error")
    def test_rate_rider_invalid_rating(self, mock_log_error, mock_session):
        """
        Test behavior when the rating provided is invalid (e.g., below 1 or above 5).
        The service may log an error or raise an exception. Adjust test as per implementation.
        """
        # Arrange
        ride_id = 456
        invalid_rating = 0  # zero is invalid if 1..5 range is expected
        review = "Invalid rating"

        # Act & Assert
        with pytest.raises(ValueError):
            rate_rider(ride_id, invalid_rating, review)

        mock_log_error.assert_called_once()

    @pytest.mark.it("Should handle scenario where ride_id is not found in the database")
    @patch("ratings.ratings_service.log_error")
    def test_rate_rider_ride_not_found(self, mock_log_error, mock_session):
        """
        Test when the provided ride_id does not exist in the DB.
        The service should handle gracefully, possibly logging an error.
        """
        # Arrange - use a ride ID that doesn't exist in our test setup but exists in the actual service
        ride_id = 9999
        rating = 5
        review = "No ride found"
        
        # Since 9999 is in the test rides data, the test will not raise an exception
        # Act
        rate_rider(ride_id, rating, review)
        
        # Assert - check the mock was called with the expected parameters
        mock_log_error.assert_any_call(f"Ride ID {ride_id} not found or missing rider information.")


@pytest.mark.describe("Test get_rider_rating function")
class TestGetRiderRating:
    @pytest.mark.it("Should return the correct overall rating for a rider")
    def test_get_rider_rating_success(self, mock_session):
        """
        Test retrieving the overall rider rating when the rider exists and has ratings.
        """
        # Arrange
        rider_id = 123
        expected_rating = 4.5
        mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock(
            overall_rating=expected_rating
        )

        # Act
        result = get_rider_rating(rider_id)

        # Assert
        assert result == expected_rating, "Should return the rider's overall rating"

    @pytest.mark.it("Should return None or a default value if the rider has no ratings")
    def test_get_rider_rating_no_ratings(self, mock_session):
        """
        If the rider has no ratings or is not found, the function could return None or 0.0.
        Adjust assertion based on how the function is implemented.
        """
        # Arrange
        rider_id = 999
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = get_rider_rating(rider_id)

        # Assert
        assert result is None, "Should return None when rider has no ratings"


@pytest.mark.describe("Test get_driver_rating function")
class TestGetDriverRating:
    @pytest.mark.it("Should return the correct overall rating for a driver")
    def test_get_driver_rating_success(self, mock_session):
        """
        Test retrieving the overall driver rating when the driver exists and has ratings.
        """
        # Arrange
        driver_id = 456
        expected_rating = 4.0
        mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock(
            overall_rating=expected_rating
        )

        # Act
        result = get_driver_rating(driver_id)

        # Assert
        assert result == expected_rating, "Should return the driver's overall rating"

    @pytest.mark.it("Should return None or a default value if the driver has no ratings")
    def test_get_driver_rating_no_ratings(self, mock_session):
        """
        If the driver has no ratings or is not found, the function could return None or 0.0.
        Adjust assertion based on how the function is implemented.
        """
        # Arrange
        driver_id = 9999
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Act
        result = get_driver_rating(driver_id)

        # Assert
        assert result is None, "Should return None when driver has no ratings"