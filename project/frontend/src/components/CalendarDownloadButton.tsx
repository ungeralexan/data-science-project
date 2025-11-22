// src/components/CalendarDownloadButtons.tsx
import React from "react";
import { Button } from "antd";
import type { Event } from "../types/Event";

/*
    CalendarDownloadButtons.tsx provides a button to download an event's details as an ICS file for calendar applications.

    CalendarDownloadButtonsProps
        event: An Event object containing details like title, start/end dates and times, location, description, and URL.

    Functions:

    parseUSDateTime:
        Parses US-format date (MM/DD/YYYY) and time (HH:MM AM/PM) strings into ICS-compatible date and date-time formats.

    buildICSForEvent: 
        Constructs the ICS file content for a given event, including fields like summary, start/end times, location, and description.

    downloadICS:
        Creates a downloadable ICS file from the provided content and triggers the download in the browser.

    CalendarDownloadButtons Component:
        A React functional component that renders a button. When clicked, it generates the ICS file for the provided event
        and initiates the download.
*/

type CalendarDownloadButtonsProps = {
  event: Event;
};

type ParsedICSDate = {
  date: string;      // "YYYYMMDD"
  dateTime?: string; // "YYYYMMDDTHHMMSS"
};

// Parse US-format date and time into ICS date/date-time format
function parseUSDateTime(dateStr?: string, timeStr?: string):
 ParsedICSDate | null {

  // If no date provided, return null
  if (!dateStr) return null;

  // Expect date in "MM/DD/YYYY" format
  const [monthStr, dayStr, yearStr] = dateStr.split("/");

  // If any part of the date is missing, return null
  if (!monthStr || !dayStr || !yearStr) return null;

  // Pad month, day, year to ensure correct format. If any part is missing, default to "00"
  const year = yearStr.padStart(4, "0");
  const month = monthStr.padStart(2, "0");
  const day = dayStr.padStart(2, "0");

  // Base date in "YYYYMMDD" format
  const baseDate = `${year}${month}${day}`;

  // If no time provided, return just the date (all-day event)
  if (!timeStr) {
    // All-day event
    return { date: baseDate };
  }

  // Expect e.g. "6:30 PM" or "06:30 AM"
  const [timePart, ampmRaw] = timeStr.trim().split(/\s+/);

  // if time part or AM/PM part is missing, return just the date
  if (!timePart || !ampmRaw) {
    return { date: baseDate };
  }

  // Split time part into hours and minutes
  const [hourStr, minuteStr = "00"] = timePart.split(":");

  // If hour part is missing, return just the date
  if (!hourStr) {
    return { date: baseDate };
  }

  // Convert hour and minute to integers
  let hour = parseInt(hourStr, 10);
  const minute = parseInt(minuteStr, 10) || 0;
  const ampm = ampmRaw.toUpperCase();

  // Convert 12h -> 24h
  if (ampm === "PM" && hour !== 12) {
    hour += 12;
  } else if (ampm === "AM" && hour === 12) {
    hour = 0;
  }

  // Pad hour and minute to ensure two digits
  const hh = String(hour).padStart(2, "0");
  const mm = String(minute).padStart(2, "0");

  // Local time, no timezone marker and no "Z"
  const dateTime = `${baseDate}T${hh}${mm}00`;

  return { date: baseDate, dateTime };
}

// Build the ICS file content for a given event
function buildICSForEvent(event: Event): string {

  // Parse start and end date/times
  const start = parseUSDateTime(event.start_date, event.start_time);

  // If no end date/time, use start date/time
  const end = parseUSDateTime(
    event.end_date || event.start_date,
    event.end_time || event.start_time
  );

  const safeSummary = (event.title || "Event").replace(/\r?\n/g, " "); // Replace newlines with spaces
  const description = (event.description || "").replace(/\r?\n/g, "\\n"); // Replace newlines with \n 
  const location = (event.location || "").replace(/,/g, "\\,");
  const uid = `event-${event.id}@ut-events`;

  // https://en.wikipedia.org/wiki/ICalendar
  const lines = [
    "BEGIN:VCALENDAR", //BEGIN = start of calendar data
    "VERSION:2.0", //VERSION = iCalendar version
    "PRODID:-//UT Events//EN", //PRODID = product identifier -> identifies the product that created the iCalendar object
    "CALSCALE:GREGORIAN", //CALSCALE = calendar scale -> specifies the calendar system used
    "METHOD:PUBLISH", //METHOD = method associated with the calendar -> indicates the purpose of the calendar data
    "BEGIN:VEVENT", //BEGIN = start of an event
    `UID:${uid}`, //UID = unique identifier for the event
    `SUMMARY:${safeSummary}`, //SUMMARY = title or summary of the event

    // DISTART = start date/time of the event. If time is included, it's a date-time; otherwise, it's an all-day event.
    start?.dateTime ? `DTSTART:${start.dateTime}` : start ? `DTSTART;VALUE=DATE:${start.date}` : "", 

    // DTEND = end date/time of the event. If time is included, it's a date-time; otherwise, it's an all-day event.
    end?.dateTime ? `DTEND:${end.dateTime}` : end ? `DTEND;VALUE=DATE:${end.date}` : "",

    location ? `LOCATION:${location}` : "", //LOCATION = location of the event
    description ? `DESCRIPTION:${description}` : "", //DESCRIPTION = description of the event
    event.url ? `URL:${event.url}` : "", //URL = URL associated with the event
    "END:VEVENT", // END = end of an event
    "END:VCALENDAR", // END = end of calendar data
    "",
  ].filter(Boolean); // Remove any empty lines

  // ICS files typically use CRLF line endings
  return lines.join("\r\n");
}

// Trigger download of the ICS file in the browser
function downloadICS(fileName: string, content: string) {

  // Create a Blob from the ICS content. A Blob is a file-like object of immutable, raw data. 
  // It is used for storing data that can be read as text or binary data.
  const blob = new Blob([content], {
    type: "text/calendar;charset=utf-8",
  });

  // Create a temporary link to trigger the download
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url; // Set the href and download attributes for the link
  a.download = fileName; // Set the file name for the download
  document.body.appendChild(a); // Append the link to the document body

  a.click(); // Programmatically click the link to start the download
  a.remove(); // Remove the link from the document
  URL.revokeObjectURL(url); // Release the object URL
}

// Props for the CalendarDownloadButtons component
const CalendarDownloadButtons: React.FC<CalendarDownloadButtonsProps> = ({
  event,
}) => {

  // Handle the button click to generate and download the ICS file
  const handleDownloadCalendar = () => {
    const ics = buildICSForEvent(event);
    const safeTitle = (event.title || "event").replace(/[^a-z0-9]+/gi, "-");

    downloadICS(`${safeTitle}.ics`, ics);
  };

  return (
  <div>
    <Button type="primary" size="large" className="event-detail-calendar-button" onClick={handleDownloadCalendar}>
      Add to calendar (.ics)
    </Button>
  </div>
);
};

export default CalendarDownloadButtons;
