// src/components/LikedFilterButton.tsx
import { Button } from "antd";
import { HeartOutlined, HeartFilled } from "@ant-design/icons";
import "./css/Events.css";

/*
  LikedFilterButton Component
  
  A toggle button that filters events to show only liked ones.
  - Uses the same heart icon styling as the LikeButton
  - When active, only events the user has liked will be displayed
*/

interface LikedFilterButtonProps {
  showLikedOnly: boolean;
  onChange: (showLikedOnly: boolean) => void;
}

export default function LikedFilterButton({ showLikedOnly, onChange }: LikedFilterButtonProps) {
  return (
    <Button
      type={showLikedOnly ? "primary" : "default"}
      icon={showLikedOnly ? <HeartFilled /> : <HeartOutlined />}
      onClick={() => onChange(!showLikedOnly)}
      className="events-page-controls"
    >
      {showLikedOnly ? "Showing Liked" : "Show Liked Only"}
    </Button>
  );
}
