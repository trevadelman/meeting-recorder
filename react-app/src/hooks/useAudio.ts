import { useCallback, useEffect, useRef, useState } from 'react';

import { notification } from 'antd';

import { api, AudioDevice } from '@/api/client';
import { useApp, appActions } from '@/contexts/AppContext';

interface AudioVisualizerData {
  dataArray: Uint8Array;
  bufferLength: number;
}

export function useAudio() {
  const { state, dispatch } = useApp();
  const { selectedDevice } = state.audioDevice;

  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [visualizerData, setVisualizerData] = useState<AudioVisualizerData | null>(null);

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const startTime = useRef<number>(0);
  const durationInterval = useRef<number>();
  const chunks = useRef<Blob[]>([]);

  // Load available devices
  const loadDevices = useCallback(async () => {
    try {
      dispatch(appActions.setAudioLoading(true));
      const response = await api.devices.list();
      const devices = response.data.data;
      
      dispatch(appActions.setAudioDevices(devices));
      
      // Select default device if none selected
      if (!selectedDevice && devices.length > 0) {
        const defaultDevice = devices.find(d => d.default) || devices[0];
        dispatch(appActions.setSelectedDevice(defaultDevice));
      }
    } catch (error) {
      dispatch(appActions.setAudioError('Failed to load audio devices'));
    } finally {
      dispatch(appActions.setAudioLoading(false));
    }
  }, [dispatch, selectedDevice]);

  // Initialize audio context and analyzer
  const initializeAudio = useCallback(async () => {
    if (!selectedDevice) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: selectedDevice.id }
      });

      audioContext.current = new AudioContext();
      analyser.current = audioContext.current.createAnalyser();
      
      const source = audioContext.current.createMediaStreamSource(stream);
      source.connect(analyser.current);
      
      // Configure analyzer
      analyser.current.fftSize = 2048;
      const bufferLength = analyser.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      setVisualizerData({ dataArray, bufferLength });

      // Set up MediaRecorder
      mediaRecorder.current = new MediaRecorder(stream);
      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.current.push(e.data);
        }
      };

      return stream;
    } catch (error) {
      notification.error({
        message: 'Audio Error',
        description: 'Failed to initialize audio recording. Please check your microphone permissions.',
      });
      throw error;
    }
  }, [selectedDevice]);

  // Start recording
  const startRecording = useCallback(async (title?: string) => {
    if (!selectedDevice) {
      notification.error({
        message: 'Error',
        description: 'Please select an audio device first',
      });
      return;
    }

    try {
      await initializeAudio();
      
      if (mediaRecorder.current) {
        chunks.current = [];
        mediaRecorder.current.start();
        setIsRecording(true);
        startTime.current = Date.now();
        
        // Update duration
        durationInterval.current = window.setInterval(() => {
          const elapsed = (Date.now() - startTime.current) / 1000;
          setDuration(elapsed);
        }, 100);

        // Start server-side recording
        await api.recording.start(title);
      }
    } catch (error) {
      notification.error({
        message: 'Recording Error',
        description: 'Failed to start recording',
      });
    }
  }, [selectedDevice, initializeAudio]);

  // Stop recording
  const stopRecording = useCallback(async () => {
    if (!mediaRecorder.current || !isRecording) return;

    try {
      return new Promise<Blob>((resolve, reject) => {
        if (!mediaRecorder.current) {
          reject(new Error('No active recording'));
          return;
        }

        mediaRecorder.current.onstop = async () => {
          try {
            // Stop server-side recording
            await api.recording.stop();
            
            // Create final blob
            const blob = new Blob(chunks.current, { type: 'audio/wav' });
            resolve(blob);
            
            // Reset state
            setIsRecording(false);
            setDuration(0);
            chunks.current = [];
            
            if (durationInterval.current) {
              clearInterval(durationInterval.current);
            }
          } catch (error) {
            reject(error);
          }
        };

        mediaRecorder.current.stop();
      });
    } catch (error) {
      notification.error({
        message: 'Recording Error',
        description: 'Failed to stop recording',
      });
      throw error;
    }
  }, [isRecording]);

  // Upload recording
  const uploadRecording = useCallback(async (blob: Blob, title?: string) => {
    try {
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');
      if (title) formData.append('title', title);
      formData.append('duration', String(duration));

      await api.recording.upload(formData);
      
      notification.success({
        message: 'Success',
        description: 'Recording uploaded successfully',
      });
    } catch (error) {
      notification.error({
        message: 'Upload Error',
        description: 'Failed to upload recording',
      });
      throw error;
    }
  }, [duration]);

  // Update visualizer data
  const updateVisualizerData = useCallback(() => {
    if (!analyser.current || !visualizerData) return;
    
    analyser.current.getByteTimeDomainData(visualizerData.dataArray);
    return visualizerData.dataArray;
  }, [visualizerData]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
      if (audioContext.current) {
        audioContext.current.close();
      }
    };
  }, []);

  // Load devices on mount
  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  return {
    devices: state.audioDevice.devices,
    selectedDevice,
    isRecording,
    duration,
    visualizerData,
    updateVisualizerData,
    startRecording,
    stopRecording,
    uploadRecording,
    selectDevice: async (device: AudioDevice) => {
      try {
        await api.devices.select(device.id);
        dispatch(appActions.setSelectedDevice(device));
      } catch (error) {
        notification.error({
          message: 'Device Error',
          description: 'Failed to select audio device',
        });
      }
    },
  };
}
