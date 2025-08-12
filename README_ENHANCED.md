# 🚀 Enhanced Multi-API Chat Application

A comprehensive chat interface that integrates multiple AI providers with advanced testing, secure API key management, and enterprise-grade features.

## ✨ New Enhanced Features

### 🔐 Secure API Key Management
- **`.env.private` Integration**: Automatic secure storage of API keys for enabled providers only
- **Environment File Management**: API endpoints for managing environment files
- **Real-time Synchronization**: Provider updates automatically sync with `.env.private`

### 🧪 Advanced Provider Testing
- **Enhanced Test Endpoints**: Raw input/output data display for comprehensive debugging
- **Multi-level Testing**: Connection tests + chat functionality validation  
- **Detailed Error Reporting**: Categorized error types with specific failure reasons
- **Test Result Analytics**: Success/failure metrics with response time tracking

### ⚙️ Provider Management
- **Full CRUD Operations**: Save, edit, remove, replace provider configurations
- **Dynamic Configuration**: Edit URLs, API keys, models, and settings on-the-fly
- **Status Monitoring**: Real-time connection status for all providers
- **Bulk Operations**: Manage multiple providers simultaneously

### 🔬 Comprehensive Testing Suite
- **Backend Tests**: pytest-based testing for all API functionality
- **Frontend Tests**: Enhanced Puppeteer integration tests
- **E2E Testing**: Complete frontend-backend integration validation
- **Test Reporting**: Detailed HTML and JSON reports with screenshots

## 🎯 Supported Providers

| Provider | Status | Features |
|----------|--------|----------|
| **Groq** | ✅ Enhanced | API key management, advanced testing |
| **Cerebras** | ✅ Enhanced | Full CRUD operations, error handling |  
| **OpenRouter** | ✅ Enhanced | Dynamic configuration, status monitoring |
| **Ollama** | ✅ Enhanced | Local service support, model management |
| **OpenAI** | ✅ Enhanced | Complete integration with testing |
| **Anthropic** | ✅ Enhanced | Claude models with advanced testing |

## 🛠 Installation & Setup

### Prerequisites
- **Python 3.11+** (recommended)
- **Node.js 18+** and npm
- **Git** for version control

### Quick Start

1. **Clone the Repository**
```bash
git clone <repository-url>
cd multi-api-chat
```

2. **Run Enhanced Setup**
```bash
# Make scripts executable
chmod +x *.sh

# Start the application (includes dependency installation)
./start_app.sh
```

3. **Run Comprehensive Tests**
```bash
# Run all enhanced tests (backend + frontend)
./run_enhanced_tests.sh

# Or run individual test suites
./run_integration_tests.sh  # Original integration tests
python -m pytest test_env_private_backend.py  # Backend tests
node enhanced_puppeteer_tests_fixed.js  # Enhanced frontend tests
```

## 📚 API Endpoints

### Enhanced Provider Management
```http
# Get all providers with status
GET /api/providers

# Update provider configuration (auto-saves to .env.private)
PUT /api/providers/{provider_id}

# Enhanced provider testing with raw data
POST /api/providers/{provider_id}/test
{
  "test_message": "Custom test message",
  "include_raw_data": true
}

# Test all enabled providers
POST /api/providers/test-all
```

### Environment File Management
```http
# Get .env.private file status
GET /api/env/private

# Refresh .env.private with current enabled providers
POST /api/env/private/refresh

# Clear .env.private file
POST /api/env/private/clear
```

### Health & Monitoring
```http
# Enhanced health check with environment status
GET /api/health
```

## 🔧 Configuration

### Environment Variables (`.env.private`)
The application automatically manages a `.env.private` file containing API keys for enabled providers:

```env
GROQ_API_KEY=your_groq_api_key_here
CEREBRAS_API_KEY=your_cerebras_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Only enabled providers with valid keys are stored
```

### Provider Configuration (`config.json`)
```json
{
  "providers": {
    "groq": {
      "name": "Groq",
      "enabled": true,
      "api_key": "",  // Loaded from .env.private
      "model": "llama-3.1-70b-versatile",
      "base_url": "https://api.groq.com/openai/v1",
      "status": "connected",
      "last_checked": "2025-08-10T09:15:00Z"
    }
  }
}
```

## 🧪 Testing

### Test Suites Available

