// components/NavBar.tsx
import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  UserOutlined,
  CalendarOutlined,
  SettingOutlined,
} from '@ant-design/icons';

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


*/
const items: MenuProps['items'] = [
  { key: '/',        icon: <UserOutlined />,    label: <Link to="/">Profile</Link> },
  { key: '/events',  icon: <CalendarOutlined />,label: <Link to="/events">Events</Link> },
  { key: '/settings',icon: <SettingOutlined />, label: <Link to="/settings">Settings</Link> },
];

export default function NavBar() {

  /*
    Get the current URL path to determine which menu item should be highlighted as selected.

    pathname: The pathname property of the location object contains the path of the current URL.
    rootPath: This variable extracts the root path segment from the pathname to match against menu item keys.
    selected: This variable determines the selected menu item key based on the current URL.
  */
  const { pathname } = useLocation();
  const rootPath = '/' + pathname.split('/')[1];
  const selected = rootPath === '//' ? '/' : rootPath;

  /*
    Render the navigation bar with menu items and highlight the selected item based on the current URL.

    mode: This property sets the menu to horizontal mode for a top navigation bar.
    theme: This property sets the theme of the menu to light.
    items: This property provides the menu items defined earlier.
    selectedKeys: This property highlights the currently selected menu item based on the URL.
    style: This property customizes the menu's appearance to remove the bottom border and make it flush with the header.
  */
  return (
    <Menu
      mode="horizontal"
      theme="light"
      items={items}
      selectedKeys={[selected]}
      style={{ borderBottom: 'none', background: 'transparent' }}
    />
  );
}
