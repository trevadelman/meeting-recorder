import React, { useEffect, useState } from 'react';
import { Layout, Menu, theme, Button, Space, Tooltip } from 'antd';
import {
  AudioOutlined,
  DashboardOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  TeamOutlined,
  BulbOutlined,
  BulbFilled,
} from '@ant-design/icons';
import styled from 'styled-components';
import { useLocation, useNavigate } from 'react-router-dom';

import { useApp, appActions } from '@/contexts/AppContext';
import { routeToMenuItem } from '@/config/menuMapping';

const { Header, Sider, Content } = Layout;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
`;

const StyledSider = styled(Sider)`
  .ant-layout-sider-children {
    display: flex;
    flex-direction: column;
  }

  .logo {
    height: 64px;
    padding: 16px;
    color: white;
    font-size: 18px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    margin: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
`;

const StyledHeader = styled(Header)`
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
`;

const StyledContent = styled(Content)`
  margin: 24px;
  padding: 24px;
  background: white;
  border-radius: 4px;
  min-height: 280px;
`;

interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: 'meetings',
    icon: <TeamOutlined />,
    label: 'Meetings',
    children: [
      {
        key: 'meetings/all',
        icon: <TeamOutlined />,
        label: 'All Meetings',
      },
      {
        key: 'meetings/recent',
        icon: <TeamOutlined />,
        label: 'Recent',
      },
      {
        key: 'meetings/favorites',
        icon: <TeamOutlined />,
        label: 'Favorites',
      },
    ],
  },
  {
    key: 'recording',
    icon: <AudioOutlined />,
    label: 'Recording',
    children: [
      {
        key: 'recording/new',
        icon: <AudioOutlined />,
        label: 'New Recording',
      },
      {
        key: 'recording/devices',
        icon: <AudioOutlined />,
        label: 'Devices',
      },
    ],
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
];

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { state, dispatch } = useApp();
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const location = useLocation();
  const navigate = useNavigate();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Get current selected menu item from route
  const selectedKey = routeToMenuItem[location.pathname] || 'dashboard';

  // Handle menu item click
  const handleMenuClick = ({ key }: { key: string }) => {
    // Convert menu key to route path
    const path = `/${key.replace(/\//g, '/')}`;
    navigate(path);

    // Close sidebar on mobile after navigation
    if (isMobile) {
      dispatch(appActions.toggleSidebar());
    }
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    dispatch(appActions.toggleSidebar());
  };

  // Toggle dark mode
  const toggleDarkMode = () => {
    dispatch(appActions.toggleDarkMode());
  };

  return (
    <StyledLayout>
      <StyledSider
        trigger={null}
        collapsible
        collapsed={state.ui.sidebarCollapsed}
        breakpoint="lg"
        collapsedWidth={isMobile ? 0 : 80}
        onBreakpoint={(broken) => {
          if (broken) {
            dispatch(appActions.toggleSidebar());
          }
        }}
      >
        <div className="logo">
          {state.ui.sidebarCollapsed ? 'MR' : 'Meeting Recorder'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={['meetings', 'recording']}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </StyledSider>
      <Layout>
        <StyledHeader style={{ background: colorBgContainer }}>
          <Button
            type="text"
            icon={state.ui.sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={toggleSidebar}
          />
          <Space>
            <Tooltip title={state.ui.darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              <Button
                type="text"
                icon={state.ui.darkMode ? <BulbFilled /> : <BulbOutlined />}
                onClick={toggleDarkMode}
              />
            </Tooltip>
          </Space>
        </StyledHeader>
        <StyledContent>{children}</StyledContent>
      </Layout>
    </StyledLayout>
  );
}
