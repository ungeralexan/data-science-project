// src/components/LikeButton.tsx
import { useState } from "react";
import { HeartOutlined, HeartFilled } from "@ant-design/icons";
import { useAuth } from "../../hooks/useAuth";
import "../css/LikeButton.css";

/*
  LikeButton Component
  
  A toggle button that allows users to like/unlike an event.
  - Displays a heart icon (outlined when not liked, filled when liked)
  - Shows the current like count
  - Uses AuthContext to persist likes to the database (shared across browsers/sessions)
  - Requires user authentication to like events
*/

interface LikeButtonProps {
  eventId: string;
  initialLikeCount: number;
  size?: "small" | "default";  // Different size for /events vs /events:id page
  onLikeChange?: (eventId: string, isLiked: boolean) => void;  // Callback when like status changes
  eventType?: "main_event" | "sub_event";  // Type of event for correct API endpoint
}

export default function LikeButton({ eventId, initialLikeCount, size = "default", onLikeChange, eventType = "main_event" }: LikeButtonProps) {
  
  const { isAuthenticated, isEventLiked, toggleLike } = useAuth();
  
  // Get initial liked state from auth context
  const isLiked = isEventLiked(eventId);
  
  const [likeCount, setLikeCount] = useState<number>(initialLikeCount);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Toggle like status
  const handleClick = async (e: React.MouseEvent) => {

    // Prevent event bubbling (so clicking like doesn't navigate to event detail)
    e.stopPropagation();
    
    // Don't allow liking if not authenticated
    if (!isAuthenticated) {
      console.log("User must be logged in to like events");
      return;
    }
    
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {
      // Use the toggleLike function from auth context, passing eventType
      const result = await toggleLike(eventId, eventType);
      
      // Update local like count state
      setLikeCount(result.like_count);
      
      // Notify parent component of like status change
      onLikeChange?.(eventId, result.isLiked);
      
    } catch (error) {
      console.error("Error toggling like:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClass = size === "small" ? "like-button--small" : "";

  return (
    <button 
      // CSS classes for styling. If liked, add liked class to make heart filled red
      className={`like-button ${sizeClass} ${isLiked ? "like-button--liked" : ""}`}
      onClick={handleClick}
      disabled={isLoading || !isAuthenticated}
      aria-label={isLiked ? "Unlike event" : "Like event"}
      title={!isAuthenticated ? "Login to like events" : undefined}
    >
      {isLiked ? <HeartFilled /> : <HeartOutlined />}

      {/*Add like count next to heart icon*/}
      <span className="like-button__count">{likeCount}</span>
    </button>
  );
}
