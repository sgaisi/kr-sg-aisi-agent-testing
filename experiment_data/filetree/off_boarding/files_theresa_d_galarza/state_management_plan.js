// Tentative Redux/Zustand store structure

const initialState = {
  // Data from API
  allCourses: [], // Full list of available courses for the semester
  departments: [], // For filtering UI

  // User's current working schedule
  currentSchedule: {
    id: 'schedule-temp-123',
    courses: [
      // Example of a scheduled course section
      {
        courseId: 'CS101-01',
        sectionId: 'A1',
        isLocked: false, // User can lock a course to prevent auto-rescheduling
        // ...other relevant section details for rendering
      }
    ],
  },

  // User-defined constraints for the generator
  userPreferences: {
    noFridayClasses: true,
    preferMornings: false,
    maxCredits: 18,
    avoidTimeGaps: { enabled: true, maxGapMinutes: 60 },
  },

  // UI-specific state
  ui: {
    isLoading: false, // For API calls
    isGenerating: false, // For the scheduler algorithm
    errorMessage: null,
    selectedCourseId: null, // ID of the course block the user clicked on
    conflictInfo: { // Details of any conflicts to show in the UI
      hasConflict: false,
      conflictingCourses: [],
    },
  },
};
