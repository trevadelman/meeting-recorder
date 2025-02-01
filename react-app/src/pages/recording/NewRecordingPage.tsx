import { useEffect, useRef, useState } from 'react';
import { Card, Button, Select, Input, Space, Alert, notification } from 'antd';
import { AudioOutlined, LoadingOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import { useQuery } from '@tanstack/react-query';

import { api, AudioDevice } from '@/api/client';
import { useAudio } from '@/hooks/useAudio';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

const AudioVisualizer = styled.canvas`
  width: 100%;
  height: 100px;
  background: ${({ theme }) => theme.token?.colorBgContainer || '#f0f2f5'};
  border-radius: 4px;
  margin: 16px 0;
`;

const RecordingStatus = styled.div<{ $isRecording: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: ${({ $isRecording }) => ($isRecording ? '#ff4d4f' : '#52c41a')};
  color: white;
  border-radius: 4px;
  font-weight: 500;

  &::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: white;
    animation: ${({ $isRecording }) =>
      $isRecording ? 'pulse 1.5s ease-in-out infinite' : 'none'};
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.5);
      opacity: 0.5;
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  }
`;

export function NewRecordingPage() {
  const {
    devices,
    selectedDevice,
    isRecording,
    duration,
    visualizerData,
    updateVisualizerData,
    startRecording,
    stopRecording,
    uploadRecording,
    selectDevice,
  } = useAudio();

  const [title, setTitle] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();

  // Fetch available devices
  const { data: audioDevices = [], isLoading: isLoadingDevices } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await api.devices.list();
      return response.data;
    },
  });

  // Draw audio visualization
  const drawVisualization = () => {
    if (!canvasRef.current || !visualizerData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get new data
    const dataArray = updateVisualizerData();
    if (!dataArray) return;

    // Draw waveform
    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = isRecording ? '#ff4d4f' : '#52c41a';

    const sliceWidth = (canvas.width * 1.0) / dataArray.length;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();

    // Request next frame
    animationFrameRef.current = requestAnimationFrame(drawVisualization);
  };

  // Handle recording start/stop
  const handleToggleRecording = async () => {
    if (isRecording) {
      setIsProcessing(true);
      try {
        const blob = await stopRecording();
        if (blob) {
          await uploadRecording(blob, title);
          notification.success({
            message: 'Recording completed',
            description: 'Your recording has been saved successfully.',
          });
          setTitle('');
        }
      } catch (error) {
        notification.error({
          message: 'Recording error',
          description: 'Failed to save recording. Please try again.',
        });
      } finally {
        setIsProcessing(false);
      }
    } else {
      try {
        await startRecording(title);
      } catch (error) {
        notification.error({
          message: 'Recording error',
          description: 'Failed to start recording. Please check your microphone permissions.',
        });
      }
    }
  };

  // Format duration display
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Start/stop visualization
  useEffect(() => {
    if (isRecording) {
      drawVisualization();
    }
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRecording]);

  if (isLoadingDevices) {
    return <LoadingSpinner />;
  }

  return (
    <Card title="New Recording">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {!selectedDevice && (
          <Alert
            message="No audio device selected"
            description="Please select an audio input device to start recording."
            type="warning"
            showIcon
          />
        )}

        <Space direction="vertical" style={{ width: '100%' }}>
          <label>Audio Device</label>
          <Select
            style={{ width: '100%' }}
            value={selectedDevice?.id}
            onChange={(value) => {
              const device = audioDevices.find((d) => d.id === value);
              if (device) selectDevice(device);
            }}
            options={audioDevices.map((device) => ({
              label: device.name,
              value: device.id,
            }))}
          />
        </Space>

        <Space direction="vertical" style={{ width: '100%' }}>
          <label>Meeting Title (optional)</label>
          <Input
            placeholder="Enter meeting title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isRecording}
          />
        </Space>

        <AudioVisualizer ref={canvasRef} />

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <RecordingStatus $isRecording={isRecording}>
            {isRecording ? 'Recording' : 'Ready'}
            {isRecording && `: ${formatDuration(duration)}`}
          </RecordingStatus>

          <Button
            type="primary"
            danger={isRecording}
            icon={isProcessing ? <LoadingOutlined /> : <AudioOutlined />}
            onClick={handleToggleRecording}
            disabled={!selectedDevice || isProcessing}
            loading={isProcessing}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </Button>
        </Space>
      </Space>
    </Card>
  );
}
