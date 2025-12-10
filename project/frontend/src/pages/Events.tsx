import { useState } from "react";
import { Typography, Card, Space } from 'antd';
import EventList from '../components/EventList';
import EventCalendar from '../components/EventCalendar';
import EventSortControls from "../components/EventSortButton";
import type { SortOption } from "../components/EventSortButton";
import LikedFilterButton from "../components/LikedFilterButton";
import ViewToggleButton from "../components/ViewToggleButton";
import { useAuth } from '../hooks/useAuth';
import "../components/css/Events.css";

const { Title, Paragraph } = Typography;

export default function Events() {
  // State to hold the current sorting option for events
  const [sortOption, setSortOption] = useState<SortOption>("date-asc");

  // State to hold whether to show only liked events
  const [showLikedOnly, setShowLikedOnly] = useState<boolean>(false);

  // State to toggle between list and calendar views
  const [viewMode, setViewMode] = useState<"list" | "calendar">("list");

  const { user } = useAuth();

  const userExists = user !== null;

  let hasSuggestedEvents = false;

  if (userExists) {
    hasSuggestedEvents = Boolean(user.suggested_event_ids && user.suggested_event_ids.length > 0);
  }

  return (
    <div className="events-page">

      {userExists ? (
        <Title level={2}>Hi {user.first_name}! Here are your event recommendations</Title>
      ) : (
        <Title level={2}>Welcome!</Title>
      )}

      {userExists ? (
        hasSuggestedEvents ? (
          <>
            <EventList
              suggestedEventIds={user.suggested_event_ids}
              sortOption={"none"}
              showLikedOnly={false}
            />
          </>
        ) : (
          <Card className="event-recommendation-card">
            <div className="event-list-empty">
              <Paragraph type="secondary">
                No recommended events yet. Update your interests in Settings to get personalized event recommendations!
              </Paragraph>
            </div>
          </Card>
        )
      ) : (
        <div className="events-page">
          <Paragraph>Please log in to view personalized event recommendations.</Paragraph>
        </div>
      )}

      <Space direction="vertical" size="large"> </Space>

      <Title level={2}>All Events</Title>

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

      {/* Toggle between list and calendar views */}
      {viewMode === "list" ? (
        <EventList sortOption={sortOption} showLikedOnly={showLikedOnly} />
      ) : (
        <EventCalendar showLikedOnly={showLikedOnly} />
      )}
    </div>
  );
}