# Real-time Online Users & Study Time Tracking Plan

## 1. Database Schema Update
### New Models
- **`UserActiveStatus`**: Tracks real-time user presence.
    - `user_id` (PK, FK)
    - `last_active_at` (DateTime)
    - `current_path` (String)
    - `current_action` (String)
- **`StudySession`**: Tracks study duration segments.
    - `id` (PK)
    - `user_id` (FK)
    - `start_time` (DateTime)
    - `end_time` (DateTime)

### Migration
- Update `migrate_db.py` to create these new tables in the existing SQLite database.

## 2. Backend Implementation (`app.py`)
### Heartbeat API (`/api/heartbeat`)
- Receives `current_path` from frontend every 30 seconds.
- Updates `UserActiveStatus`.
- Manages `StudySession`:
    - Extends current session if `last_active` was < 5 min ago.
    - Creates new session if gap > 5 min.

### Online Users Page (`/online_users`)
- Renders a list of users active in the last 5 minutes.
- Shows their avatar, name, and current activity (inferred from path).

### Study Stats Calculation
- Helper function to calculate total duration for: Today, Week, Month, 3 Months, 6 Months, Year, Total.
- Inject `online_user_count` into all templates via `context_processor`.
- Update `/book/my_notes` route to pass study stats to the template.

## 3. Frontend Implementation
### Base Template (`base.html`)
- **JavaScript**: Add heartbeat script (fetch API every 30s).
- **UI**: Add "Online: X" badge in the navbar (linking to `/online_users`).

### Online Users Page (`templates/online_users.html`)
- Create a new clean interface listing active users.

### My Stats Page (`templates/book/my_notes.html`)
- Add a new "Study Time" section with statistics cards/table showing duration for different time ranges.
