// src/pages/Events.tsx
import { useState } from "react";
import { Typography } from 'antd';
import EventList from '../components/EventList';
import EventSortControls from "../components/EventSortButton";
import type { SortOption } from "../components/EventSortButton";
import LikedFilterButton from "../components/LikedFilterButton";
import "../components/css/Events.css";

/*
  Events.tsx is the main page component for displaying a list of events. It includes sorting functionality
  to allow users to sort events based on different criteria.

  Typography:
    Typography is a component from Ant Design that provides various typographic elements like titles, paragraphs,
    and text styles to enhance the visual presentation of text content.
  
  EventList:
    EventList is a custom component that fetches and displays a list of events. It takes a sortOption prop
    to determine the order in which events are displayed.
  
  EventSortControls:
    EventSortControls is a custom component that provides UI controls for selecting the sorting option. It takes
    sortOption and onChange props to manage the current sorting state.
  
  LikedFilterButton:
    LikedFilterButton is a custom component that provides a toggle button to filter events by liked status.
  
  useState:
    useState is a React hook that allows functional components to have state variables. In this case, it is used
    to manage the current sorting option for the events.
*/

const { Title } = Typography;

export default function Events() {

  // State to hold the current sorting option for events
  const [sortOption, setSortOption] = useState<SortOption>("date-asc");
  
  // State to hold whether to show only liked events
  const [showLikedOnly, setShowLikedOnly] = useState<boolean>(false);

  // Render the Events page with title, sorting controls, and event list
  return (
    <div className="events-page">
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
      </div>
      
      <EventList sortOption={sortOption} showLikedOnly={showLikedOnly} />
    </div>
  );
}
