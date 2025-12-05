// src/pages/Profile.tsx
import { Typography, Card } from 'antd';
import { useAuth } from '../hooks/useAuth';
import EventList from '../components/EventList';
import '../components/css/Profile.css';

/*
  This page displays recommended events based on the user's interests.
  It uses the EventList component filtered by the user's suggested_event_ids.
*/

const { Title, Paragraph } = Typography;

export default function Profile() {
    const { user } = useAuth();

    if (!user) {
        return (
            <div className="profile-page">
                <Title level={2}>Event Recommendations</Title>
                <Paragraph>Please log in to view your profile.</Paragraph>
            </div>
        );
    }

    const hasSuggestedEvents = user.suggested_event_ids && user.suggested_event_ids.length > 0;

    return (
        <div className="profile-page">
            <Title level={2}>Hi {user.first_name}! Here are your event recommendations</Title>

            {/* Recommended Events Section */}
            {hasSuggestedEvents ? (
                <EventList 
                    sortOption="date-asc" 
                    suggestedEventIds={user.suggested_event_ids} 
                />
            ) : (
                <Card className="profile-card">
                    <div className="profile-recommended-empty">
                        <Paragraph type="secondary">
                            No recommended events yet. Update your interests in Settings to get personalized event recommendations!
                        </Paragraph>
                    </div>
                </Card>
            )}
        </div>
    );
}
