// src/pages/EventDetail.tsx
import { useParams, useNavigate } from "react-router-dom";
import { Typography, Button } from "antd";

import { useEvents } from "../hooks/useEvents";
import EventImage from "../components/EventImage";

const { Title, Paragraph, Text } = Typography;

export default function EventDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { events, error } = useEvents();

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!events.length) {
    return <div>Loading events…</div>;
  }

  const event = events.find((e) => String(e.id) === id);

  if (!event) {
    return (
      <div>
        <Title level={2}>Event not found</Title>
        <Button type="link" onClick={() => navigate("/events")}>
          ← Back to events
        </Button>
      </div>
    );
  }

  const dateObj = new Date(event.start_date);
  const dateLabel = isNaN(dateObj.getTime())
    ? event.start_date
    : dateObj.toLocaleDateString();

  const timeLabel = event.start_time || "";

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <Button type="link" onClick={() => navigate("/events")} style={{ padding: 0, marginBottom: 8 }}>
        ← Back to events
      </Button>

      <Title level={2} style={{ marginBottom: 12 }}>
        {event.title}
      </Title>

      <div style={{ marginBottom: 16, display: "flex", gap: 16, alignItems: "flex-start" }}>
        <div style={{ flexShrink: 0, width: 260, maxWidth: "40%" }}>
          <EventImage
            imageKey={event.image_key}
            title={event.title}
            className="event-detail-image"
          />
        </div>

        <div style={{ flex: 1 }}>
          <Paragraph style={{ marginBottom: 4 }}>
            <Text strong>Date:</Text> {dateLabel}
            {timeLabel && ` ${timeLabel}`}
          </Paragraph>

          {event.location && (
            <Paragraph style={{ marginBottom: 4 }}>
              <Text strong>Location:</Text> {event.location}
            </Paragraph>
          )}
        </div>
      </div>

      <Title level={4} style={{ marginTop: 8 }}>
        Description
      </Title>

      {event.description ? (
        <Paragraph style={{ whiteSpace: "pre-line", fontSize: "1.05rem", lineHeight: 1.6 }}>
          {event.description}
        </Paragraph>
      ) : (
        <Paragraph type="secondary">No description available for this event.</Paragraph>
      )}
    </div>
  );
}
