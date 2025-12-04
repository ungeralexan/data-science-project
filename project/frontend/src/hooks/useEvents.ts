import { useEffect, useRef, useState } from "react";
import type { Event } from "../types/Event";
import { WS_PORT } from "../config";

/*
  This custom React hook establishes a WebSocket connection to fetch event data from the backend server.

  A hook is a special function in React that lets you "hook into" React features.
  Custom hooks are user-defined functions that can use other hooks to encapsulate and reuse stateful logic across components.
  Here, useEvents uses the useState, useEffect, and useRef hooks to manage state and side effects related to WebSocket communication.

  useEvents:
    useEvents is a custom React hook that manages a WebSocket connection to fetch events from the backend.
    It maintains the state of events, connection status, and any errors that occur during the WebSocket communication.
    The hook returns the current list of events, connection status, and error state to the consuming component.

  WebSocket:
    WebSocket is a protocol that enables two-way communication between a client (frontend) and a server (backend) over a single, 
    long-lived connection. This allows for real-time data updates without the need for repeated HTTP requests.

  State Variables:
    events: An array of Event objects representing the events fetched from the backend.
    isConnected: A boolean indicating whether the WebSocket connection is currently open.
    error: A string or null representing any error message that occurred during WebSocket communication.
    socketRef: socketRef is a mutable reference to the WebSocket instance, allowing access to the WebSocket 
                object across re-renders without causing re-renders itself.
*/

export function useEvents() {

  // State variables to hold events, connection status, and error messages
  const [events, setEvents] = useState<Event[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // Establish WebSocket connection on component mount
  useEffect(() => {
    const host = window.location.hostname || "localhost";
    const wsUrl = `ws://${host}:${WS_PORT}/ws/events`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws; // Store WebSocket instance in ref

    // WebSocket open event handler
    ws.onopen = () => {

      // Update connection status and clear any previous errors
      setIsConnected(true);
      setError(null);
      
      // Request events from the server
      ws.send("get_events");
    };

    // WebSocket message event handler. (event) is the incoming message event
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Event[]; // Assume data is an array of Event objects
        setEvents(data); // Update events state
      } catch (err) {
        console.error("Failed to parse event data:", err);
        setError("Failed to parse events from server.");
      }
    };

    // WebSocket error event handler
    ws.onerror = () => {
      setError("WebSocket error occurred.");
    };

    // WebSocket close event handler
    ws.onclose = () => {
      setIsConnected(false);
    };

    // Cleanup function to close WebSocket connection on component unmount
    return () => {
      ws.close();
    };
  }, []); // Empty dependency array ensures this effect runs only once on mount

  // Return the current events, connection status, and error state
  return { events, isConnected, error };
}
