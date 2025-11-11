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
  }));

  // Custom event styling based on event type
  const eventStyleGetter = (event: CalendarEvent) => {
    let backgroundColor = '#FFB3C1'; // Default rose color
    let borderColor = '#FF85A1';

    if (event.event_type === 'assignment') {
      backgroundColor = '#E9D5FF'; // Purple
      borderColor = '#C084FC';
    } else if (event.event_type === 'commute') {
      backgroundColor = '#BFDBFE'; // Blue
      borderColor = '#60A5FA';
    }

    // Check if event title contains "bhangra" (case insensitive)
    if (event.title.toLowerCase().includes('bhangra')) {
      backgroundColor = '#FCA5A5'; // Red/pink for bhangra
      borderColor = '#F87171';
    }

    return {
      style: {
        backgroundColor,
        borderColor,
        borderWidth: '2px',
        borderStyle: 'solid',
        borderRadius: '8px',
        color: '#1f2937',
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
      />
    </div>
  );
}
