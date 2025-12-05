// src/pages/EventDetail.tsx
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button, Tag } from "antd";
import { UserOutlined, TeamOutlined, CheckCircleOutlined, EnvironmentOutlined } from "@ant-design/icons";

import { useEvents } from "../hooks/useEvents";
import EventImage from "../components/EventImage";
import LikeButton from "../components/LikeButton";
import CalendarDownloadButtons from "../components/CalendarDownloadButton";
import EventWebsiteButton from "../components/EventWebsiteButton";
import "../components/css/EventDetail.css";

/*
  EventDetail.tsx is the page component for displaying detailed information about a specific event.
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
                <EnvironmentOutlined style={{ color: '#1890ff' }} />
                <Text strong>Location:</Text>
                {googleMapsUrl ? (
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
                )}
              </div>
            )}

            {event.organizer && (
              <div className="event-detail-meta-row">
                <TeamOutlined style={{ color: '#1890ff' }} />
                <Text strong>Organizer:</Text>
                <span>{event.organizer}</span>
              </div>
            )}

            {event.speaker && (
              <div className="event-detail-meta-row">
                <UserOutlined style={{ color: '#1890ff' }} />
                <Text strong>Speaker:</Text>
                <span>{event.speaker}</span>
              </div>
            )}

            {event.registration_needed && (
              <div className="event-detail-meta-row">
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <Text strong>Registration:</Text>
                <Tag 
                // If registration_needed indicates true/yes, use orange tag, else green
                color={event.registration_needed.toLowerCase() === 'true' || event.registration_needed.toLowerCase() === 'yes' ? 'orange' : 'green'}>
                  {event.registration_needed.toLowerCase() === 'true' || event.registration_needed.toLowerCase() === 'yes' ? 'Required' : 'Not Required'}
                </Tag>
              </div>
            )}

            <div className="event-detail-actions">
              <LikeButton eventId={event.id} initialLikeCount={event.like_count} />
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
    </div>
  );
}
