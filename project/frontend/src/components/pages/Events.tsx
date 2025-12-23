import { useState } from "react";
import { Typography, Card, Input, Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import EventList from '../EventList';
import EventCalendar from '../EventCalendar';
import EventSortControls from "../buttons/EventSortButton";
import type { SortOption } from "../buttons/EventSortButton";
import LikedFilterButton from "../buttons/LikedFilterButton";
import GoingFilterButton from "../buttons/GoingFilterButton";
import ViewToggleButton from "../buttons/ViewToggleButton";
import SubeventToggleButton from "../buttons/SubeventToggleButton";
import { useAuth } from '../../hooks/useAuth';
import "../css/Events.css";

const { Title, Paragraph } = Typography;

export default function Events() {
  // State to hold the current sorting option for events
  const [sortOption, setSortOption] = useState<SortOption>("date-asc");

  // State to hold whether to show only liked events
  const [showLikedOnly, setShowLikedOnly] = useState<boolean>(false);

  // State to hold whether to show only going events
  const [showGoingOnly, setShowGoingOnly] = useState<boolean>(false);

  // State to toggle between list and calendar views
  const [viewMode, setViewMode] = useState<"list" | "calendar">("list");

  // State to toggle showing subevents
  const [showSubevents, setShowSubevents] = useState<boolean>(false);

  // State for search query across events
  const [searchQuery, setSearchQuery] = useState<string>("");

  const { user, isRecommendationLoading } = useAuth();

  const userExists = user !== null;

  let hasSuggestedEvents = false;

  if (userExists) {
    hasSuggestedEvents = Boolean(user.suggested_event_ids && user.suggested_event_ids.length > 0);
  }

  return (
    <div className="events-page">

      {userExists ? (
        <Title level={2}>Hi {user.first_name}! Here are your event recommendations</Title>
      ) : null }

      {userExists ? (
        isRecommendationLoading ? (
          <Card className="event-recommendation-card">
            <div className="event-list-loading">
              <Spin indicator={<LoadingOutlined spin />} size="large" />
              <Paragraph type="secondary" style={{ marginTop: 16 }}>
                Your event recommendations will appear momentarily...
              </Paragraph>
            </div>
          </Card>
        ) : hasSuggestedEvents ? (
          <>
            <EventList
              suggestedEventIds={user.suggested_event_ids?.map(String)}
              sortOption={"none"}
              showLikedOnly={false}
              fetchMode="main_events"
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
      ) : null}


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
        <GoingFilterButton
          showGoingOnly={showGoingOnly}
          onChange={setShowGoingOnly}
        />
        <ViewToggleButton
          viewMode={viewMode}
          onToggle={setViewMode}
        />
        <SubeventToggleButton
          showSubevents={showSubevents}
          onToggle={setShowSubevents}
        />

        <div className="events-page-search">
          <Input.Search
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            allowClear
            placeholder='Search events'
          />
        </div>
      </div>

      {/* Toggle between list and calendar views */}
      {viewMode === "list" ? (
        <EventList 
          sortOption={sortOption} 
          showLikedOnly={showLikedOnly} 
          showGoingOnly={showGoingOnly}
          fetchMode={showSubevents ? "all_events" : "main_events"}
          searchQuery={searchQuery}
          enablePagination={true}
        />
      ) : (
        <EventCalendar 
          showLikedOnly={showLikedOnly} 
          showGoingOnly={showGoingOnly}
          fetchMode={showSubevents ? "all_events" : "main_events"}
        />
      )}
    </div>
  );
}