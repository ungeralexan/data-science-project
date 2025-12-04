import { Layout } from 'antd';
import { Route, Routes } from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import NavBar from './components/NavBar'
import Profile from './pages/Profile';
import Events from './pages/Events';
import Settings from './pages/Settings';
import EventDetail from "./pages/EventDetail";
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import './components/css/App.css';

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

  <AuthProvider>:
    AuthProvider wraps the application and provides authentication context to all child components.
    This allows any component to access user authentication state and functions.

  <ProtectedRoute>:
    ProtectedRoute wraps routes that require authentication. If the user is not logged in,
    they are redirected to the login page.

  The layout of the frontend application is as follows:
    
    App.tsx
      ├── AuthProvider (provides authentication context)
      └── Layout
          ├── Layout.Header (contains NavBar)
          └── Layout.Content (renders different pages based on routing)
              ├── Login (at path "/login") - public
              ├── Register (at path "/register") - public
              ├── Profile (at path "/") - protected
              ├── Events (at path "/events") - protected
              └── Settings (at path "/settings") - protected
*/
export default function App() {
  return (
    <AuthProvider>
      <Layout>

        <Layout.Header className="app-header">
          <div className="app-logo">

            tuevent
          </div>

          <NavBar />
        </Layout.Header>

        <Layout.Content className="app-content">
          
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            
            {/* Protected routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />

            <Route path="/events" element={
              <ProtectedRoute>
                <Events />
              </ProtectedRoute>
            } />
            <Route path="/events/:id" element={
              <ProtectedRoute>
                <EventDetail />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            } />
          </Routes>
        </Layout.Content>
        
      </Layout>
    </AuthProvider>
  );
}