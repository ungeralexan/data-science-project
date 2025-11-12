// components/NavBar.tsx
import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  UserOutlined,
  CalendarOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const items: MenuProps['items'] = [
  { key: '/',        icon: <UserOutlined />,    label: <Link to="/">Profile</Link> },
  { key: '/events',  icon: <CalendarOutlined />,label: <Link to="/events">Events</Link> },
  { key: '/settings',icon: <SettingOutlined />, label: <Link to="/settings">Settings</Link> },
];

export default function NavBar() {
  const { pathname } = useLocation();
  const rootPath = '/' + pathname.split('/')[1];
  const selected = rootPath === '//' ? '/' : rootPath;

  return (
    <Menu
      mode="horizontal"
      theme="light"
      items={items}
      selectedKeys={[selected]}
      // keep it flush with the header & remove bottom border
      style={{ borderBottom: 'none', background: 'transparent' }}
    />
  );
}
