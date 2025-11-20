// src/pages/Events.tsx
import { useState } from "react";
import { Typography } from 'antd';
import EventList from '../components/EventList';

import EventSortControls from "../components/EventSortButton";
import type { SortOption } from "../components/EventSortButton";

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
  
  useState:
    useState is a React hook that allows functional components to have state variables. In this case, it is used
    to manage the current sorting option for the events.
*/

const { Title } = Typography;

export default function Events() {

  // State to hold the current sorting option for events
  const [sortOption, setSortOption] = useState<SortOption>("date-asc");

  // Render the Events page with title, sorting controls, and event list
  return (
    <div>
      <Title level={2}>Events</Title>
      <EventSortControls
        sortOption={sortOption}
        onChange={setSortOption}
      />
      <EventList sortOption={sortOption} />
    </div>
  );
}
