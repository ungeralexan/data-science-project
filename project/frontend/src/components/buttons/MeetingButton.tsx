// src/components/buttons/MeetingButton.tsx
import { Button } from "antd";

/*
  MeetingButton Component
  
  Renders a button that links to the event's online meeting.
  Only renders if a meeting URL is provided (e.g., Zoom, Microsoft Teams).
*/

interface MeetingButtonProps {
  meetingUrl?: string;
}

export default function MeetingButton({ meetingUrl }: MeetingButtonProps) {

  // Only show a button if there is a meeting link
  if (!meetingUrl) return null;

  // Ensure URL has a protocol prefix, otherwise the browser treats it as a relative path
  const normalizedUrl = meetingUrl.match(/^https?:\/\//) ? meetingUrl : `https://${meetingUrl}`;

  return (
    <Button
      type="primary"
      size="large"
      className="event-detail-action-button"
      href={normalizedUrl}
      target="_blank"
      rel="noopener noreferrer"
    >
      Join Online Meeting
    </Button>
  );
}
