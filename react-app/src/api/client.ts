import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

import { notification } from 'antd';

// Types
export interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: number;
  audio_path: string;
  transcript?: TranscriptSegment[];
  summary?: string;
  tags?: string[];
}

export interface TranscriptSegment {
  speaker: string;
  text: string;
  startTime: number;
  endTime: number;
}

export interface AudioDevice {
  id: string;
  name: string;
  default: boolean;
}

export interface RecordingStatus {
  status: 'idle' | 'recording' | 'processing';
  progress?: string;
  meeting_id?: string;
}

// Create Axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Check if the response has a data property that contains the actual data
    if (response.data && typeof response.data === 'object') {
      // If the response has a data property that contains the actual data, return just that
      return {
        ...response,
        data: response.data.data || response.data,
      };
    }
    return response;
  },
  (error: AxiosError<ApiError>) => {
    const errorMessage = error.response?.data?.message || error.message;
    notification.error({
      message: 'Error',
      description: errorMessage,
    });
    return Promise.reject(error);
  }
);

// API functions
export const api = {
  // Devices
  devices: {
    list: () => 
      apiClient.get<AudioDevice[]>('/devices'),
    select: (deviceId: string) =>
      apiClient.post<void>('/devices/select', { device_id: deviceId }),
  },

  // Meetings
  meetings: {
    list: (params?: { 
      tags?: string[],
      title_search?: string,
      transcript_search?: string 
    }) =>
      apiClient.get<Meeting[]>('/meetings', { params }),
    
    get: (id: string) =>
      apiClient.get<Meeting>(`/meetings/${id}`),
    
    delete: (id: string) =>
      apiClient.delete<void>(`/meetings/${id}`),
    
    export: (id: string, format: 'txt' | 'json' | 'md' = 'txt') =>
      apiClient.get<Blob>(`/meetings/${id}/export`, {
        params: { format },
        responseType: 'blob',
      }),
    
    getAudio: (id: string) =>
      apiClient.get<Blob>(`/meetings/${id}/audio`, {
        responseType: 'blob',
      }),
  },

  // Recording
  recording: {
    start: (title?: string) =>
      apiClient.post<void>('/meetings/start', { title }),
    
    stop: () =>
      apiClient.post<{ audio_path: string }>('/meetings/stop'),
    
    status: () =>
      apiClient.get<RecordingStatus>('/meetings/status'),
    
    upload: (data: FormData) =>
      apiClient.post<void>('/meetings/upload', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }),
  },

  // Tags
  tags: {
    list: () =>
      apiClient.get<string[]>('/tags'),
    
    add: (meetingId: string, tag: string) =>
      apiClient.post<void>(`/meetings/${meetingId}/tags`, { tag }),
    
    remove: (meetingId: string, tag: string) =>
      apiClient.delete<void>(`/meetings/${meetingId}/tags/${tag}`),
  },
};

export default api;
