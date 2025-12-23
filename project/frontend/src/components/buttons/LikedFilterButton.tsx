// src/components/LikedFilterButton.tsx
import { Button } from "antd";
import { HeartOutlined, HeartFilled } from "@ant-design/icons";
import "../css/Events.css";

/*
  LikedFilterButton Component
  
  A toggle button that filters events to show only liked ones.
  - Uses the same heart icon styling as the LikeButton
  - When active, only events the user has liked will be displayed
*/

interface LikedFilterButtonProps {
  showLikedOnly: boolean;
  onChange: (showLikedOnly: boolean) => void;

  iconOnly?: boolean;
}

export default function LikedFilterButton({ showLikedOnly, onChange, iconOnly = false }: LikedFilterButtonProps) {
  const label = showLikedOnly ? "Showing Liked" : "Show Liked Only";
  return (
    <Button
      type={showLikedOnly ? "primary" : "default"}
      icon={showLikedOnly ? <HeartFilled /> : <HeartOutlined />}
      onClick={() => onChange(!showLikedOnly)}
      className={iconOnly ? "events-control-icon-btn" : "events-control-btn"}

      aria-label={label}
      title={label}
    >
      {iconOnly ? null : label}
    </Button>
  );
}