1. **Enhanced Backend Tests** (`test_env_private_backend.py`)
   - `.env.private` file management
   - Enhanced provider testing with raw data
   - Provider configuration updates
   - Environment file synchronization

2. **Enhanced Frontend Tests** (`enhanced_puppeteer_tests_fixed.js`)
   - Backend health checks with environment status
   - Provider configuration UI testing
   - Raw data display validation
   - Error handling verification

3. **Integration Tests** (`final_integration_test.js`)
   - Complete frontend-backend integration
   - Cross-page navigation testing
   - Performance monitoring

### Running Tests

```bash
# Run all tests with detailed reporting
./run_enhanced_tests.sh

# Individual test suites
python -m pytest test_env_private_backend.py -v  # Backend only
node enhanced_puppeteer_tests_fixed.js          # Frontend only
```

### Test Reports
- **HTML Reports**: `enhanced_test_reports/enhanced_test_report.html`
- **JSON Data**: `enhanced_test_reports/enhanced_test_report.json`
- **Screenshots**: `enhanced_test_screenshots/` (for failed tests)

## 🌐 Frontend Pages

| Page | URL | Enhanced Features |
|------|-----|-------------------|
| **Chat Interface** | `/index.html` | Enhanced error handling, provider status |
| **Dashboard** | `/dashboard.html` | Usage analytics, provider metrics |
| **Operations** | `/operations.html` | Device management integration |
| **Settings** | `/settings.html` | Provider configuration, API key management |
| **Automation** | `/automation.html` | Workflow automation features |

## 🚀 Advanced Features

### Real-time Provider Testing
```javascript
// Enhanced test with raw data
const testResult = await fetch('/api/providers/groq/test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    test_message: 'Test provider functionality',
    include_raw_data: true
  })
});

const result = await testResult.json();
console.log('Raw request:', result.raw_data.request);
console.log('Raw response:', result.raw_data.response);
```

### Dynamic Provider Management
```javascript
// Update provider configuration
await fetch('/api/providers/cerebras', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    enabled: true,
    api_key: 'new-api-key',
    model: 'llama-4-scout-wse-3',
    base_url: 'https://api.cerebras.ai/v1'
  })
});
// Automatically updates .env.private file
```

## 📊 Monitoring & Analytics

### Provider Status Monitoring
- Real-time connection status
- Response time tracking
- Error rate analytics
- Usage statistics

### Test Result Analytics
- Success/failure rates
- Performance metrics
- Error categorization
- Historical data tracking

## 🔒 Security Features

- **Secure API Key Storage**: Keys stored in `.env.private`, excluded from version control
- **Environment Isolation**: Separate environments for different deployment stages
- **Error Sanitization**: Sensitive data removed from error messages
- **Access Control**: Provider-level security controls

## 🐛 Troubleshooting

### Common Issues

1. **Provider Connection Failures**
   - Check API key validity in `.env.private`
   - Verify provider base URL configuration
   - Review network connectivity

2. **Test Failures**
   - Ensure both backend and frontend servers are running
   - Check port availability (7001, 7002)
   - Review test logs in console output

3. **Environment File Issues**
   - Use `/api/env/private/refresh` to regenerate `.env.private`
   - Verify provider enabled status
   - Check file permissions

### Debug Commands
```bash
# Check service status
curl http://localhost:7002/api/health

# Test specific provider
curl -X POST http://localhost:7002/api/providers/groq/test \
  -H "Content-Type: application/json" \
  -d '{"include_raw_data": true}'

# Check environment file status
curl http://localhost:7002/api/env/private
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run the enhanced test suite: `./run_enhanced_tests.sh`
5. Commit with descriptive messages
6. Push to your fork and create a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for the ChatGPT API
- **Groq** for high-speed inference
- **Cerebras** for advanced AI capabilities
- **OpenRouter** for model aggregation
- **Ollama** for local AI model support
- **Anthropic** for Claude integration

---

## 🎯 Quick Commands Reference

```bash
# Start application
./start_app.sh

# Run all tests
./run_enhanced_tests.sh

# Stop application
./stop_app.sh

# Backend tests only
python -m pytest test_env_private_backend.py -v

# Frontend tests only
node enhanced_puppeteer_tests_fixed.js

# Check API health
curl http://localhost:7002/api/health
```

**🌟 Ready for production deployment with enterprise-grade testing and security!** 🌟
