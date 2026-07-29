from typing import Tuple, Optional, Dict, Any
from app.ai.validators.json_validator import JSONValidator
from app.ai.validators.schema_validator import SchemaValidator
from app.ai.validators.placeholder_validator import PlaceholderValidator
from app.ai.validators.opening_hours_validator import OpeningHoursValidator
from app.ai.validators.distance_validator import DistanceValidator
from app.ai.validators.weather_validator import WeatherValidator
from app.ai.validators.business_validator import BusinessValidator
from app.ai.validators.normalizer import Normalizer

class ItineraryValidator:
    """Orchestrates JSON parsing, Schema, Placeholder, Opening Hours, Distance, Weather, Business validation, and Normalization."""

    @staticmethod
    def validate_and_normalize(
        raw_response: str,
        currency_code: str = "USD",
        weather_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        # Layer 1: JSON Parsing
        ok_json, data, err_json = JSONValidator.parse(raw_response)
        if not ok_json or not data:
            return False, None, err_json or "Failed to parse JSON output"

        # Layer 2: Schema Validation
        ok_schema, err_schema = SchemaValidator.validate(data)
        if not ok_schema:
            return False, None, err_schema

        # Layer 3: Anti-Placeholder Validation
        ok_placeholder, err_placeholder = PlaceholderValidator.validate(data)
        if not ok_placeholder:
            return False, None, err_placeholder

        # Layer 4: Opening Hours & Closed Days Validation
        ok_hours, err_hours = OpeningHoursValidator.validate(data)
        if not ok_hours:
            return False, None, err_hours

        # Layer 5: Geographic Distance & Speed Validation
        ok_dist, err_dist = DistanceValidator.validate(data)
        if not ok_dist:
            return False, None, err_dist

        # Layer 6: Conditional Weather Filter
        ok_weather, err_weather = WeatherValidator.validate(data, weather_info=weather_info)
        if not ok_weather:
            return False, None, err_weather

        # Layer 7: Business Rules & Duplicate Prevention
        ok_biz, err_biz = BusinessValidator.validate(data, target_currency=currency_code)
        if not ok_biz:
            return False, None, err_biz

        # Layer 8: Normalization & Google Maps URLs
        try:
            normalized_data = Normalizer.normalize(data, currency_code=currency_code)
            return True, normalized_data, None
        except Exception as e:
            return False, None, f"Normalization error: {e}"
