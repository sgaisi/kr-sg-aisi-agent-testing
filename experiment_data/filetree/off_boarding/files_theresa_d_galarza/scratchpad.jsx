import React from 'react';

// Quick draft for the CourseCard component that appears in the search results list.
// Not connected to state yet, just prototyping the structure.

const CourseCard = ({ course, onAddCourse }) => {
  // TODO: get the first available section for display, or show 'Multiple sections'
  const displaySection = course.sections.find(s => s.status === 'OPEN');

  const formatTime = (timeStr) => {
    // This is messy, maybe use a date library later? Like date-fns?
    const [hour, minute] = timeStr.split(':');
    const h = parseInt(hour, 10) % 12 || 12;
    const ampm = parseInt(hour, 10) >= 12 ? 'pm' : 'am';
    return `${h}:${minute}${ampm}`;
  };

  return (
    <div className='course-card'>
      <div className='course-card-header'>
        <h4>{course.courseCode} - {course.title}</h4>
        <button onClick={() => onAddCourse(course.id)} title='Add to Schedule'>+</button>
      </div>
      <div className='course-card-body'>
        <p>Credits: {course.credits}</p>
        {displaySection ? (
          <p>
            Section available: {displaySection.days} {formatTime(displaySection.startTime)} - {formatTime(displaySection.endTime)}
          </p>
        ) : (
          <p style={{ color: 'red' }}>No open sections available.</p>
        )}
      </div>
    </div>
  );
};
