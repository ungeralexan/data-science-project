// src/pages/Profile.tsx
import { Typography, Card } from 'antd';
import { useAuth } from '../hooks/useAuth';
import '../components/css/Profile.css';

/*
  This page displays recommended events
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

    return (
        <div className="profile-page">
            <Title level={2}>Event Recommendations</Title>

            {/* Recommended Events Section */}
            <Card className="profile-card" title="Recommended Events">
                <div className="profile-recommended-empty">
                    <Paragraph type="secondary">
                        No recommended events yet. Update your interests in Settings to get personalized event recommendations!
                    </Paragraph>
                </div>
            </Card>
        </div>
    );
}
