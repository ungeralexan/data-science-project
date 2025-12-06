// src/pages/Events.tsx
import { useState } from "react";
import { Typography } from 'antd';
import EventList from '../components/EventList';
import EventCalendar from '../components/EventCalendar';
import EventSortControls from "../components/EventSortButton";
import type { SortOption } from "../components/EventSortButton";
import LikedFilterButton from "../components/LikedFilterButton";
import ViewToggleButton from "../components/ViewToggleButton";
import "../components/css/Events.css";

/*
  Events.tsx is the main page component for displaying events. It includes sorting functionality
  to allow users to sort events based on different criteria or change the view mode between list and calendar.
*/

const { Title } = Typography;

export default function Events() {

  // State to hold the current sorting option for events
  const [sortOption, setSortOption] = useState<SortOption>("date-asc");
  
  // State to hold whether to show only liked events
  const [showLikedOnly, setShowLikedOnly] = useState<boolean>(false);

  // State to toggle between list and calendar views
  const [viewMode, setViewMode] = useState<"list" | "calendar">("list");

  // Render the Events page with title, sorting controls, and event list
  return (
    <div className="events-page">
      <div className="events-page-topbar">
        <div className="events-page-header">
          <Title level={2} className="events-page-title">Events</Title>
        </div>

        <div className="events-page-controls">
          <EventSortControls
            sortOption={sortOption}
            onChange={setSortOption}
          />
          <LikedFilterButton
            showLikedOnly={showLikedOnly}
            onChange={setShowLikedOnly}
          />
          <ViewToggleButton
            viewMode={viewMode}
            onToggle={setViewMode}
          />
        </div>
      </div>
      
      {/* Toggle between list and calendar views */}
      {viewMode === "list" ? (
        <EventList sortOption={sortOption} showLikedOnly={showLikedOnly} />
      ) : (
        <EventCalendar showLikedOnly={showLikedOnly} />
      )}
    </div>
  );
}
