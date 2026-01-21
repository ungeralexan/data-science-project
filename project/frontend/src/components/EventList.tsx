import { useMemo, useState, useEffect } from "react";
import { Pagination, Spin } from "antd";
import { useEvents } from "../hooks/useEvents";
import type { EventFetchMode } from "../hooks/useEvents";
import { useAuth } from "../hooks/useAuth";
import type { SortOption } from "./buttons/EventSortButton";
import type { Event } from "../types/Event";
import EventImage from "./EventImage";
import LikeButton from "./buttons/LikeButton";
import GoingButton from "./buttons/GoingButton";
import ShareButton from "./buttons/ShareButton";
import { useNavigate } from "react-router-dom";

import { matchesEvent } from "../utils/search";
import { PAGINATION } from "../config";

import "./css/EventList.css";
import LoadingOutlined from "@ant-design/icons/lib/icons/LoadingOutlined";
import Paragraph from "antd/es/typography/Paragraph";

/*
  This file defines the EventList component, which displays a list of events with sorting and filtering capabilities.

  Sections:

  EventList Component:
    - Fetches events using the useEvents hook.
    - Uses AuthContext to track liked events (shared across browsers via database).
    - Provides sorting functionality based on the selected sort option.
    - Renders the list of events, including event images, titles, dates, locations, and like buttons.
  
  Helper Functions:
    - parseDate: Converts date strings into timestamps for sorting.
    - parseTimeToMinutes: Converts time strings into total minutes for sorting.
*/

interface EventListProps {
  sortOption: SortOption;
  showLikedOnly?: boolean;
  showGoingOnly?: boolean;
  suggestedEventIds?: (string | number)[] | null;  // Filter to show only suggested events for user
  fetchMode?: EventFetchMode;  // "main_events" | "all_events" | "sub_events"
  filterByMainEventId?: string;  // Filter sub_events by their parent main_event ID
  filterBySubEventMainId?: string;  // Filter to show only the main_event for a sub_event
  providedEvents?: Event[];  // Optionally provide events directly instead of fetching
  searchQuery?: string;  // Optional search query provided by parent
  enablePagination?: boolean;  // Enable pagination with page controls
}

