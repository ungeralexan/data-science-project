// This is the Event type definition used throughout the frontend application.
export type Event = {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  description?: string;
  speaker?: string;
  organizer?: string;
  registration_needed?: string;
  url?: string;
  image_key?: string;
};
