import React, { createContext, useContext, useReducer, ReactNode } from 'react';

import { AudioDevice, RecordingStatus } from '@/api/client';

// Types
interface AppState {
  audioDevice: {
    devices: AudioDevice[];
    selectedDevice: AudioDevice | null;
    loading: boolean;
    error: string | null;
  };
  recording: {
    status: RecordingStatus['status'];
    progress?: string;
    duration: number;
    meetingId?: string;
  };
  ui: {
    sidebarCollapsed: boolean;
    darkMode: boolean;
  };
}

type Action =
  | { type: 'SET_AUDIO_DEVICES'; payload: AudioDevice[] }
  | { type: 'SET_SELECTED_DEVICE'; payload: AudioDevice }
  | { type: 'SET_AUDIO_LOADING'; payload: boolean }
  | { type: 'SET_AUDIO_ERROR'; payload: string | null }
  | { type: 'SET_RECORDING_STATUS'; payload: Partial<AppState['recording']> }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'TOGGLE_DARK_MODE' };

// Initial state
const initialState: AppState = {
  audioDevice: {
    devices: [],
    selectedDevice: null,
    loading: false,
    error: null,
  },
  recording: {
    status: 'idle',
    duration: 0,
  },
  ui: {
    sidebarCollapsed: false,
    darkMode: import.meta.env.VITE_ENABLE_DARK_MODE === 'true',
  },
};

// Reducer
function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_AUDIO_DEVICES':
      return {
        ...state,
        audioDevice: {
          ...state.audioDevice,
          devices: action.payload,
        },
      };
    case 'SET_SELECTED_DEVICE':
      return {
        ...state,
        audioDevice: {
          ...state.audioDevice,
          selectedDevice: action.payload,
        },
      };
    case 'SET_AUDIO_LOADING':
      return {
        ...state,
        audioDevice: {
          ...state.audioDevice,
          loading: action.payload,
        },
      };
    case 'SET_AUDIO_ERROR':
      return {
        ...state,
        audioDevice: {
          ...state.audioDevice,
          error: action.payload,
        },
      };
    case 'SET_RECORDING_STATUS':
      return {
        ...state,
        recording: {
          ...state.recording,
          ...action.payload,
        },
      };
    case 'TOGGLE_SIDEBAR':
      return {
        ...state,
        ui: {
          ...state.ui,
          sidebarCollapsed: !state.ui.sidebarCollapsed,
        },
      };
    case 'TOGGLE_DARK_MODE':
      return {
        ...state,
        ui: {
          ...state.ui,
          darkMode: !state.ui.darkMode,
        },
      };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the context
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

// Action creators
export const appActions = {
  setAudioDevices: (devices: AudioDevice[]) => ({
    type: 'SET_AUDIO_DEVICES' as const,
    payload: devices,
  }),
  setSelectedDevice: (device: AudioDevice) => ({
    type: 'SET_SELECTED_DEVICE' as const,
    payload: device,
  }),
  setAudioLoading: (loading: boolean) => ({
    type: 'SET_AUDIO_LOADING' as const,
    payload: loading,
  }),
  setAudioError: (error: string | null) => ({
    type: 'SET_AUDIO_ERROR' as const,
    payload: error,
  }),
  setRecordingStatus: (status: Partial<AppState['recording']>) => ({
    type: 'SET_RECORDING_STATUS' as const,
    payload: status,
  }),
  toggleSidebar: () => ({
    type: 'TOGGLE_SIDEBAR' as const,
  }),
  toggleDarkMode: () => ({
    type: 'TOGGLE_DARK_MODE' as const,
  }),
};
