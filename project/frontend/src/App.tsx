import { Layout } from 'antd';
import { Route, Routes, Link } from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import ScrollToTop from './components/ScrollToTop';
import NavBar from './components/NavBar'
import Events from './pages/Events';
import Settings from './pages/Settings';
import EventDetail from "./pages/EventDetail";
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import WelcomePopup from "./components/WelcomePopup";
import './components/css/App.css';
import './components/css/ColorPalette.css';
import './components/css/AntDesignOverrides.css';

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
*/
export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ScrollToTop />
        <Layout>
          
          <WelcomePopup />
          <Layout.Header className="app-header">
            <Link to="/events" className="app-logo">
              tuevent
            </Link>

            <NavBar />
          </Layout.Header>

          <Layout.Content className="app-content">
          
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              
              {/* Public routes - events can be viewed without login */}
              <Route path="/" element={<Events />} />
              <Route path="/events" element={<Events />} />
              <Route path="/events/:id" element={<EventDetail />} />

              {/* Protected routes - require authentication */}
              <Route path="/settings" element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              } />
            </Routes>
          </Layout.Content>
        </Layout>
      </AuthProvider>
    </ThemeProvider>
  );
}