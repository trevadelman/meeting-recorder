# Meeting Recorder React App

A modern React application for recording, transcribing, and managing meeting recordings. Built with TypeScript, Vite, and Ant Design.

## Features

- 🎙️ **Audio Recording**: Record meetings with real-time audio visualization
- 📝 **Transcription**: Automatic speech-to-text transcription with speaker diarization
- 📊 **Dashboard**: View meeting statistics and recent recordings
- 🔍 **Meeting Management**: Search, filter, and organize your meetings
- 🎨 **Modern UI**: Responsive design with dark mode support
- 🔄 **Real-time Updates**: Live updates using React Query
- 📱 **Mobile-friendly**: Responsive layout that works on all devices

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Ant Design
- **State Management**: React Query + Context
- **Styling**: Styled Components
- **API Client**: Axios
- **Audio Processing**: Web Audio API
- **Routing**: React Router v6

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- FastAPI backend server running

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/meeting-recorder.git
cd meeting-recorder/react-app
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
├── api/          # API client and types
├── components/   # Reusable components
│   ├── common/   # Shared components
│   └── pages/    # Page-specific components
├── contexts/     # React contexts
├── hooks/        # Custom hooks
├── pages/        # Page components
├── styles/       # Global styles
└── utils/        # Utility functions
```

## Key Components

### Audio System

The audio recording system uses the Web Audio API for capturing and visualizing audio:

```typescript
interface AudioConfig {
  sampleRate: number;
  channels: number;
  format: 'audio/webm' | 'audio/wav';
}
```

### Meeting Management

Meetings are managed through a comprehensive API:

```typescript
interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: number;
  tags: string[];
  transcript?: TranscriptSegment[];
}
```

### User Interface

The UI is built with Ant Design and includes:

- Responsive sidebar navigation
- Dark mode support
- Custom audio visualization
- Interactive meeting list
- Real-time recording interface

## Development

### Code Style

- Follow TypeScript best practices
- Use functional components with hooks
- Implement proper error handling
- Write meaningful comments
- Use consistent naming conventions

### Testing

Run tests with:
```bash
npm test
```

### Linting

Check code style with:
```bash
npm run lint
```

Fix code style issues with:
```bash
npm run lint:fix
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
