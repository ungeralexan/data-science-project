// src/components/EventWebsiteButton.tsx
import { Button } from "antd";

/*
  EventWebsiteButton Component
  
  Renders a button that links to the event's external website.
  Only renders if a URL is provided.
*/

interface EventWebsiteButtonProps {
  url?: string;
}

export default function EventWebsiteButton({ url }: EventWebsiteButtonProps) {

  // Only show a button if there is a link
  if (!url) return null;

  // Ensure URL has a protocol prefix, otherwise the browser treats it as a relative path
  const normalizedUrl = url.match(/^https?:\/\//) ? url : `https://${url}`;

  return (
    <Button
      type="primary"
      size="large"
      className="event-detail-action-button"
      href={normalizedUrl}
      target="_blank"
      rel="noopener noreferrer"
    >
      Visit Event Website
    </Button>
  );
}
