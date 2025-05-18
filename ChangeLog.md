# ChangeLog

## 2025-05-18
- Feat:
    - Upsert locations for current year into collection every one hour.
    - get_locations in OpenF1 service first query locations from database, and if there is no result then query from OpenF1 API and insert into the database.
    - Create locations collection index on initialization.

## 2025-05-17
- Added custom Exceptions: OpenF1Error and DatabaseError.
- Changed h2h background color to separate between laps.