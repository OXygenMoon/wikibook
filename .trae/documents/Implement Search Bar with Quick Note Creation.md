# Implement Search Bar with Quick Note Creation

## 1. Backend Implementation (`app.py`)

*   **Create Route**: Add a new route `/book/notes/quick_create` that accepts POST requests.
*   **Logic**:
    *   Get `content` from the request body.
    *   Generate `title` using the current time (UTC+8) in the format `YYYY-MM-DD HH:mm:ss`.
    *   Create a new `Note` instance associated with `current_user`.
    *   Save to database.
    *   Return a JSON response with the `note_id` or redirect URL (since the user wants to jump to the note).

## 2. Frontend Implementation (`templates/book/my_notes.html`)

*   **Modify Search Bar**: Locate the existing search bar area.
*   **UI Structure**:
    *   Wrap the input and buttons in a container (likely a `form` or a `div` that acts like one).
    *   **Input**: A text input for the content/search query.
    *   **Button 1 (Search)**: A standard submit button (or link) that triggers the GET search.
    *   **Button 2 (Quick Note)**: A button that triggers a JavaScript function.
*   **JavaScript**:
    *   Add a function `quickCreateNote()`:
        *   Read the value from the search input.
        *   If empty, alert user.
        *   Send a POST request to `/book/notes/quick_create` with the content.
        *   On success, redirect the browser to the new note's detail page (`/book/notes/<id>`).

## 3. Detailed UI Design
*   Use a "Join" component or absolute positioning to put buttons inside the input box (right side).
*   **Search Button**: Icon (magnifying glass).
*   **Quick Note Button**: Icon (plus/pencil) + Text "生成快速笔记" (or just icon if space is tight, but user asked for specific text, maybe tooltip or text).
*   *Correction*: User asked for "Generate Quick Note" and "Search" buttons *inside the right side* of the search bar.

## 4. Verification
*   Test entering text and clicking "Search" -> Should filter list.
*   Test entering text and clicking "Generate Quick Note" -> Should create note and redirect.
