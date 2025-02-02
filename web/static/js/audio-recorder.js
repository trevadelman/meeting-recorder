class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
    }

    async getDevices() {
        try {
            // Ensure mediaDevices is available
            if (navigator.mediaDevices === undefined) {
                navigator.mediaDevices = {};
            }

            // Ensure getUserMedia is available
            if (navigator.mediaDevices.getUserMedia === undefined) {
                navigator.mediaDevices.getUserMedia = function(constraints) {
                    const getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
                    if (!getUserMedia) {
                        throw new Error('getUserMedia is not implemented in this browser');
                    }
                    return new Promise((resolve, reject) => {
                        getUserMedia.call(navigator, constraints, resolve, reject);
                    });
                }
            }

            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // Release the stream immediately after device enumeration
            stream.getTracks().forEach(track => track.stop());
            
            // Get devices list
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'audioinput').map(device => ({
                id: device.deviceId,
                name: device.label,
                default: device.deviceId === 'default'
            }));
        } catch (error) {
            console.error('Error listing audio devices:', error);
            throw new Error('Unable to access audio devices');
        }
    }

    async startRecording(deviceId) {
        try {
            // Ensure mediaDevices is available
            if (navigator.mediaDevices === undefined) {
                navigator.mediaDevices = {};
            }

            // Ensure getUserMedia is available
            if (navigator.mediaDevices.getUserMedia === undefined) {
                navigator.mediaDevices.getUserMedia = function(constraints) {
                    const getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
                    if (!getUserMedia) {
                        throw new Error('getUserMedia is not implemented in this browser');
                    }
                    return new Promise((resolve, reject) => {
                        getUserMedia.call(navigator, constraints, resolve, reject);
                    });
                }
            }

            this.audioChunks = [];
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    deviceId: deviceId ? { exact: deviceId } : undefined
                }
            });

            if (!window.MediaRecorder) {
                throw new Error('MediaRecorder is not supported in this browser');
            }

            // Get supported MIME type
            const mimeType = this.getSupportedMimeType();
            if (!mimeType) {
                throw new Error('No supported audio MIME type found');
            }

            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType
            });

            // Ensure we collect data frequently for better real-time handling
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            // Start recording and request data every 1 second
            this.mediaRecorder.start(1000);
            
            // Send start recording request to server
            const response = await fetch('/start_recording', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    title: document.querySelector('input[name="title"]').value
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start server-side recording');
            }
            
            return true;
        } catch (error) {
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            throw new Error(`Failed to start recording: ${error.message}`);
        }
    }

    async stopRecording() {
        return new Promise((resolve, reject) => {
            this.mediaRecorder.onstop = async () => {
                try {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                    this.stream.getTracks().forEach(track => track.stop());

                    // Convert to WAV format
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const fileReader = new FileReader();

                    fileReader.onload = async (e) => {
                        try {
                            const arrayBuffer = e.target.result;
                            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                            const wavBlob = await this.audioBufferToWav(audioBuffer);
                            resolve(wavBlob);
                        } catch (error) {
                            reject(error);
                        }
                    };

                    fileReader.readAsArrayBuffer(audioBlob);
                } catch (error) {
                    reject(error);
                }
            };

            this.mediaRecorder.stop();
        });
    }

    audioBufferToWav(buffer) {
        const numChannels = buffer.numberOfChannels;
        const sampleRate = buffer.sampleRate;
        const format = 1; // PCM
        const bitDepth = 16;
        
        const bytesPerSample = bitDepth / 8;
        const blockAlign = numChannels * bytesPerSample;
        
        const dataLength = buffer.length * blockAlign;
        const bufferLength = 44 + dataLength;
        
        const arrayBuffer = new ArrayBuffer(bufferLength);
        const view = new DataView(arrayBuffer);
        
        // WAV header
        const writeString = (view, offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + dataLength, true);
        writeString(view, 8, 'WAVE');
        writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, format, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * blockAlign, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitDepth, true);
        writeString(view, 36, 'data');
        view.setUint32(40, dataLength, true);
        
        // Write audio data
        const offset = 44;
        const channelData = [];
        for (let i = 0; i < numChannels; i++) {
            channelData[i] = buffer.getChannelData(i);
        }
        
        let pos = 44;
        for (let i = 0; i < buffer.length; i++) {
            for (let channel = 0; channel < numChannels; channel++) {
                const sample = channelData[channel][i];
                const value = Math.max(-1, Math.min(1, sample));
                view.setInt16(pos, value < 0 ? value * 0x8000 : value * 0x7FFF, true);
                pos += 2;
            }
        }
        
        return new Blob([arrayBuffer], { type: 'audio/wav' });
    }

    async uploadRecording(blob, title, duration, email) {
        const formData = new FormData();
        formData.append('audio', blob, 'recording.wav');
        formData.append('title', title || '');
        formData.append('duration', duration);
        formData.append('email', email || '');

        // Add tags and notes
        const tags = $('#recordingTags').val() || [];
        formData.append('tags', JSON.stringify(tags));
        
        const notes = $('#recordingNotes').val() || '';
        formData.append('notes', notes);

        try {
            // First stop server-side recording
            document.getElementById('processingStatus').textContent = 'Stopping server recording...';
            const stopResponse = await fetch('/stop_recording', {
                method: 'POST'
            });

            if (!stopResponse.ok) {
                const errorData = await stopResponse.json();
                throw new Error(errorData.error || 'Failed to stop server-side recording');
            }

            // Update status and upload
            document.getElementById('processingStatus').textContent = 'Uploading audio...';
            const uploadResponse = await fetch('/upload_recording', {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json();
                throw new Error(errorData.error || 'Failed to upload recording');
            }

            document.getElementById('processingStatus').textContent = 'Processing complete!';
            return await uploadResponse.json();
        } catch (error) {
            console.error('Error uploading recording:', error);
            throw error;
        }
    }

    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return null;
    }
}

// Export for use in other files
window.AudioRecorder = AudioRecorder;
