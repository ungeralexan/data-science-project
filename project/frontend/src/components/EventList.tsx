import { useEvents } from "../hooks/useEvents";

export default function EventList() {
  const { events, isConnected, error } = useEvents();

  if (error) {
    return <div style={{ color: "red" }}>Error: {error}</div>;
  }

  return (
    <div>
      <h2>Upcoming Events</h2>
      <p>WebSocket status: {isConnected ? "Connected" : "Disconnected"}</p>

      {events.length === 0 ? (
        <p>No events received yet.</p>
      ) : (
        <ul>
          {events.map((event) => (
            <li key={event.id} style={{ marginBottom: "8px" }}>
              <strong>{event.event_title}</strong>
              <div>
                {new Date(event.start_date).toLocaleString()} –{" "}
                {new Date(event.end_date).toLocaleString()}
              </div>
              {event.location && <div>Location: {event.location}</div>}
              {event.description && <div>{event.description}</div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
