// src/pages/Events.tsx
import { Typography } from 'antd';
import EventList from '../components/EventList';

const { Title } = Typography;

export default function Events() {
  return (
    <div>
      <Title level={2}>Events</Title>
      <EventList />
    </div>
  );
}
