// src/components/EventSortControls.tsx
import React from "react";
import { SortAscendingOutlined } from "@ant-design/icons";
import "./css/EventList.css"; // reuse same CSS file for controls styling
import "./css/Events.css";

/*
  EventSortControls.tsx defines a React component that provides sorting controls for the event list.
  It allows users to select different sorting options such as title, date, and time in ascending or descending order.

  SortOption:
    SortOption is a TypeScript type that defines the possible sorting options available for events.
  
  EventSortControlsProps:
    EventSortControlsProps is a TypeScript interface that defines the props accepted by the EventSortControls component.
    It includes the current sortOption and an onChange function to handle changes in the selected sorting option.
  
  EventSortControls:
    EventSortControls is a React functional component that renders a dropdown menu for selecting the sorting option.
    It uses the sortOption prop to set the current selection and calls the onChange prop when the user selects a different option.
*/

// Define the possible sorting options for events
export type SortOption =
  | "title-asc"
  | "title-desc"
  | "date-asc"
  | "date-desc"
  | "time-asc"
  | "time-desc"
  | "none";

// Define the props for the EventSortControls component
interface EventSortControlsProps {
  sortOption: SortOption;
  onChange: (value: SortOption) => void; 
  compact?: boolean;
}

// EventSortControls component definition
const EventSortControls: React.FC<EventSortControlsProps> = ({
  sortOption,
  onChange, compact = false
}) => {
  if (compact) {
    return (
      <div className="events-sort-compact">
        {/* icon + text “Sort” */}
        <SortAscendingOutlined />
        <span className="events-sort-compact-label">Sort</span>

        {/* invisible select overlay to keep native dropdown behavior */}
        <select
          className="events-sort-compact-select"
          value={sortOption}
          onChange={(e) => onChange(e.target.value as SortOption)}
          aria-label="Sort events"
          title="Sort"
        >
          <option value="title-asc">Title (A → Z)</option>
          <option value="title-desc">Title (Z → A)</option>
          <option value="date-asc">Start date (earliest → latest)</option>
          <option value="date-desc">Start date (latest → earliest)</option>
          <option value="time-asc">Start time (earliest → latest)</option>
          <option value="time-desc">Start time (latest → earliest)</option>
        </select>
      </div>
    );
  }

  return (
    <div className="event-list-controls">
      <select
          className="event-list-sort-select"
          value={sortOption}

          /*
            onChange:
              onChange is an event handler that is called when the user selects a different option from the dropdown menu.
              It takes the event object as an argument and calls the onChange prop with the selected value cast to SortOption type.
              Then, the parent component can update its state based on the new sort option.
              As a result, the event list will be re-sorted according to the user's selection.
          */
          onChange={(e) => onChange(e.target.value as SortOption)}
        >
          <option value="title-asc">Title (A → Z)</option>
          <option value="title-desc">Title (Z → A)</option>
          <option value="date-asc">Start date (earliest → latest)</option>
          <option value="date-desc">Start date (latest → earliest)</option>
          <option value="time-asc">Start time (earliest → latest)</option>
          <option value="time-desc">Start time (latest → earliest)</option>
        </select>
    </div>
  );
};

export default EventSortControls;
