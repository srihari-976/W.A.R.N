# W.A.R.N

This is a modern, cyberpunk-themed endpoint security monitoring system built for BrinHack 2025. It provides real-time monitoring of endpoint security metrics, alerts, and events with a beautiful neon-styled interface.

## Features

- Real-time security alerts and events monitoring
- Interactive metrics visualization with neon-themed graphs
- Process and network monitoring capabilities (coming soon)
- Risk scoring and threat level assessment
- Cyberpunk-inspired UI design

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/W.A.R.N.git
cd W.A.R.N
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The application will be available at `http://localhost:3000`

## API Endpoints

The system expects the following backend API endpoints:

- `/api/alerts/` - Get security alerts
- `/api/events/` - Get system events
- `/api/risk/scores` - Get risk assessment scores
- `/api/risk/factors` - Get risk factors
- `/api/processes/` - Get process information (planned)
- `/api/network/connections` - Get network connections (planned)

## Contributing

This project was created for BrinHack 2025. Feel free to fork and modify it for your use.
