// src/components/buttons/RegistrationButton.tsx
import { Button } from "antd";

/*
  RegistrationButton Component
  
  Renders a button that links to the event's registration page.
  Only renders if a registration URL is provided.
*/

interface RegistrationButtonProps {
  registrationUrl?: string;
}

export default function RegistrationButton({ registrationUrl }: RegistrationButtonProps) {

  // Only show a button if there is a registration link
  if (!registrationUrl) return null;

  // Ensure URL has a protocol prefix, otherwise the browser treats it as a relative path
  const normalizedUrl = registrationUrl.match(/^https?:\/\//) ? registrationUrl : `https://${registrationUrl}`;

  return (
    <Button
      type="primary"
      size="large"
      className="event-detail-action-button"
      href={normalizedUrl}
      target="_blank"
      rel="noopener noreferrer"
    >
      Register for Event
    </Button>
  );
}
