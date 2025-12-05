import { useMemo, useState, useCallback } from "react";
import { useEvents } from "../hooks/useEvents";
import type { SortOption } from "./EventSortButton";
import EventImage from "./EventImage";
import LikeButton from "./LikeButton";
import { useNavigate } from "react-router-dom";

import "./css/EventList.css";

/*
  This file defines the EventList component, which displays a list of events with sorting and filtering capabilities.

  Sections:

  EventList Component:
    - Fetches events using the useEvents hook.
    - Manages liked events state to track which events the user has liked.
    - Provides sorting functionality based on the selected sort option.
    - Renders the list of events, including event images, titles, dates, locations, and like buttons.
  
  Helper Functions:
    - parseDate: Converts date strings into timestamps for sorting.
    - parseTimeToMinutes: Converts time strings into total minutes for sorting.
*/

interface EventListProps {
  sortOption: SortOption;
  showLikedOnly?: boolean;
  suggestedEventIds?: number[] | null;  // Filter to show only suggested events for user
}

export default function EventList({ sortOption, showLikedOnly = false, suggestedEventIds }: EventListProps) {

  // -------------- Initialization --------------

  // Fetch events and error state using the custom useEvents hook
  const { events, error } = useEvents();
  const navigate = useNavigate();

  // State to track liked event IDs - triggers re-render when likes change
  const [likedEventIds, setLikedEventIds] = useState<number[]>(() => {
    return JSON.parse(localStorage.getItem("likedEvents") || "[]");
  });

  // -------------- Helper Functions --------------

  // Callback to update liked events state when a like/unlike happens
  const handleLikeChange = useCallback((eventId: number, isLiked: boolean) => {

    setLikedEventIds(prev => {
      if (isLiked) {
        return [...prev, eventId];
      } else {
        return prev.filter(id => id !== eventId);
      }
    });

  }, []);

  // Helper function to parse date strings into timestamps
  const parseDate = (dateStr?: string | null) => {
    if (!dateStr) return NaN; // Handle null or undefined

    const d = new Date(dateStr); // Create Date object

    return d.getTime(); // Return timestamp (milliseconds since epoch)
  };

  // Helper function to parse time strings into total minutes
  const parseTimeToMinutes = (timeStr?: string | null) => {

    // Handle null or undefined
    if (!timeStr) return NaN;

    // Extract "HH:MM" part and split into hours and minutes
    const clean = timeStr.split(" ")[0]; // "HH:MM" or first part before spaces
    const [hh, mm] = clean.split(":");
    const h = Number(hh);
    const m = Number(mm ?? "0");

    // Handle invalid numbers: return NaN if parsing fails
    if (isNaN(h) || isNaN(m)) return NaN;

    // Convert to total minutes
    return h * 60 + m;
  };

  // -------------- Sort Events --------------

  const sortedEvents = useMemo(() => {

    // Start with all events
    let filteredEvents = events;

    // Filter by suggested event IDs if provided
    if (suggestedEventIds && suggestedEventIds.length > 0) {
      filteredEvents = filteredEvents.filter(event => suggestedEventIds.includes(event.id));
    }

    // Filter events if showLikedOnly is enabled (uses state instead of reading from localStorage)
    if (showLikedOnly) {
      filteredEvents = filteredEvents.filter(event => likedEventIds.includes(event.id));
    }

    // Creates a copy of filtered events to sort
    const arr = [...filteredEvents];

    /*
      Sort the events array based on the selected sort option.

      a is the first event being compared.
      b is the second event being compared.
    */
    arr.sort((a, b) => {

      /*
        switch (sortOption):
          This switch statement evaluates the sortOption variable to determine how to sort the events.
          Each case corresponds to a different sorting criterion (title, date, time) and order (ascending, descending).
          
          at is the title of event a in lowercase.
          bt is the title of event b in lowercase.
      
      */
      switch (sortOption) {

        // Sort by title in ascending order (A to Z)
        case "title-asc": {
          const at = (a.title || "").toLowerCase();
          const bt = (b.title || "").toLowerCase();

          return at.localeCompare(bt); // Compare titles lexicographically (A to Z)
        }

        // Sort by title in descending order (Z to A)
        case "title-desc": {
          const at = (a.title || "").toLowerCase();
          const bt = (b.title || "").toLowerCase();

          return bt.localeCompare(at); // Compare titles lexicographically (Z to A)
        }

        // Sort by date in ascending order (earliest to latest)
        case "date-asc": {

          const ad = parseDate(a.start_date);
          const bd = parseDate(b.start_date);

          return (isNaN(ad) ? 0 : ad) - (isNaN(bd) ? 0 : bd); // Compare dates (earliest to latest)
        }

        // Sort by date in descending order (latest to earliest)
        case "date-desc": {
          const ad = parseDate(a.start_date);
          const bd = parseDate(b.start_date);

          return (isNaN(bd) ? 0 : bd) - (isNaN(ad) ? 0 : ad); // Compare dates (latest to earliest)
        }

        // Sort by time in ascending order (earliest to latest)
        case "time-asc": {
          const at = parseTimeToMinutes(a.start_time);
          const bt = parseTimeToMinutes(b.start_time);

          return (isNaN(at) ? 0 : at) - (isNaN(bt) ? 0 : bt); // Compare times (earliest to latest)
        }

        // Sort by time in descending order (latest to earliest)
        case "time-desc": {
          const at = parseTimeToMinutes(a.start_time);
          const bt = parseTimeToMinutes(b.start_time);

          return (isNaN(bt) ? 0 : bt) - (isNaN(at) ? 0 : at); // Compare times (latest to earliest)
        }

        // Default case: no sorting or unrecognized sort option
        default:
          return 0;
      }
    });

    // Return the sorted array
    return arr;
  }, [events, sortOption, showLikedOnly, likedEventIds, suggestedEventIds]); // Recompute when any filter/sort criteria change

  // -------------- Check for Error --------------

  // Render error message if there was an error fetching events
  if (error) {
    return <div className="event-list-error">Error: {error}</div>;
  }

  // -------------- Render Component --------------

  return (

    // Container for the event list
    <div className="event-list">
      {sortedEvents.length === 0 ? (
        <p className="event-list-empty">No events received yet.</p>
      ) : ( 
        
        /*
          Render the grid of event cards.
        */
        <div className="event-grid">
          {sortedEvents.map((event) => {

            const dateObj = new Date(event.start_date); 
            const dateLabel = isNaN(dateObj.getTime()) ? event.start_date : dateObj.toLocaleDateString();
            const timeLabel = event.start_time || "";
            
            /*
              Render individual event card with image, title, date/time, location, and description.
            */
            return (
              <div 
              key={event.id} 
              className="event-card" onClick={() => navigate(`/events/${event.id}`)}
              role="button"
              tabIndex={0}>
                <div className="event-card-image-wrapper">
                  <EventImage
                    imageKey={event.image_key}
                    title={event.title}
                    className="event-card-image"
                  />
                </div>

                <div className="event-card-title">{event.title}</div>

                <div className="event-card-datetime">
                  {dateLabel}
                  {timeLabel && ` ${timeLabel}`}
                </div>

                {event.location && (
                  <div className="event-card-location">{event.location}</div>
                )}

                <div className="event-card-actions">
                  <LikeButton 
                    eventId={event.id} 
                    initialLikeCount={event.like_count} 
                    size="small"
                    onLikeChange={handleLikeChange}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
