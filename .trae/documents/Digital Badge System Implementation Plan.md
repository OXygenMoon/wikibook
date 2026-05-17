# Implement Digital Badge System

## 1. Database Schema Changes (`app.py`)

*   **New Model `Badge`**:
    *   `id`: Integer, Primary Key.
    *   `name`: String (Name of the badge).
    *   `description`: String (Description of how to earn it).
    *   `icon`: String (Emoji or FontAwesome class).
    *   `condition_type`: String (Enum: `streak_days`, `study_hours`, `featured_count`, `note_count`).
    *   `condition_value`: Integer (The threshold value).
    *   `created_at`: DateTime.

*   **New Model `UserBadge`** (Association):
    *   `user_id`: ForeignKey (`User`).
    *   `badge_id`: ForeignKey (`Badge`).
    *   `earned_at`: DateTime.

*   **Update `User` Model**:
    *   `selected_badge_id`: ForeignKey (`Badge`), nullable (The badge currently displayed).
    *   Relationship `badges`: Many-to-Many via `UserBadge`.

## 2. Admin Management (`/admin/badges`)

*   **Route**: `/admin/badges` (List & Create), `/admin/badges/<id>/edit`, `/admin/badges/<id>/delete`.
*   **Template**: `admin/manage_badges.html`.
*   **Functionality**: Allow admins to define badges and their triggering conditions (Type + Threshold).

## 3. Badge Awarding Logic (The Engine)

*   **Service Function**: `check_and_award_badges(user)`
    *   This function will iterate through all **unearned** badges for the user.
    *   Based on `badge.condition_type`, it will query the DB (e.g., count featured notes, calculate study duration).
    *   If condition is met, create `UserBadge` record and flash a notification.

*   **Trigger Points**:
    *   **Study/Streak**: Hook into `/api/heartbeat` (checks `study_hours` and `streak_days`).
    *   **Note Creation**: Hook into `/book/notes/new` (checks `note_count`).
    *   **Featured Note**: Hook into admin's `edit_note` (when toggling `is_featured`).

## 4. User Interface

*   **Badge Wall Page**: `/user/badges`
    *   **Route**: Display all available badges.
    *   **Visuals**:
        *   **Earned**: Full color, with an "Equip/Unequip" button.
        *   **Unearned**: Grayscale/Locked, showing the requirement.
    *   **Entry Point**: Make the username in the Sidebar (`base.html`) clickable, opening this page (or a modal).

*   **Badge Display**:
    *   **Sidebar**: Show the selected badge icon next to the username.
    *   **Online Users**: Update `online_users.html` to show the badge next to names.

## 5. Implementation Steps

1.  **Models**: Add `Badge`, `UserBadge`, update `User` in `app.py` & migrate.
2.  **Admin UI**: Build badge management interface.
3.  **Logic**: Implement `BadgeService` and hooks.
4.  **User UI**: Build Badge Wall and Equip logic.
5.  **Frontend**: Update global display (Sidebar, Online List).

