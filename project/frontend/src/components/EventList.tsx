import { useMemo } from "react";
import { useEvents } from "../hooks/useEvents";
import type { SortOption } from "./EventSortButton";
import EventImage from "./EventImage";

import "./css/EventList.css";

/*
  This component displays a list of events sorted based on the provided sort option.

  EventListProps:
    EventListProps is a TypeScript interface that defines the props for the EventList component.
    It includes the current sort option.
  
  EventList:
    EventList is a React functional component that fetches events using the useEvents hook,
    sorts them based on the provided sort option, and renders them in a grid layout.
    It handles different sorting options such as title, date, and time in both ascending and descending order.
    If there are no events or an error occurs during fetching, it displays appropriate messages.
  
    parseDate:
      parseDate is a helper function that converts a date string into a timestamp for comparison during sorting.

    parseTimeToMinutes:
      parseTimeToMinutes is a helper function that converts a time string into total minutes for comparison during sorting.

    sortedEvents:
      sortedEvents is a memoized array of events sorted according to the selected sort option.
*/

interface EventListProps {
  sortOption: SortOption;
}

export default function EventList({ sortOption }: EventListProps) {

  // Fetch events and error state using the custom useEvents hook
  const { events, error } = useEvents();

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

  /*
    Memoization:
      useMemo is a React hook that memoizes the result of a computation (in this case, sorting events).
      It only recomputes the sorted array when the dependencies (events or sortOption) change.
      This improves performance by preventing unnecessary re-sorting on every render.
  
  */
  const sortedEvents = useMemo(() => {

    // Creates a copy of events to sort
    const arr = [...events];

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
  }, [events, sortOption]); // Recompute only when events or sortOption change

  // Render error message if there was an error fetching events
  if (error) {
    return <div className="event-list-error">Error: {error}</div>;
  }

  // Render the sorted list of events
  return (

    // Container for the event list
    <div className="event-list">
      {sortedEvents.length === 0 ? (
        <p className="event-list-empty">No events received yet.</p>
      ) : ( 
        
        /*
          Render the grid of event cards.
          
          sortedEvents.map:
            This method iterates over each event in the sortedEvents array and returns a JSX element for each event.
            Each event card displays the event image, title, date, time, location, and description (if available).
          
            dateObj:
              dateObj is a Date object created from the event's start_date string.
              It is used to format the date for display.
              
            dateLabel:
              dateLabel is a formatted string representing the event's start date.
              If the date is invalid, it falls back to displaying the original date string.
              
            timeLabel:
              timeLabel is a string representing the event's start time.
              If no time is provided, it defaults to an empty string.
        */
        <div className="event-grid">
          {sortedEvents.map((event) => {

            const dateObj = new Date(event.start_date); 
            const dateLabel = isNaN(dateObj.getTime()) ? event.start_date : dateObj.toLocaleDateString();
            const timeLabel = event.start_time || "";
            
            /*
              Render individual event card with image, title, date/time, location, and description.
            
            event-card:
              This div represents a single event card in the grid layout.
              It contains the event image, title, date/time, location, and description (if available).
            
              EventImage:
                The EventImage component is used to display the event's image based on the provided imageKey.
                It falls back to a default image if no matching key is found.
              
              event-card__image-placeholder:
                This div serves as a placeholder for the event image, ensuring consistent sizing and layout.

              event-card__title:
                This div displays the title of the event.

              event-card__datetime:
                This div displays the formatted date and time of the event.

              event-card__location:
                This div displays the location of the event, if available.

              event-card__description:
                This div displays the description of the event, if available.

            */
            return (
              <div key={event.id} className="event-card">
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

                {event.description && (
                  <div className="event-card-description">
                    {event.description}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
