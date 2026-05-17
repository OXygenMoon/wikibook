# Implement "Focus Mode" Table of Contents

## 1. Modify `templates/wiki/view_page.html`

### A. CSS Styles
- Add `.toc-ellipsis` class for the "..." indicators: centered text, subtle color, refined look.
- Ensure `toc-link` has a fixed height or consistent spacing to prevent layout jitter.

### B. HTML Structure
- Update `#toc-container`:
    - Remove `overflow-y-auto`.
    - Add `overflow-hidden`.
    - Keep `max-h` (or let the item limit define the height).

### C. JavaScript Logic
- Enhance the TOC generation script:
    - Insert "top ellipsis" and "bottom ellipsis" elements into the container.
    - Implement `updateTOCVisibility(activeIndex)`:
        - define `WINDOW_SIZE = 5` (show 5 items above and 5 below active).
        - Loop through all links:
            - Show if index is within `[active - WINDOW_SIZE, active + WINDOW_SIZE]`.
            - Hide otherwise.
        - Toggle top ellipsis if `active - WINDOW_SIZE > 0`.
        - Toggle bottom ellipsis if `active + WINDOW_SIZE < total - 1`.
- Update the `IntersectionObserver` callback:
    - When a new link becomes active, call `updateTOCVisibility`.
- Handle initial state (highlight first item or none).

## 2. Refinement
- Ensure smooth transitions if possible (optional, maybe simple show/hide is snappier and less buggy).
- Ensure "Word Count" remains at the bottom.

## 3. Verification
- Check if TOC updates correctly when scrolling.
- Check if clicking a link updates the TOC window.
- Verify no scrollbars appear.
