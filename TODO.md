# TODO: Implement Filtering and Search for Properties

## 1. Update Property Model
- [ ] Add 'type' field to Property model in models.py (e.g., String(50), nullable=True)

## 2. Create Database Migration
- [ ] Generate Alembic migration for adding 'type' column to properties table
- [ ] Run migration to update database schema
- [ ] (Optional) Add indexes on city, rent_amount, and type fields

## 3. Update GET /properties Endpoint
- [ ] Remove @token_required decorator from get_properties function
- [ ] Add logic to check for Authorization header
  - If token present: authenticate user and filter properties by user (landlord/tenant)
  - If no token: perform public search with filters
- [ ] Implement query parameter handling:
  - location: filter by city (case-insensitive)
  - price_min: filter rent_amount >= price_min
  - price_max: filter rent_amount <= price_max
  - type: filter by property type
- [ ] Handle dynamic combinations of filters using SQLAlchemy
- [ ] Add logging for search queries (console output)
- [ ] Return 200 with results or 404 if no properties found
- [ ] Handle invalid/missing filters gracefully

## 4. Testing
- [ ] Test endpoint with various filter combinations
- [ ] Test with and without authentication token
- [ ] Verify existing user-specific functionality still works
- [ ] Check logging output for search queries
