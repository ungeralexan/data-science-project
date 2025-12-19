// src/components/EventCalendar.tsx
import { useMemo, useState } from "react";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useEvents } from "../hooks/useEvents";
import type { EventFetchMode } from "../hooks/useEvents";
import { useAuth } from "../hooks/useAuth";
import type { Event } from "../types/Event";
import "./css/EventCalendar.css";

/*
    This file defines the EventCalendar component, which displays events in a monthly calendar view.
*/

// -------- Props Interface --------
interface EventCalendarProps {
    showLikedOnly?: boolean;
    showGoingOnly?: boolean;
    suggestedEventIds?: (string | number)[] | null;
    fetchMode?: EventFetchMode;  // "main_events" | "all_events" | "sub_events"
}

// -------- Constants --------
const WEEKDAY_LABELS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const WEEKDAY_LABELS_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// -------- Helper Functions --------

// Pad single digit numbers with leading zero (Used for date keys)
function pad(num: number) {
  return num.toString().padStart(2, "0");
}

// Generate a date key in YYYY-MM-DD format
function dateKey(d: Date) {
  // Build YYYY-MM-DD in local time to avoid TZ drift
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function parseTimeToMinutes(timeStr?: string | null) {
    if (!timeStr) return NaN;
    const clean = timeStr.split(" ")[0]; // "HH:MM" or first part
    const [hh, mm] = clean.split(":");
    const h = Number(hh);
    const m = Number(mm ?? "0");
    if (isNaN(h) || isNaN(m)) return NaN;
    return h * 60 + m;
}

// Today's date key
// Date() is a built-in JavaScript object that represents a single moment in time.
// It is initialized to the current date and time when called without arguments.
const TODAY_KEY = dateKey(new Date());

// -------- Component --------

export default function EventCalendar({ showLikedOnly = false, showGoingOnly = false, suggestedEventIds, fetchMode = "main_events" }: EventCalendarProps) {

    // ----- State & Hooks -----

    const { events, error, isLoading } = useEvents(fetchMode); // Query events from backend
    const navigate = useNavigate(); // For navigating to event details page
    const { likedEventIds, goingEventIds } = useAuth(); // Get liked/going event IDs from auth context

    // State to track the currently displayed month
    const [currentMonth, setCurrentMonth] = useState<Date>(() => {
        const now = new Date();

        // Arguments : {year, monthIndex, day}
        return new Date(now.getFullYear(), now.getMonth(), now.getDay()); 
    });

    // Filter events by suggested IDs and liked-only toggle
    const filteredEvents = useMemo(() => {
        let result: Event[] = events;

        if (suggestedEventIds && suggestedEventIds.length > 0) {
            const suggestedSet = new Set(suggestedEventIds.map(String));
            result = result.filter((e) => suggestedSet.has(String(e.id)));
        }

        if (showLikedOnly) {
            const likedSet = new Set(likedEventIds.map(String));
            result = result.filter((e) => likedSet.has(String(e.id)));
        }

        if (showGoingOnly) {
            const goingSet = new Set(goingEventIds.map(String));
            result = result.filter((e) => goingSet.has(String(e.id)));
        }

        return result;
    }, [events, showLikedOnly, showGoingOnly, suggestedEventIds, likedEventIds, goingEventIds]);

    // Group events by date key for quick lookup
    const eventsByDate = useMemo(() => {

        //Format: Map<dateKey, Event[]> -> Each date has a list of events
        const map = new Map<string, Event[]>();

        // Loop over each event
        filteredEvents.forEach((event) => {

            // Skip events without a valid start date
            if (!event.start_date) return;

            // Create Date object from start_date
            const d = new Date(event.start_date);

            // Skip invalid dates
            if (isNaN(d.getTime())) return;

            // Get date key (YYYY-MM-DD) and add event to corresponding list
            const key = dateKey(d);

            // Get existing list of events for this date or create a new one
            const list = map.get(key) || [];

            // Add event to the list for this date
            list.push(event);

            // Update map 
            map.set(key, list);

        });

        // Sort events in each day by start_time
        for (const [key, list] of map.entries()) {

            /*
                Sort events by start_time within the day

                ta output = total minutes from midnight for event a
                tb output = total minutes from midnight for event b
            */

            list.sort((a, b) => {
                const ta = parseTimeToMinutes(a.start_time);
                const tb = parseTimeToMinutes(b.start_time);

                // Handle NaN values by treating them as 0
                return (isNaN(ta) ? 0 : ta) - (isNaN(tb) ? 0 : tb);
            });

            // Update map with sorted list
            map.set(key, list);
        }

        // Return the map of events grouped by date
        return map;

    }, [filteredEvents]); // Changes if filteredEvents changes

    // Build cells for current month
    const monthCells = useMemo(() => {

        // Get year and month from currentMonth state (Currently displayed month)
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();

        // Determine the starting day of the week for the month (0 = Sun, 1 = Mon, 2 = Tue, etc.)
        const startDay = new Date(year, month, 1).getDay(); // If month starts on Wed, startDay = 3
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Initialize an array to hold the cells for the calendar grid
        const cells: Array<{ 
            day: number; // Day of the month (0 for blank cells)
            key: string; // Date key (YYYY-MM-DD) or blank identifier
            events: Event[] // List of events on that day
        }> = [];

        // For blank cells before the first day of the month
        for (let i = 0; i < startDay; i += 1) {
            cells.push({ 
                day: 0, 
                key: `blank-${i}`, 
                events: [] 
            });
        }

        // For each day of the month
        for (let day = 1; day <= daysInMonth; day += 1) {
            
            const d = new Date(year, month, day); // Create Date object for the day
            const key = dateKey(d); // Generate date key (YYYY-MM-DD)
            
            // Add cell with events for that day
            cells.push({ 
                day, // Day of the month
                key, // Date key
                events: eventsByDate.get(key) // Get events for this date or empty array
                || [] 
            });
        }

        return cells;

    }, [currentMonth, eventsByDate]);

    // ----- Helper Functions -----

    // Sets the currentMonth state to the previous month
    const handlePrevMonth = () => {
        setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
    };

    // Sets the currentMonth state to the next month
    const handleNextMonth = () => {
        setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
    };

    // Generate month label (e.g., "March 2024")
    const monthLabel = currentMonth.toLocaleString(undefined, { month: "long", year: "numeric" });

    if (isLoading) {
        return <div className="event-calendar">Loading calendar...</div>;
    }

    if (error) {
        return <div className="event-calendar-error">Error: {error}</div>;
    }

    // ----- Rendering -----

    return (
        <div className="event-calendar">
            <div className="event-calendar-header">

                {/* Navigation buttons for previous and next month */}

                <button className="event-calendar-nav" onClick={handlePrevMonth} aria-label="Previous month">
                    <LeftOutlined />
                </button>

                <div className="event-calendar-month">
                    {monthLabel}
                </div>

                <button className="event-calendar-nav" onClick={handleNextMonth} aria-label="Next month">
                    <RightOutlined />
                </button>
            </div>

            {/* Grid displaying the days of the month and their events */}
            <div className="event-calendar-grid">
                
                {/* Shows the labels for the days of the week */}
                {WEEKDAY_LABELS.map((label, index) => (
                    <div key={label} className="event-calendar-weekday">
                        <span className="weekday-full">{label}</span>
                        <span className="weekday-short">{WEEKDAY_LABELS_SHORT[index]}</span>
                    </div>
                ))}

                 {/* Shows the cells for each day of the month */}
                {monthCells.map((cell) => (
                
                    <div
                        key = {cell.key}

                        // If day is 0, it's a blank cell; if key matches TODAY_KEY, highlight it
                        // If its today apply special styling

                        /*
                            Syntax Comment: ${}${} is used for embedding expressions inside template literals
                        
                            If cell.day === 0, add "event-calendar-cell--blank" class for blank cells
                            If cell.key === TODAY_KEY, add "event-calendar-cell--today" class for today's date

                            Possible results:

                            "event-calendar-cell "
                            "event-calendar-cell event-calendar-cell--blank"
                            "event-calendar-cell event-calendar-cell--today"
                        */
                        className={
                            `event-calendar-cell ${
                                cell.day === 0 
                                ? "event-calendar-cell--blank" 
                                : ""
                            } ${
                                cell.key === TODAY_KEY 
                                ? "event-calendar-cell--today" 
                                : ""
                            }`
                        }
                    >
                        {/* If cell.day is not 0, render the day number and events */}
                        {cell.day !== 0 && (
                        <>
                            {/* Render the day number */}
                            <div className="event-calendar-day-number">
                                {cell.day}
                            </div>
                            
                            {/* Render the events */}
                            <div className="event-calendar-events">

                                {/* If there are no events, show an empty placeholder */}
                                {cell.events.length === 0 ? (
                                    <span className="event-calendar-empty" />
                                ) : (

                                    // Render each event in the cell
                                    cell.events.map((ev) => (
                                        <div
                                            key={ev.id}
                                            className="event-calendar-event"
                                            onClick={() => navigate(`/events/${ev.id}`)} // Navigate to event details on click
                                            role="button"
                                            tabIndex={0} // You can click "tab" on your keyboard to select events
                                            onKeyDown={(e) => {

                                                //If "Enter" or "Space" is pressed, navigate to event details
                                                if (e.key === "Enter" || e.key === " ") 
                                                    navigate(`/events/${ev.id}`);
                                            }}
                                        >
                                            {/* Shows Start Time & Title */}
                                            <span className="event-calendar-event-time">
                                                {ev.start_time || ""}
                                            </span>
                                            <span className="event-calendar-event-title">
                                                {ev.title}
                                            </span>
                                        </div>
                                    ))
                                )}
                            </div>
                        </>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
