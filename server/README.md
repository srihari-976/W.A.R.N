# Endpoint Agent

A comprehensive endpoint security agent that monitors, collects, and reports security-relevant information from Windows endpoints.

## Features

- **System Monitoring**
  - Process monitoring and protection
  - Network connection monitoring
  - File system monitoring
  - Registry monitoring
  - Service monitoring
  - User account monitoring

- **Data Collection**
  - System information
  - Process information
  - Network information
  - Installed software
  - Security events
  - User accounts
  - Services
  - File integrity

- **Security Features**
  - File integrity monitoring
  - Process protection
  - Network protection
  - Service protection
  - SSL/TLS communication
  - API key authentication
  - HMAC message signing

- **Communication**
  - Real-time event reporting
  - WebSocket-based command channel
  - Heartbeat mechanism
  - Automatic reconnection
  - Batch event processing
  - Compressed data transfer

## Requirements

- Windows 10 or later
- Python 3.8 or later
- Administrator privileges

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/endpoint-agent.git
cd endpoint-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the agent:
   - Copy `config/endpoint_agent.yaml.example` to `config/endpoint_agent.yaml`
   - Update the configuration with your settings
   - Set up SSL certificates in the `certs` directory

## Usage

1. Start the agent:
```bash
python -m backend.endpoint_agent.agent
```

2. The agent will:
   - Load configuration
   - Initialize components
   - Start monitoring
   - Connect to the server
   - Begin reporting events

3. Monitor the logs:
```bash
tail -f logs/endpoint_agent.log
```

## Configuration

The agent is configured through `config/endpoint_agent.yaml`. Key settings include:

- Agent identification
- Communication settings
- Data collection intervals
- Monitoring paths
- Security settings
- Performance tuning
- Error handling

See the configuration file for detailed options.

## Security

The agent implements several security measures:

- SSL/TLS for all communications
- API key authentication
- HMAC message signing
- File integrity monitoring
- Process protection
- Network protection
- Service protection

## Development

1. Set up development environment:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Run linting:
```bash
flake8 backend/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## Acknowledgments

- Windows Management Instrumentation (WMI)
- Python for Windows Extensions (pywin32)
- Watchdog file system monitoring
- psutil system monitoring 
