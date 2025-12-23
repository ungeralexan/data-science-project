import { Button } from "antd";
import { CalendarOutlined, UnorderedListOutlined } from "@ant-design/icons";
import "./css/Events.css";

type ViewMode = "list" | "calendar";

interface ViewToggleButtonProps {
  viewMode: ViewMode;
  onToggle: (next: ViewMode) => void;

  iconOnly?: boolean;
}

export default function ViewToggleButton({ viewMode, onToggle, iconOnly = false}: ViewToggleButtonProps) {

  const isCalendar = viewMode === "calendar";

  const label = isCalendar ? "Showing Calendar View" : "Show Calendar View";

  return (
    <Button
      type={isCalendar ? "primary" : "default"} // Highlight button when in calendar view
      onClick={() => onToggle(isCalendar ? "list" : "calendar")} // Toggle between list and calendar views

      icon={isCalendar ? <UnorderedListOutlined /> : <CalendarOutlined />}
      className={iconOnly ? "events-control-icon-btn" : "events-control-btn"}
      aria-label={label}
      title={label}
    >
      {iconOnly ? null : label}
    </Button>
  );
}
