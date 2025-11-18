import { Layout } from 'antd';
import { Route, Routes } from 'react-router-dom';

import NavBar from './components/NavBar'
import Profile from './pages/Profile';
import Events from './pages/Events';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Layout>

      <Layout.Header
        style={{
            background: '#fff',
            color: 'rgba(0, 0, 0, 0.88)',
            display: 'flex', // Determines the layout of items in the header. With flex, they can appear next to each other
            gap: 15, // Determines the space between items in the header
            paddingInline: 20 // Determines how much white space there is on the left and right side of header
          }}
      >
        <div style={{ 
          fontWeight: 500,
          fontSize: 22
        }}>
          tuevent
        </div>

        <NavBar />
        
      </Layout.Header>

      <Layout.Content style = {{ padding: '24px', minHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<Profile />} />
          <Route path="/events" element={<Events />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout.Content>
      
    </Layout>
  );
}