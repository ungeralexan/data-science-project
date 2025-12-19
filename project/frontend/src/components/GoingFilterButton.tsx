// src/components/GoingFilterButton.tsx
import { Button } from "antd";
import "./css/Events.css";

/*
  GoingFilterButton Component
  A toggle button that filters events to show only those the user marked as "going".
  Mirrors the behavior and styling of LikedFilterButton.
*/

interface GoingFilterButtonProps {
  showGoingOnly: boolean;
  onChange: (showGoingOnly: boolean) => void;
}

export default function GoingFilterButton({ showGoingOnly, onChange }: GoingFilterButtonProps) {
  return (
    <Button
      type={showGoingOnly ? "primary" : "default"}
      onClick={() => onChange(!showGoingOnly)}
      className="events-page-controls"
    >
      {showGoingOnly ? "Showing Going" : "Show Going Only"}
    </Button>
  );
}
