'use client';

import { Calendar, momentLocalizer, View } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useState } from 'react';

const localizer = momentLocalizer(moment);

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  location?: string;
  description?: string;
  event_type?: string;
  color_id?: string;
}

interface EventCalendarProps {
  events: Array<{
    id: string;
    title: string;
    start: string;
    end: string;
    location?: string;
    description?: string;
    event_type?: string;
    color_id?: string;
  }>;
  onEventClick?: (event: CalendarEvent) => void;
}

export function EventCalendar({ events, onEventClick }: EventCalendarProps) {
  const [view, setView] = useState<View>('week');
  const [date, setDate] = useState(new Date());

  // Convert API events to calendar format
  const calendarEvents: CalendarEvent[] = events.map(event => ({
    id: event.id,
    title: event.title,
    start: new Date(event.start),
    end: new Date(event.end),
    location: event.location,
    description: event.description,
    event_type: event.event_type,
    color_id: event.color_id,
  }));

  // Google Calendar color mappings (official colors)
  const getGoogleCalendarColor = (colorId?: string) => {
    const colors: { [key: string]: { bg: string; border: string; text: string } } = {
      '1': { bg: '#a4bdfc', border: '#7da7ea', text: '#1d1d1d' },  // Lavender
      '2': { bg: '#7ae7bf', border: '#46d6a0', text: '#1d1d1d' },  // Sage
      '3': { bg: '#dbadff', border: '#c58af9', text: '#1d1d1d' },  // Grape
      '4': { bg: '#ff887c', border: '#f06463', text: '#1d1d1d' },  // Flamingo
      '5': { bg: '#fbd75b', border: '#f2c246', text: '#1d1d1d' },  // Banana
      '6': { bg: '#ffb878', border: '#f5a449', text: '#1d1d1d' },  // Tangerine
      '7': { bg: '#46d6db', border: '#29cccc', text: '#1d1d1d' },  // Peacock
      '8': { bg: '#e1e1e1', border: '#cacaca', text: '#1d1d1d' },  // Graphite
      '9': { bg: '#5484ed', border: '#3b6fd9', text: '#ffffff' },  // Blueberry
      '10': { bg: '#51b749', border: '#3ea338', text: '#ffffff' }, // Basil
      '11': { bg: '#dc2127', border: '#c41e23', text: '#ffffff' }, // Tomato
    };

    return colors[colorId || ''] || { bg: '#a4bdfc', border: '#7da7ea', text: '#1d1d1d' }; // Default to Lavender
  };

  // Custom event styling based on Google Calendar colors
  const eventStyleGetter = (event: CalendarEvent) => {
    // If event has a Google Calendar color, use it
    if (event.color_id) {
      const color = getGoogleCalendarColor(event.color_id);
      return {
        style: {
          backgroundColor: color.bg,
          borderColor: color.border,
          borderWidth: '2px',
          borderStyle: 'solid',
          borderRadius: '8px',
          color: color.text,
          padding: '4px 8px',
          fontSize: '13px',
          fontWeight: '500',
        }
      };
    }

    // Fallback for events without color_id (assignment blocks, bus suggestions)
    let backgroundColor = '#a4bdfc'; // Default Lavender
    let borderColor = '#7da7ea';
    let textColor = '#1d1d1d';

    if (event.event_type === 'assignment') {
      // Use Grape (purple) for assignments
      backgroundColor = '#dbadff';
      borderColor = '#c58af9';
    } else if (event.event_type === 'commute') {
      // Use Peacock (blue) for bus/commute
      backgroundColor = '#46d6db';
      borderColor = '#29cccc';
    }

    return {
      style: {
        backgroundColor,
        borderColor,
        borderWidth: '2px',
        borderStyle: 'solid',
        borderRadius: '8px',
        color: textColor,
        padding: '4px 8px',
        fontSize: '13px',
        fontWeight: '500',
      }
    };
  };

  return (
    <div className="bg-white rounded-xl p-4 border border-rose/20 shadow-sm">
      <style jsx global>{`
        .rbc-calendar {
          font-family: inherit;
          min-height: 600px;
        }
        .rbc-header {
          padding: 12px 4px;
          font-weight: 600;
          color: #9333EA;
          border-bottom: 2px solid #E9D5FF;
          background-color: #FAF5FF;
        }
        .rbc-today {
          background-color: #FFF7ED;
        }
        .rbc-event {
          padding: 4px 8px;
          border-radius: 8px;
        }
        .rbc-event:focus {
          outline: 2px solid #9333EA;
        }
        .rbc-toolbar button {
          color: #9333EA;
          border: 1px solid #E9D5FF;
          padding: 8px 16px;
          border-radius: 8px;
          background-color: white;
          font-weight: 500;
          transition: all 0.2s;
        }
        .rbc-toolbar button:hover {
          background-color: #FAF5FF;
          border-color: #9333EA;
        }
        .rbc-toolbar button.rbc-active {
          background-color: #9333EA;
          color: white;
          border-color: #9333EA;
        }
        .rbc-toolbar button.rbc-active:hover {
          background-color: #7E22CE;
        }
        .rbc-time-slot {
          min-height: 40px;
        }
        .rbc-current-time-indicator {
          background-color: #F87171;
          height: 2px;
        }
        .rbc-day-slot .rbc-time-slot {
          border-top: 1px solid #F3F4F6;
        }
        .rbc-timeslot-group {
          border-left: 1px solid #E5E7EB;
        }
        .rbc-time-header-content {
          border-left: 1px solid #E5E7EB;
        }
        .rbc-time-content {
          border-top: 2px solid #E9D5FF;
        }
      `}</style>

      <Calendar
        localizer={localizer}
        events={calendarEvents}
        startAccessor="start"
        endAccessor="end"
        view={view}
        onView={setView}
        date={date}
        onNavigate={setDate}
        eventPropGetter={eventStyleGetter}
        onSelectEvent={onEventClick}
        style={{ height: '600px' }}
        views={['month', 'week', 'day']}
        defaultView="week"
        step={30}
        showMultiDayTimes
        popup
        min={new Date(1970, 1, 1, 6, 0, 0)}
        max={new Date(1970, 1, 1, 23, 59, 0)}
      />
    </div>
  );
}
