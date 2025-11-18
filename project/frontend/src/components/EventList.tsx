import { useEvents } from "../hooks/useEvents";
import "./css/EventList.css"; // ⬅️ make sure the path is correct

export default function EventList() {
  const { events, error } = useEvents();

  if (error) {
    return <div className="event-list__error">Error: {error}</div>;
  }

  return (
    <div className="event-list">
      {events.length === 0 ? (
        <p className="event-list__empty">No events received yet.</p>
      ) : (
        <div className="event-grid">
          {events.map((event) => (
            <div key={event.id} className="event-card">
              {/* Image placeholder */}
              <div className="event-card__image-placeholder">
                {/* Later: <img src={event.imageUrl} alt={event.event_title} className="event-card__image" /> */}
              </div>

              <div className="event-card__title">{event.event_title}</div>

              <div className="event-card__datetime">
                {new Date(event.start_date).toLocaleString()} –{" "}
                {new Date(event.end_date).toLocaleString()}
              </div>

              {event.location && (
                <div className="event-card__location">{event.location}</div>
              )}

              {event.description && (
                <div className="event-card__description">
                  {event.description}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
