# Multi-API Chat - Operations Summary

## Overview
Multi-API Chat is a GENAI Network Operations platform that provides a unified interface for interacting with multiple AI providers while managing Cisco router configurations and network operations.

## Quick Start

### Prerequisites
- Ubuntu system with ability to add PPAs
- Network ports 7001 and 7002 available
- Internet connectivity for AI provider APIs

### Installation & Setup
```bash
# 1. Clone the repository
git clone https://github.com/zumanm1/multi-api-chat.git
cd multi-api-chat

# 2. Install Python 3.11 (if not present)
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y
sudo apt-get install -y python3.11 python3.11-venv

# 3. Create virtual environment
python3.11 -m venv venv

# 4. Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Make scripts executable
chmod +x start_app.sh stop_app.sh

# 6. Configure environment
cp .env.template .env
# Edit .env with your API keys and settings
```

### Starting the Application
```bash
# Start both backend and frontend servers
./start_app.sh

# Or use individual commands:
# Backend only: python3.11 backend_server.py
# Frontend only: python3.11 -m http.server 7001
```

### Stopping the Application
```bash
# Stop all services
./stop_app.sh
```

## Architecture

### Components
- **Backend Server**: Flask API server (Port 7002)
- **Frontend Server**: Static HTTP server (Port 7001)
- **Virtual Environment**: Python 3.11 isolated environment

### File Structure
```
multi-api-chat/
├── venv/                    # Python 3.11 virtual environment
├── logs/                    # Application logs
├── data/                    # Database and data files
├── .env                     # Environment variables
├── config.json             # Provider configurations
├── usage.json              # Usage statistics
├── backend_server.py       # Main Flask API server
├── requirements.txt        # Python dependencies
├── start_app.sh           # Startup script
├── stop_app.sh            # Shutdown script
├── index.html             # Chat interface
├── settings.html          # Configuration interface
├── dashboard.html         # Operations dashboard
├── operations.html        # Network operations console
├── automation.html        # Automation workflows
└── devices.html           # Device management
```

## Configuration

### Environment Variables (.env)
```bash
# AI Provider API Keys
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_anthropic_key
CEREBRAS_API_KEY=your_cerebras_key
SAMBANOVA_API_KEY=your_sambanova_key
OPENROUTER_API_KEY=your_openrouter_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=7002

# Application Settings
DEFAULT_PROVIDER=openai
TEMPERATURE=0.7
MAX_TOKENS=1000
USE_TELNET=true

# Database
DATABASE_URL=sqlite:///./data/app.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Provider Configuration (config.json)
```json
{
  "openai": {
    "name": "OpenAI",
    "enabled": true,
    "api_key": "",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1"
  },
  "groq": {
    "name": "Groq",
    "enabled": true,
    "api_key": "",
    "model": "llama-3.1-70b-versatile",
    "base_url": "https://api.groq.com/openai/v1"
  }
}
```

## Network Ports & URLs

### Application Access
- **Frontend Interface**: http://localhost:7001
- **Backend API**: http://localhost:7002
- **Settings Page**: http://localhost:7001/settings.html
- **Dashboard**: http://localhost:7001/dashboard.html
- **Operations Console**: http://localhost:7001/operations.html

### API Endpoints
```
GET  /api/providers         # List providers
GET  /api/settings          # Get settings
POST /api/chat              # Single provider chat
POST /api/chat/compare      # Multi-provider comparison
POST /api/providers/test    # Test provider connections
GET  /api/usage             # Usage statistics
```

## Dependencies

### System Requirements
- Ubuntu 20.04+ (or compatible Linux)
- Python 3.11 with venv support
- pip 25.2+ (auto-upgraded in venv)

### Key Python Packages
```
Flask==3.1.1
flask-cors==6.0.1
openai==1.99.5
python-dotenv==1.1.1
paramiko==4.0.0
pydantic==2.11.7
httpx==0.28.1
typing-extensions==4.14.1
```

## Operational Procedures

### Daily Operations
1. **Health Check**: Verify services are running on ports 7001/7002
2. **Log Review**: Check `logs/start_app.log` for errors
3. **Provider Status**: Test AI provider connections via Settings page
4. **Usage Monitoring**: Review usage statistics on Dashboard

### Troubleshooting

#### Common Issues

**Service Won't Start**
```bash
# Check port availability
netstat -tlnp | grep :800[12]

# Check Python environment
source venv/bin/activate
python --version  # Should show 3.11.x

# Check logs
tail -f logs/start_app.log
```

**Provider Connection Failures**
- Verify API keys in `.env` or Settings page
- Test network connectivity to provider endpoints
- Check provider-specific rate limits and quotas

**Port Already in Use**
```bash
# Find process using port
sudo lsof -i :7001
sudo lsof -i :7002

# Kill process if needed
sudo kill -9 <PID>
```

#### Log Files
- **Start Log**: `logs/start_app.log` - Service startup and general operations
- **Backend Log**: `logs/backend.log` - API server detailed logs
- **Frontend Log**: `logs/frontend.log` - Static server logs

### Maintenance

#### Virtual Environment Management
```bash
# Activate environment
source venv/bin/activate

# Update packages
pip install --upgrade -r requirements.txt

# View installed packages
pip list --format=freeze
```

#### Configuration Updates
1. Update `.env` for environment variables
2. Use Settings page for provider configurations
3. Restart services after configuration changes

#### Data Management
- **Usage Data**: `usage.json` - Automatically updated
- **Configuration**: `config.json` - Provider settings
- **Database**: `data/app.db` - Application data (SQLite)

## Security Considerations

### API Key Management
- Store keys in `.env` file (excluded from git)
- Use Settings page for secure key entry
- Rotate keys regularly
- Monitor usage for unauthorized access

### Network Security
- Application runs on localhost by default
- For production deployment, configure proper firewall rules
- Use HTTPS in production environments
- Implement authentication for multi-user environments

## Performance Tuning

### Resource Monitoring
```bash
# Monitor CPU/Memory usage
htop

# Check disk usage
df -h

# Monitor network connections
ss -tulnp | grep :800[12]
```

### Optimization Tips
- Adjust `MAX_TOKENS` based on use case
- Configure provider fallbacks for reliability
- Monitor usage statistics for cost optimization
- Use appropriate temperature settings for consistency

## Backup & Recovery

### Configuration Backup
```bash
# Backup configuration files
tar -czf backup-$(date +%Y%m%d).tar.gz .env config.json usage.json data/
```

### Recovery Procedure
1. Restore configuration files
2. Recreate virtual environment if needed
3. Install dependencies
4. Restart services

## Development Environment

### Version Information
- **Python**: 3.11.13 (via deadsnakes PPA)
- **Virtual Environment**: `venv` at project root
- **Package Manager**: pip 25.2
- **Web Framework**: Flask 3.1.1

### Development Workflow
1. Activate virtual environment: `source venv/bin/activate`
2. Make code changes
3. Test locally
4. Update requirements.txt if adding dependencies
5. Restart services to apply changes

## Support & Documentation

### Additional Resources
- Backend API documentation: Available at runtime
- Provider-specific documentation: Check individual AI service docs
- Network operations: Cisco IOS command references

### Getting Help
- Check logs for error details
- Verify configuration settings
- Test network connectivity
- Review provider status and quotas

---

**Last Updated**: 2025-08-08  
**Environment**: Ubuntu Linux with Python 3.11  
**Status**: Active Development  
**Maintainer**: Local Development Team
