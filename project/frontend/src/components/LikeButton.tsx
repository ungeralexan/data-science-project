// src/components/LikeButton.tsx
import { useState } from "react";
import { HeartOutlined, HeartFilled } from "@ant-design/icons";
import { API_BASE_URL } from "../config";
import "./css/LikeButton.css";

/*
  LikeButton Component
  
  A toggle button that allows users to like/unlike an event.
  - Displays a heart icon (outlined when not liked, filled when liked)
  - Shows the current like count
  - Persists likes to localStorage to remember user's liked events
  - Calls backend API to update the like count in the database
*/

interface LikeButtonProps {
  eventId: number;
  initialLikeCount: number;
  size?: "small" | "default";  // Different size for /events vs /events:id page
  onLikeChange?: (eventId: number, isLiked: boolean) => void;  // Callback when like status changes
}

export default function LikeButton({ eventId, initialLikeCount, size = "default", onLikeChange }: LikeButtonProps) {
  
  // Check localStorage to see if user has already liked this event
  const getIsLiked = (): boolean => {
    const likedEvents = JSON.parse(localStorage.getItem("likedEvents") || "[]");
    return likedEvents.includes(eventId);
  };

  const [isLiked, setIsLiked] = useState<boolean>(getIsLiked());
  const [likeCount, setLikeCount] = useState<number>(initialLikeCount);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Toggle like status
  const handleClick = async (e: React.MouseEvent) => {

    // Prevent event bubbling (so clicking like doesn't navigate to event detail)
    e.stopPropagation();
    
    if (isLoading) return;
    
    setIsLoading(true);
    
    try {

      // If already liked, send unlike request; otherwise, send like request
      const endpoint = isLiked 
        ? `${API_BASE_URL}/api/events/${eventId}/unlike`
        : `${API_BASE_URL}/api/events/${eventId}/like`;
      
      const response = await fetch(endpoint, { method: "POST" });
      
      if (response.ok) {

        //Current count is part of response
        const data = await response.json();
        setLikeCount(data.like_count);
        
        // Update localStorage
        const likedEvents = JSON.parse(localStorage.getItem("likedEvents") || "[]");
        
        //If event is already liked, remove it; otherwise, add it
        if (isLiked) {
          // Remove from liked events
          const updated = likedEvents.filter((id: number) => id !== eventId);
          localStorage.setItem("likedEvents", JSON.stringify(updated));
        } else {
          // Add to liked events
          likedEvents.push(eventId);
          localStorage.setItem("likedEvents", JSON.stringify(likedEvents));
        }
        
        // Notify parent component of like status change
        const newIsLiked = !isLiked;

        setIsLiked(newIsLiked);
        onLikeChange?.(eventId, newIsLiked);
      }
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
      disabled={isLoading}
      aria-label={isLiked ? "Unlike event" : "Like event"}
    >
      {isLiked ? <HeartFilled /> : <HeartOutlined />}

      {/*Add like count next to heart icon*/}
      <span className="like-button__count">{likeCount}</span>
    </button>
  );
}
