// components/NavBar.tsx
import { Menu, Button, Space } from 'antd';
import type { MenuProps } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  UserOutlined,
  CalendarOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import './css/NavBar.css';

/*
  Define the navigation items for the NavBar.

  MenuProps:
    MenuProps is a TypeScript type from Ant Design that defines the properties for the Menu component.
    A type is a way to specify the shape of an object, including the types of its properties.

  Link:
    Link is a component from React Router that enables navigation between different routes in a single-page application

  useLocation:
    useLocation is a hook from React Router that provides access to the current location object, 
    which contains information about the current URL.

  Menu:
    Menu is a component from Ant Design that provides a navigation menu. It supports various modes and themes,
    and allows for easy creation of navigation bars.
  
  Icons:
    UserOutlined, CalendarOutlined, and SettingOutlined are icon components from Ant Design that represent
    user profile, calendar/events, and settings respectively.

  useAuth:
    useAuth is a custom hook that provides access to the authentication context, including user info
    and logout functionality.
*/

// Navigation items for authenticated users
const authenticatedItems: MenuProps['items'] = [
  { key: '/',        icon: <UserOutlined />,    label: <Link to="/">Profile</Link> },
  { key: '/events',  icon: <CalendarOutlined />,label: <Link to="/events">Events</Link> },
  { key: '/settings',icon: <SettingOutlined />, label: <Link to="/settings">Settings</Link> },
];

// Navigation items for unauthenticated users (empty - they see login/register buttons)
const unauthenticatedItems: MenuProps['items'] = [];

export default function NavBar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  /*
    Get the current URL path to determine which menu item should be highlighted as selected.

    pathname: The pathname property of the location object contains the path of the current URL.
    rootPath: This variable extracts the root path segment from the pathname to match against menu item keys.
    selected: This variable determines the selected menu item key based on the current URL.
  */
  const { pathname } = useLocation();
  const rootPath = '/' + pathname.split('/')[1];
  const selected = rootPath === '//' ? '/' : rootPath;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  /*
    Render the navigation bar with menu items and highlight the selected item based on the current URL.

    mode: This property sets the menu to horizontal mode for a top navigation bar.
    theme: This property sets the theme of the menu to light.
    items: This property provides the menu items defined earlier.
    selectedKeys: This property highlights the currently selected menu item based on the URL.
    style: This property customizes the menu's appearance to remove the bottom border and make it flush with the header.
  */
  return (
    <div className="navbar-container">
      <Menu
        mode="horizontal"
        theme="light"

        // Menu items are chosen based on authentication status
        items={isAuthenticated ? authenticatedItems : unauthenticatedItems}
        selectedKeys={[selected]}
        className="navbar-menu"
      />
      
      {/* if authenticated, show greeting and logout button */}
      {isAuthenticated ? (
        <Space>
          <Button 
            icon={<LogoutOutlined />} 
            onClick={handleLogout}
            type="text"
          >
            Logout
          </Button>
        </Space>
      ) : (
        <Space>
          <Link to="/login">
            <Button type="text">Sign In</Button>
          </Link>
          <Link to="/register">
            <Button type="primary">Sign Up</Button>
          </Link>
        </Space>
      )}
    </div>
  );
}
