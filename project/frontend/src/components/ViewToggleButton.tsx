import { Button } from "antd";

type ViewMode = "list" | "calendar";

interface ViewToggleButtonProps {
  viewMode: ViewMode;
  onToggle: (next: ViewMode) => void;
}

export default function ViewToggleButton({ viewMode, onToggle }: ViewToggleButtonProps) {

  const isCalendar = viewMode === "calendar";

  return (
    <Button
      type={isCalendar ? "primary" : "default"} // Highlight button when in calendar view
      onClick={() => onToggle(isCalendar ? "list" : "calendar")} // Toggle between list and calendar views
      className="events-page-controls"
    >
      {isCalendar ? "Showing Calendar View" : "Show Calendar View"}
    </Button>
  );
}
