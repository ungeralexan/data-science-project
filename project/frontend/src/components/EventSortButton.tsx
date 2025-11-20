// src/components/EventSortControls.tsx
import React from "react";
import "./css/EventList.css"; // reuse same CSS file for controls styling

/*
  SortOption:
    SortOption is a TypeScript type that defines the possible sorting options for events.
    It is a union type, meaning it can be one of several specified string literals.

  EventSortControlsProps:
    EventSortControlsProps is a TypeScript interface that defines the props for the EventSortControls component.
    It includes the current sort option and a callback function to handle changes to the sort option.
    A callback function is a function that is passed as an argument to another function and is executed after some operation is completed.
    Here , it is used to notify the parent component when the user selects a different sort option.

  EventSortControls:
    EventSortControls is a React functional component that renders a dropdown menu for selecting event sorting options.
    It takes in the current sort option and a change handler as props, and calls the change handler when a new option is selected.
*/

// Define the possible sorting options for events
export type SortOption =
  | "title-asc"
  | "title-desc"
  | "date-asc"
  | "date-desc"
  | "time-asc"
  | "time-desc";

// Define the props for the EventSortControls component
interface EventSortControlsProps {
  sortOption: SortOption;
  onChange: (value: SortOption) => void; 
}

// EventSortControls component definition
const EventSortControls: React.FC<EventSortControlsProps> = ({
  sortOption,
  onChange,
}) => {
  return (
    <div className="event-list-controls">
      <label className="event-list-sort-label">
        Sort Events:&nbsp;
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
      </label>
    </div>
  );
};

export default EventSortControls;
