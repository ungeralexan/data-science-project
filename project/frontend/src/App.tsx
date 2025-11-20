import { Layout } from 'antd';
import { Route, Routes } from 'react-router-dom';

import NavBar from './components/NavBar'
import Profile from './pages/Profile';
import Events from './pages/Events';
import Settings from './pages/Settings';

/*
  App.tsx serves as the main layout component for the application, defining the structure
  and routing for different pages.

  <Layout>:
    Layout is a component from Ant Design that provides a flexible and responsive layout structure.
    It helps in organizing the content into different sections like header, footer, and content area.
  
  <Layout.Header>:
    Layout.Header is a specific section of the Layout component that represents the top header area.
    It contains navigation elements, branding, or other important information.
  
  <Layout.Content>:
    Layout.Content is another section of the Layout component that represents the main content area.
    This is where the primary content of each page is displayed based on the current route.
  
  <Routes> and <Route>:
    Routes is a component from React Router that manages the routing of the application.
    It contains multiple Route components, each defining a specific path and the corresponding component
    to render when that path is accessed.

  The layout of the frontend application is as follows:
    
    App.tsx
      ├── Layout.Header (contains NavBar)
      └── Layout.Content (renders different pages based on routing)
          ├── Profile (at path "/")
          ├── Events (at path "/events")
          └── Settings (at path "/settings")
*/
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