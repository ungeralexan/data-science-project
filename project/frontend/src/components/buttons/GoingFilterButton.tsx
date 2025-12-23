// src/components/GoingFilterButton.tsx
import { Button } from "antd";
import { CheckCircleOutlined, CheckCircleFilled } from "@ant-design/icons";
import "../css/Events.css";

/*
  GoingFilterButton Component
  A toggle button that filters events to show only those the user marked as "going".
  Mirrors the behavior and styling of LikedFilterButton.
*/

interface GoingFilterButtonProps {
  showGoingOnly: boolean;
  onChange: (showGoingOnly: boolean) => void;

  iconOnly?: boolean;
}

export default function GoingFilterButton({ showGoingOnly, onChange, iconOnly = false }: GoingFilterButtonProps) {
  const label = showGoingOnly ? "Showing Going" : "Show Going Only";
  return (
    <Button
      type={showGoingOnly ? "primary" : "default"}
      icon={showGoingOnly ? <CheckCircleFilled /> : <CheckCircleOutlined />}
      onClick={() => onChange(!showGoingOnly)}
      className={iconOnly ? "events-control-icon-btn" : "events-control-btn"}

      aria-label={label}
      title={label}
    >
      {iconOnly ? null : label}
    </Button>
  );
}
