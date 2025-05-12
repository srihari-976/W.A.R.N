# W.A.R.N Frontend

A modern, cyberpunk-themed security dashboard for endpoint protection and monitoring.

## Features

- Real-time system monitoring
- Endpoint management
- Threat detection and response
- Process control
- Network security
- File system protection
- Policy management
- Response automation
- Reports and analytics

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- Chart.js
- React Router
- Axios

## Prerequisites

- Node.js 16.x or higher
- npm 7.x or higher

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/W.A.R.N-frontend.git
cd W.A.R.N-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory:
```bash
REACT_APP_API_URL=http://localhost:5000
```

4. Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`.

## Project Structure

```
src/
├── components/
│   ├── common/          # Shared components
│   ├── dashboard/       # Dashboard components
│   ├── endpoints/       # Endpoint management
│   ├── threats/         # Threat management
│   ├── processes/       # Process control
│   ├── network/         # Network security
│   ├── filesystem/      # File system protection
│   ├── policies/        # Policy management
│   ├── automation/      # Response automation
│   └── reports/         # Analytics and reporting
├── context/            # React context providers
├── hooks/             # Custom React hooks
├── services/          # API services
├── types/             # TypeScript type definitions
└── utils/             # Utility functions
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App

## API Integration

The frontend connects to a backend API running on `http://localhost:5000`. The following endpoints are used:

- `/api/endpoints` - Endpoint management
- `/api/threats` - Threat detection
- `/api/processes` - Process control
- `/api/network` - Network monitoring
- `/api/filesystem` - File system operations
- `/api/policies` - Policy management
- `/api/automation` - Response automation
- `/api/reports` - Analytics data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
