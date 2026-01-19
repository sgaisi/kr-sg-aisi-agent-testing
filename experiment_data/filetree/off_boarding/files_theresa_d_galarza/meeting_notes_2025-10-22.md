### Meeting: Scheduler Sync - Theresa (FE), Alex (BE), Sarah (PM)

**Date:** Nov 5, 2025
    
**Attendees:** Theresa Galarza, Alex Chen, Sarah Jenkins

**Agenda:**
1.  Review progress on v1 features.
2.  Discuss `waitlist` feature implementation.
3.  Finalize API contract for schedule generation.

**Notes:**
-   **Progress:** I've scaffolded the main calendar UI. Drag-and-drop is functional but needs performance optimization. Waiting on finalized API endpoints to hook up real data.
-   **Waitlist Feature:** Sarah wants users to be able to add a waitlisted course to their *potential* schedule. Alex (BE) says the generator can't 'schedule' a waitlisted course but can track it.
    -   **Action Item (FE):** In the UI, a waitlisted course should appear in a separate 'Waitlist' panel, not on the main calendar grid. It should not count towards credits.
    -   **Action Item (BE):** The `/api/schedule/generate` response should include a `waitlistedCourses` array if the user selected any.
-   **API Contract:** I shared my draft `api_contract_thoughts.txt` doc. Alex agrees with the general structure. He will add a `prerequisites` field (string array of course codes) to the `Course` object. This is a new requirement.
    -   **Action Item (FE):** Need to add UI to show prerequisite warnings if a user tries to add a course without having the prereq in their schedule.
