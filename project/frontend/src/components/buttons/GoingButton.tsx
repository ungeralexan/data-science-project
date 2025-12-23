import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import "../css/GoingButton.css";

interface Props {
  eventId: string;
  initialGoingCount: number;
  size?: "small" | "default";
  eventType?: "main_event" | "sub_event";
}

export default function GoingButton({
  eventId,
  initialGoingCount,
  size = "default",
  eventType = "main_event",
}: Props) {
  const { isAuthenticated, isEventGoing, toggleGoing } = useAuth();

  const isGoing = isEventGoing(eventId);
  const [goingCount, setGoingCount] = useState<number>(initialGoingCount);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAuthenticated) return;
    if (isLoading) return;

    setIsLoading(true);
    try {
      const result = await toggleGoing(eventId, eventType);
      setGoingCount(result.going_count);
    } catch (err) {
      console.error("Error toggling going:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClass = size === "small" ? "going-button--small" : "";

  return (
    <button
      className={`going-button ${sizeClass} ${isGoing ? "going-button--active" : ""}`}
      onClick={handleClick}
      disabled={isLoading || !isAuthenticated}
      aria-label={isGoing ? "Unmark going" : "Mark going"}
      title={!isAuthenticated ? "Login to mark going" : undefined}
    >
      Going <span className="going-button__count">{goingCount}</span>
    </button>
  );
}
