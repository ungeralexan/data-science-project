import { Button } from "antd";

interface SubeventToggleButtonProps {
  showSubevents: boolean;
  onToggle: (next: boolean) => void;
}

export default function SubeventToggleButton({ showSubevents, onToggle }: SubeventToggleButtonProps) {
  return (
    <Button
      type={showSubevents ? "primary" : "default"} // Highlight button when showing subevents
      onClick={() => onToggle(!showSubevents)} // Toggle between showing and hiding subevents
      className="events-page-controls"
    >
      {showSubevents ? "Showing Subevents" : "Show Subevents"}
    </Button>
  );
}
