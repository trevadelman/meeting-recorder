import { Card, Col, Row, Statistic } from 'antd';
import { AudioOutlined, ClockCircleOutlined, TeamOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';

import { api, Meeting } from '@/api/client';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export function DashboardPage() {
  // Fetch meetings for statistics
  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['meetings'],
    queryFn: async () => {
      const response = await api.meetings.list();
      return response.data;
    },
  });

  // Calculate statistics
  const totalMeetings = meetings.length;
  const totalMinutes = meetings.reduce((acc: number, meeting: Meeting) => {
    return acc + meeting.duration / 60;
  }, 0);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Total Meetings"
              value={totalMeetings}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Total Recording Time"
              value={Math.round(totalMinutes)}
              suffix="minutes"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Active Device"
              value="No device selected"
              prefix={<AudioOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