export default function EventList({ 
  sortOption, 
  showLikedOnly = false, 
  showGoingOnly = false,
  suggestedEventIds,
  fetchMode = "main_events",
  filterByMainEventId,
  filterBySubEventMainId,
  providedEvents,
  searchQuery = "",
  enablePagination = false,
}: EventListProps) {

  // -------------- Initialization --------------

  // Fetch events and error state using the custom useEvents hook
  const { events: fetchedEvents, error, isLoading } = useEvents(fetchMode);
  const navigate = useNavigate();

  // Use provided events if available, otherwise use fetched events
  const events = providedEvents ?? fetchedEvents;

  // Get liked event IDs from auth context (shared across browsers)
  const { likedEventIds, goingEventIds } = useAuth();

  const normalizedQuery = searchQuery.trim();

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const eventsPerPage = PAGINATION.EVENTS_PER_PAGE;

  // -------------- Helper Functions --------------

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

    // Flexible keyword search
    if (normalizedQuery) {
      filteredEvents = filteredEvents.filter((event) => 
        matchesEvent(event, normalizedQuery)
      );
    }


    // Filter by suggested event IDs if provided
    if (suggestedEventIds && suggestedEventIds.length > 0) {
      const suggestedIdsSet = new Set(suggestedEventIds.map(String));
      filteredEvents = filteredEvents.filter(event => suggestedIdsSet.has(String(event.id)));
    }

    // Filter sub_events by their parent main_event ID if provided
    if (filterByMainEventId !== undefined) {
      filteredEvents = filteredEvents.filter(
        event => event.event_type === "sub_event" && event.main_event_id === filterByMainEventId
      );
    }

    // Filter to show only the main_event for a sub_event if provided
    if (filterBySubEventMainId !== undefined) {
      filteredEvents = filteredEvents.filter(
        event => event.event_type === "main_event" && event.id === filterBySubEventMainId
      );
    }

    // Filter events if showLikedOnly is enabled (uses state instead of reading from localStorage)
    if (showLikedOnly) {
      const likedSet = new Set(likedEventIds.map(String));
      filteredEvents = filteredEvents.filter(event => likedSet.has(String(event.id)));
    }

    // Filter events if showGoingOnly is enabled (uses state instead of reading from localStorage)
    if (showGoingOnly) {
      const goingSet = new Set(goingEventIds.map(String));
      filteredEvents = filteredEvents.filter(event => goingSet.has(String(event.id)));
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
  }, [events,
    normalizedQuery, 
    sortOption, 
    showLikedOnly, 
    likedEventIds,
    showGoingOnly,
    goingEventIds,
    filterByMainEventId, 
    filterBySubEventMainId,
    suggestedEventIds]); // Recompute when any filter/sort criteria change

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [normalizedQuery, sortOption, showLikedOnly, showGoingOnly, filterByMainEventId, filterBySubEventMainId, suggestedEventIds]);

  // -------------- Pagination --------------

  // Calculate total pages and get events for current page
  const totalEvents = sortedEvents.length;
  const totalPages = Math.ceil(totalEvents / eventsPerPage);
  
  const paginatedEvents = useMemo(() => {
    if (!enablePagination) {
      return sortedEvents;
    }
    const startIndex = (currentPage - 1) * eventsPerPage;
    const endIndex = startIndex + eventsPerPage;

    return sortedEvents.slice(startIndex, endIndex);
    
  }, [sortedEvents, currentPage, eventsPerPage, enablePagination]);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top of event list when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // -------------- Check for Loading/Error --------------

  // Show loading state
  if (isLoading) {
    return (
      <div className="event-list-loading">
        <Spin indicator={<LoadingOutlined spin />} size="large" />
        <Paragraph type="secondary" style={{ marginTop: 16 }}>
          Events will appear momentarily...
        </Paragraph>
      </div>
    );
  }

  // Render error message if there was an error fetching events
  if (error) {
    return <div className="event-list-error">Error: {error}</div>;
  }

  // -------------- Render Component --------------

  const formatDateLabel = (value?: string | null) => {
    if (!value) return null;
    const dateObject = new Date(value);
    return Number.isNaN(dateObject.getTime()) ? value : dateObject.toLocaleDateString();
  };

  return (
    // Container for the event list
    <div className="event-list">
      {sortedEvents.length === 0 ? (
        <p className="event-list-empty">No events found.</p>
      ) : ( 
        
        /*
          Render the grid of event cards.
        */
        <>
        <div className="event-grid">
          {paginatedEvents.map((event) => {

            //const dateObj = new Date(event.start_date); 

            const startDateLabel = formatDateLabel(event.start_date) ?? event.start_date;
            const endDateLabel = formatDateLabel(event.end_date);
              
            let dateLabel = undefined;
            let timeLabel = undefined;

            // If both start and end dates exist and are different, show range
            if (event.start_date === event.end_date) {
              dateLabel = startDateLabel;
            } else {
              dateLabel = event.start_date ? event.end_date ? `${startDateLabel} – ${endDateLabel}` : startDateLabel : "";
            }

            if (event.start_time === event.end_time) {
              timeLabel = event.start_time;
            } else {
              timeLabel = event.start_time ? event.end_time ? `${event.start_time} – ${event.end_time}` : event.start_time : "";
            }

            const hasSubEvents = event.event_type === "main_event" && Array.isArray(event.sub_event_ids) && event.sub_event_ids.length > 0;

            const relationLabel = hasSubEvents ? "Multiple dates" : null;
            
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
                  {timeLabel && (
                    <>
                      <span className="event-detail-separator"> • </span>
                      <span>{timeLabel}</span>
                    </>
                  )}
                </div>

                {event.location && (
                  <div className="event-card-location">{event.location}</div>
                )}

                <div className="event-card-actions">
                  <LikeButton 
                    eventId={event.id} 
                    initialLikeCount={event.like_count}
                    eventType={event.event_type} 
                    size="small"
                  />

                  <GoingButton
                    eventId={event.id}
                    initialGoingCount={event.going_count}
                    eventType={event.event_type}
                    size="small"
                  />

                  <ShareButton
                    title={event.title}
                    url={`${window.location.origin}/events/${event.id}`}
                    size="small"
                  />

                  {relationLabel && (
                    <span className="event-card-relation">{relationLabel}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Pagination controls */}
        {enablePagination && totalPages > 1 && (

          <div className="event-list-pagination">

            {/* Use Ant Design's light/dark algorithms; colors still come from CSS variables */}
            <Pagination
                current={currentPage}
                total={totalEvents}
                pageSize={eventsPerPage}
                onChange={handlePageChange}
                showSizeChanger={false}
                showQuickJumper={totalPages > 10}
                showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} events`}
            />
          </div>
        )}
        </>
      )}
    </div>
  );
}
