// src/pages/EventDetail.tsx
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button } from "antd";

import { useEvents } from "../hooks/useEvents";
import EventImage from "../components/EventImage";
import CalendarDownloadButtons from "../components/CalendarDownloadButton";
import "../components/css/EventDetail.css";

/*
  EventDetail.tsx is the page component for displaying detailed information about a specific event.

  useParams:
    useParams is a React Router hook that allows access to URL parameters. In this case, it is used to
    retrieve the event ID from the URL.

  useNavigate:
    useNavigate is a React Router hook that provides a function to programmatically navigate between routes.
    Here, it is used to navigate back to the events list.

  useEvents:
    useEvents is a custom hook that fetches the list of events from the backend. It returns the events
    and any error encountered during fetching.

  EventImage:
    EventImage is a custom component that displays an image for the event based on the provided image key.

  Typography:
    Typography is a component from Ant Design that provides various typographic elements like titles, paragraphs,
    and text styles to enhance the visual presentation of text content.

  Button:
    Button is a component from Ant Design that provides styled button elements for user interactions.


*/

const { Title, Paragraph, Text } = Typography;

export default function EventDetail() {

  const { id } = useParams<{ id: string }>(); // Get the event ID from the URL parameters
  const navigate = useNavigate(); // Hook to programmatically navigate between routes
  const { events, error } = useEvents(); // Fetch the list of events using a custom hook

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

  const dateObj = new Date(event.start_date); // Create Date object from event's start_date
  const dateLabel = isNaN(dateObj.getTime()) ? event.start_date : dateObj.toLocaleDateString(); // Either formatted date or original string
  // Construct time label based on start_time and end_time. If no end_time, just show start_time
  const timeLabel = event.start_time ? event.end_time ? `${event.start_time} – ${event.end_time}` : event.start_time : "";

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

              {/* Display the formatted date*/}
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

            {event.location && (
              <div className="event-detail-meta-row">
                <Text strong>Location:</Text>
                <span>{event.location}</span>
              </div>
            )}
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

      {/* Calendar Download Buttons */}
      <CalendarDownloadButtons event={event} />
    </div>
  );
}
