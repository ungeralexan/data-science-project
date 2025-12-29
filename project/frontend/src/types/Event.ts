// This is the Event type definition used throughout the frontend application.
// Used for both main_events and sub_events.
export type Event = {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
  location?: string;  // Full address string (for backward compatibility)
  street?: string;
  house_number?: string;
  zip_code?: string;
  city?: string;
  country?: string;
  room?: string;
  floor?: string;
  description?: string;
  language?: string;
  speaker?: string;
  organizer?: string;
  registration_needed?: boolean;
  url?: string;
  registration_url?: string;  // URL where users can register for the event
  meeting_url?: string;  // URL for online meetings (Zoom, Teams, etc.)
  image_key?: string;
  like_count: number;
  going_count: number;
  event_type: "main_event" | "sub_event";  // Type of event
  main_event_id?: string | null;  // For sub_events: reference to parent main_event
  sub_event_ids?: string[] | null;  // For main_events: list of child sub_event IDs
};
