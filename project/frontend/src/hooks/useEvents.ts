import { useEffect, useRef, useState, useCallback } from "react";
import type { Event } from "../types/Event";
import { WS_PORT, LOCAL } from "../config";

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

export type EventFetchMode = "main_events" | "all_events" | "sub_events";

export function useEvents(fetchMode: EventFetchMode = "main_events") {

  // State variables to hold events, connection status, and error messages
  const [events, setEvents] = useState<Event[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);  // Start with loading true
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const hasReceivedDataRef = useRef(false); // Track if we've successfully received data (ref to avoid closure issues)
  const currentFetchModeRef = useRef<EventFetchMode>(fetchMode);

  // Function to request events based on fetch mode
  const requestEvents = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      let message: string;
      switch (currentFetchModeRef.current) {
        case "all_events":
          message = "get_all_events";
          break;
        case "sub_events":
          message = "get_sub_events";
          break;
        case "main_events":
        default:
          message = "get_events";
          break;
      }
      socketRef.current.send(message);
    }
  }, []);

  // Update current fetch mode ref when it changes
  useEffect(() => {
    currentFetchModeRef.current = fetchMode;
    // If socket is open, request events for the new mode immediately
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      requestEvents();
    }
  }, [fetchMode, requestEvents]);

  // Establish WebSocket connection on component mount
  useEffect(() => {

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    let wsUrl = "";

    if (LOCAL) {
      console.log("Using local WebSocket configuration");

      // Decide URL based on environment

      if (import.meta.env.DEV) {
        // Local dev: backend on port 8000
        wsUrl = `ws://localhost:${WS_PORT}/ws/events`;
        // or hardcode: `ws://localhost:8000/ws/events`
      } else {
        wsUrl = `${protocol}://${window.location.host}/ws/events`;
      }
    } else {
      // Production WebSocket URL
      wsUrl = `${protocol}://${window.location.host}/ws/events`;
    }
    
    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      // Ask backend to send events based on current fetch mode
      requestEvents();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Event[];
        setEvents(data);
        hasReceivedDataRef.current = true;
        setError(null);
        setIsLoading(false);
      } catch (err) {
        console.error("Failed to parse event data:", err);
        setError("Failed to parse events from server.");
        setIsLoading(false);
      }
    };

    // WebSocket error event handler
    ws.onerror = () => {
      // Only set error if we haven't already received data successfully
      // This prevents showing transient errors during reconnection attempts
      if (!hasReceivedDataRef.current) {
        setError("WebSocket error occurred.");
      }
      
      //setIsLoading(false);
    };

    // WebSocket close event handler
    ws.onclose = () => {
      setIsConnected(false);
    };

    // Cleanup function to close WebSocket connection on component unmount
    return () => {
      ws.close();
    };
  }, []); // Empty dependency array to run only once on mount

  // Return the current events, connection status, loading state, and error state
  // Only show error if we're not loading AND we haven't received data successfully
  return { events, isConnected, isLoading, error: (isLoading || hasReceivedDataRef.current) ? null : error };
}
