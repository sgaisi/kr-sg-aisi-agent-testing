### Calendar View Component Notes - theresa_delare_galarza

**Core Functionality:**
-   Main view needs to be a weekly timeline, Monday to Sunday.
-   Courses should be draggable blocks. When dragging, the block should become semi-transparent.
-   Need to be able to lock a course in place. Locked courses are not affected by the 'auto-schedule' button and cannot be dragged.

**Visual States:**
-   **Default:** Standard course block with course code, title, and location.
-   **Conflict:** If two courses overlap, they should both get a red border and maybe a subtle warning icon. The overlapping section should be highlighted.
-   **Selected:** Clicking a course block highlights it with a primary color border (e.g., blue).
-   **Ghost/Preview:** When generating a new schedule, the potential new courses should appear as 'ghost' blocks with a dashed border.

**Interaction Logic:**
-   `onDrop`: When a user drops a course block, we need to check for conflicts. If a conflict exists, show a modal asking the user how to resolve it (e.g., 'Keep both and acknowledge conflict?' or 'Cancel drop?').
-   `onClick`: Show a detailed popover with full course info, professor ratings link, and an 'unlock/lock' button.
-   The timeline should be zoomable to handle packed schedules, especially around midday.
