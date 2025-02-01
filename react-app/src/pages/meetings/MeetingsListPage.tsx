import { useState } from 'react';
import { Card, Table, Tag, Space, Button, Input, Dropdown, Modal } from 'antd';
import { MoreOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { api, Meeting } from '@/api/client';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

const { confirm } = Modal;

export function MeetingsListPage() {
  const [searchText, setSearchText] = useState('');
  const queryClient = useQueryClient();

  // Fetch meetings
  const { data: meetings = [], isLoading } = useQuery({
    queryKey: ['meetings', searchText],
    queryFn: async () => {
      const response = await api.meetings.list({
        title_search: searchText || undefined,
      });
      return response.data;
    },
  });

  // Delete meeting mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.meetings.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
  });

  // Handle meeting deletion
  const handleDelete = (id: string) => {
    confirm({
      title: 'Are you sure you want to delete this meeting?',
      content: 'This action cannot be undone.',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        deleteMutation.mutate(id);
      },
    });
  };

  // Format duration display
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Table columns
  const columns: ColumnsType<Meeting> = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => text || `Meeting ${record.id.slice(0, 8)}`,
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      render: (date) => new Date(date).toLocaleString(),
      sorter: (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration) => formatDuration(duration),
      sorter: (a, b) => a.duration - b.duration,
    },
    {
      title: 'Tags',
      key: 'tags',
      dataIndex: 'tags',
      render: (tags: string[]) => (
        <>
          {tags?.map((tag) => (
            <Tag key={tag}>{tag}</Tag>
          ))}
        </>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'export',
                label: 'Export',
                onClick: () => window.open(`/api/meetings/${record.id}/export`),
              },
              {
                key: 'delete',
                label: 'Delete',
                danger: true,
                onClick: () => handleDelete(record.id),
              },
            ],
          }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ];

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Card title="All Meetings">
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Space>
          <Input
            placeholder="Search meetings..."
            allowClear
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
        </Space>

        <Table
          columns={columns}
          dataSource={meetings}
          rowKey="id"
          pagination={{
            defaultPageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} meetings`,
          }}
        />
      </Space>
    </Card>
  );
}
