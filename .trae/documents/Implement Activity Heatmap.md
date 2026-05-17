# Implement Activity Heatmap (GitHub Style)

## 1. Backend Implementation (`app.py`)

*   **Create API Endpoint**: `/api/stats/heatmap` (GET)
*   **Data Aggregation Logic**:
    *   Target `StudySession` model (which already tracks user activity).
    *   Query sessions for the `current_user` within the last 1 year (365 days).
    *   Aggregate `duration` (seconds) by date (`YYYY-MM-DD`).
    *   **Bonus**: Also count `Note` creations per day to enrich the "activity" metric?
        *   *Decision*: For now, let's focus on **Study Duration** as the primary metric, as it reflects "active time". Alternatively, we can combine count + duration, but duration is more granular. Let's stick to duration (seconds) for the heatmap value.
    *   Return format: `[["2023-01-01", 1234], ["2023-01-02", 0], ...]`

## 2. Frontend Implementation (`templates/book/my_notes.html`)

*   **Add ECharts Library**: Include ECharts via CDN.
*   **Add Container**: Insert a `<div id="activity-heatmap" style="height: 200px;"></div>` into the "My Notes" dashboard (likely inside the stats card or a new card).
*   **Initialize Chart**:
    *   Fetch data from `/api/stats/heatmap`.
    *   Configure ECharts:
        *   **Calendar**: Set range to current year (or rolling last 12 months).
        *   **Heatmap**: Map date to X, duration to value.
        *   **VisualMap**: Define color gradient (Light Green -> Dark Green).
        *   **Tooltip**: Show formatted duration (e.g., "2h 30m") on hover.

## 3. UI/UX Details
*   **Color Scheme**: Use a GitHub-like green palette (`#ebedf0`, `#9be9a8`, `#40c463`, `#30a14e`, `#216e39`).
*   **Placement**: Place it prominently at the top of the "My Notes" page, replacing or augmenting the current text-based stats.

## 4. Verification
*   Check if the chart renders correctly.
*   Verify data matches the "Study Stats" table.
*   Ensure the API returns correct JSON.
