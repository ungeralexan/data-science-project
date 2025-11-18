import { useEffect, useRef, useState } from "react";
import type { Event } from "../types/Event";

export function useEvents() {
  const [events, setEvents] = useState<Event[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/events");
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      // Ask backend for events
      ws.send("get_events");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Event[];
        setEvents(data);
      } catch (err) {
        console.error("Failed to parse event data:", err);
        setError("Failed to parse events from server.");
      }
    };

    ws.onerror = () => {
      setError("WebSocket error occurred.");
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    // Cleanup when component unmounts
    return () => {
      ws.close();
    };
  }, []);

  return { events, isConnected, error };
}
