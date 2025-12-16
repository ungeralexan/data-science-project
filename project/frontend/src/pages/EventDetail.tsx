// src/pages/EventDetail.tsx
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button, Tag } from "antd";
import { UserOutlined, TeamOutlined, CheckCircleOutlined, EnvironmentOutlined } from "@ant-design/icons";

import { useEvents } from "../hooks/useEvents";
import EventImage from "../components/EventImage";
import LikeButton from "../components/LikeButton";
import CalendarDownloadButtons from "../components/CalendarDownloadButton";
import EventWebsiteButton from "../components/EventWebsiteButton";
import EventList from "../components/EventList";
import "../components/css/EventDetail.css";

/*
  EventDetail.tsx is the page component for displaying detailed information about a specific event.
*/

const { Title, Paragraph, Text } = Typography;

export default function EventDetail() {

  const { id } = useParams<{ id: string }>(); // Get the event ID from the URL parameters
  const navigate = useNavigate(); // Hook to programmatically navigate between routes
  
  // Fetch all events (main + sub) to find the current event regardless of type
  const { events, error } = useEvents("all_events");

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!events.length) {
    return <div>Loading events…</div>;
  }

  // Find the event that matches the ID from the URL
  const event = events.find((e) => String(e.id) === id);

  // If no event is found, display a not found message with a back button
  if (!event) {
    return (
      <div className="event-detail">
        <Title level={2}>Event not found</Title>
        <Button
          type="link"
          onClick={() => navigate("/events")}
          className="event-detail-back"
        >
          ← Back to events
        </Button>
      </div>
    );
  }

  // Determine if this is a main_event with sub_events
  const isMainEvent = event.event_type === "main_event";
  const hasSubEvents = isMainEvent && event.sub_event_ids && event.sub_event_ids.length > 0;
  
  // Get sub_events for this main_event
  const subEvents = hasSubEvents 
    ? events.filter(e => e.event_type === "sub_event" && e.main_event_id === event.id)
    : [];

  // For sub_events, get the parent main_event
  const isSubEvent = event.event_type === "sub_event";
  const parentMainEvent = isSubEvent && event.main_event_id
    ? events.find(e => e.event_type === "main_event" && e.id === event.main_event_id)
    : null;

  const formatDateLabel = (value?: string | null) => {
    if (!value) return null;
    const dateObject = new Date(value);
    return Number.isNaN(dateObject.getTime()) ? value : dateObject.toLocaleDateString();
  };

  // Format date and time labels
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

  // Build formatted address from individual address fields
  const buildFormattedAddress = () => {
    const parts: string[] = [];
    
    // Street with house number
    if (event.street) {

      // If house_number exists, include it after street name
      parts.push(event.house_number ? `${event.street} ${event.house_number}` : event.street);
    }
    
    // Room and floor info
    if (event.room || event.floor) {

      //If both room and floor exist, join them with a comma
      const roomFloor = [event.room, event.floor ? `Floor ${event.floor}` : null].filter(Boolean).join(", ");
      if (roomFloor) parts.push(roomFloor);
    }
    
    // City with zip code
    if (event.city || event.zip_code) {

      // Combine zip code and city, filtering out any missing values
      const cityZip = [event.zip_code, event.city].filter(Boolean).join(" ");
      if (cityZip) parts.push(cityZip);
    }
    
    // Country
    if (event.country) {
      parts.push(event.country);
    }
    
    return parts.length > 0 ? parts.join(", ") : null;
  };

  // Build Google Maps URL from address fields
  const buildGoogleMapsUrl = () => {
    const addressParts: string[] = [];
    
    if (event.street) {
      addressParts.push(event.house_number ? `${event.street} ${event.house_number}` : event.street);
    }

    if (event.zip_code) addressParts.push(event.zip_code);
    if (event.city) addressParts.push(event.city);
    if (event.country) addressParts.push(event.country);
    
    if (addressParts.length > 0) {
      return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addressParts.join(", "))}`;
    }
    
    return null;
  };

  const formattedAddress = buildFormattedAddress();
  const googleMapsUrl = buildGoogleMapsUrl();

  // Normalize registration_needed which may arrive as string or boolean
  const registrationRaw = event.registration_needed;
  const registrationNormalized = typeof registrationRaw === "string"
    ? registrationRaw.toLowerCase()
    : typeof registrationRaw === "boolean"
      ? (registrationRaw ? "true" : "false")
      : "";

  // Use formatted address if available, otherwise fall back to location field
  const displayAddress = formattedAddress || event.location;

  // Render the detailed view of the event
  return (
    <div className="event-detail">

      <Button type="link" onClick={() => navigate("/events")} className="event-detail-back"> 
        ← Back to events
      </Button>

      <div className="event-detail-layout">
        <div className="event-detail-image-wrapper">
          <EventImage imageKey={event.image_key}  title={event.title} className="event-detail-image" />
        </div>

        <div className="event-detail-content">
          <Title level={2} className="event-detail-title">
            {event.title}
          </Title>
        
          <div className="event-detail-meta">
            <div className="event-detail-meta-row">
              <Text strong>Date:</Text> 

              <span>{dateLabel}</span>

              {/* 
                {timeLabel && (...)} means if timeLabel is not an empty string, then render the JSX inside the parentheses. 
                Otherwise do not render anything.

                The part inside (...) is a React fragment (<>...</>) that contains two span elements:
                
                1. The first span with className="event-detail-separator" displays a separator dot (•) between the date and time.
                2. The second span displays the actual timeLabel value.
              */}
              {timeLabel && (
                <>
                  <span className="event-detail-separator">•</span>
                  <span>{timeLabel}</span>
                </>
              )}
            </div>

            <div className="event-detail-meta-row">
              <EnvironmentOutlined className="event-detail-icon event-detail-icon--location" />
              <Text strong>Location:</Text>
              {displayAddress ? (
                googleMapsUrl ? (
                  <a 
                    href={googleMapsUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="event-detail-location-link"
                  >
                    {displayAddress}
                  </a>
                ) : (
                  <span>{displayAddress}</span>
                )
              ) : (
                <Text type="secondary">No information available</Text>
              )}
            </div>

            <div className="event-detail-meta-row">
              <TeamOutlined className="event-detail-icon event-detail-icon--organizer" />
              <Text strong>Organizer:</Text>
              {event.organizer ? (
                <span>{event.organizer}</span>
              ) : (
                <Text type="secondary">No information available</Text>
              )}
            </div>

            <div className="event-detail-meta-row">
              <UserOutlined className="event-detail-icon event-detail-icon--speaker" />
              <Text strong>Speaker:</Text>
              {event.speaker ? (
                <span>{event.speaker}</span>
              ) : (
                <Text type="secondary">No information available</Text>
              )}
            </div>

            <div className="event-detail-meta-row">
              <CheckCircleOutlined className="event-detail-icon event-detail-icon--registration" />
              <Text strong>Registration:</Text>
              {registrationNormalized ? (
                <Tag
                  // If registration_needed indicates true/yes, use orange tag, else green
                  color={registrationNormalized === 'true' || registrationNormalized === 'yes' ? 'orange' : 'green'}>
                  {registrationNormalized === 'true' || registrationNormalized === 'yes' ? 'Required' : 'Not Required'}
                </Tag>
              ) : (
                <Text type="secondary">No information available</Text>
              )}
            </div>

            <div className="event-detail-actions">
              <LikeButton eventId={event.id} initialLikeCount={event.like_count} eventType={event.event_type} />
            </div>
          </div>
        </div>
      </div>

      {/* Event Description Section. Only shows if event.description exists */}
      <div className="event-detail-description">
        <Title level={4} className="event-detail-description-title">
          Description
        </Title>

        {event.description ? (
          <Paragraph className="event-detail-description-text">
            {event.description}
          </Paragraph>
        ) : (
          <Paragraph type="secondary">
            No description available for this event.
          </Paragraph>
        )}
      </div>

      {/* Calendar Download and Event URL Buttons */}
      <div className="event-detail-buttons">
        <CalendarDownloadButtons event={event} />
        <EventWebsiteButton url={event.url} />
      </div>

      {/* If this is a main_event, show its sub_events list */}
      {isMainEvent && subEvents.length > 0 && (
        <div className="event-detail-subevents">
          <Title level={4} className="event-detail-subevent-section">Sub Events</Title>
          <EventList
            sortOption="date-asc"
            fetchMode="all_events"
            providedEvents={subEvents}
            filterByMainEventId={event.id}
          />
        </div>
      )}

      {/* If this is a sub_event, show a small card/list for its parent main_event */}
      {isSubEvent && parentMainEvent && (
        <div className="event-detail-parent">

          <Title level={4} className="event-detail-subevent-section">Parent Event</Title>

          <EventList
            sortOption="date-asc"
            fetchMode="all_events"
            providedEvents={[parentMainEvent]}
            filterBySubEventMainId={parentMainEvent.id}
          />
        </div>
      )}
    </div>
  );
}
