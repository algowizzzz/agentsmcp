# Abhikarta LLM Management System

## Overview

This comprehensive LLM (Large Language Model) management system provides centralized configuration and administration of multiple AI models from various providers for the Abhikarta multi-agent orchestration platform.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google, AWS Bedrock, Meta, Mistral, DeepSeek, Alibaba, Microsoft, HuggingFace, and more
- **Centralized Configuration**: All LLM configurations stored in `config/llm/llm.json`
- **Singleton Facade Pattern**: Thread-safe singleton with auto-refresh every 15 minutes
- **Admin Web Interface**: Full CRUD operations for LLM configurations
- **Model Selection**: Users can select specific models in the planner interface
- **Default Model Configuration**: System-wide default with fallback to mock provider
- **Mock Provider**: Built-in testing provider that requires no API keys

## Architecture

### Components

1. **llm.json** - Comprehensive database of LLM configurations
2. **llm_facade.py** - Singleton facade with auto-refresh and provider integrations
3. **Admin Pages** - Web interface for LLM management (admin-only)
4. **API Routes** - RESTful endpoints for LLM operations
5. **Planner Integration** - Model selector in LangGraph planner

### Directory Structure

```
abhikarta/
├── config/
│   └── llm/
│       └── llm.json           # LLM configuration database
├── llm_facade.py              # LLM Facade (singleton)
├── templates/
│   ├── base.html              # Updated navigation with LLM admin
│   ├── llms.html              # LLM list/management page
│   ├── llm_add.html           # Add new LLM
│   ├── llm_edit.html          # Edit existing LLM
│   └── lgraph_planner.html    # Updated with model selector
└── app.py                     # Flask routes (add LLM routes)
```

## Installation

### 1. Copy Files

Copy all new files to your Abhikarta installation:

```bash
# Core files
cp llm_facade.py /path/to/abhikarta/
cp config/llm/llm.json /path/to/abhikarta/config/llm/

# Templates
cp templates/llms.html /path/to/abhikarta/templates/
cp templates/llm_add.html /path/to/abhikarta/templates/
cp templates/llm_edit.html /path/to/abhikarta/templates/
cp templates/lgraph_planner.html /path/to/abhikarta/templates/  # Updated version
cp templates/base.html /path/to/abhikarta/templates/  # Updated version
```

### 2. Update app.py

Add the LLM management routes from `app_llm_routes.py` to your `app.py`. Key additions:

```python
from llm_facade import get_llm_facade

# Initialize LLM Facade
llm_facade = get_llm_facade()

# Add admin_required decorator
# Add all LLM routes (/admin/llms/*, /api/llms/*)
# Update lgraph_planner_page to pass available_models
# Update api_lgraph_planner_chat to accept model_id
```

### 3. Install Dependencies

```bash
pip install anthropic  # For Claude models
pip install openai     # For GPT models
pip install google-generativeai  # For Gemini models
pip install boto3      # For AWS Bedrock
pip install mistralai  # For Mistral models
```

## Configuration

### LLM Configuration Format

Each model in `llm.json` has the following structure:

```json
{
  "id": "claude-sonnet-4-5",
  "provider": "anthropic",
  "model": "claude-sonnet-4.5",
  "version": "20250929",
  "enabled": true,
  "description": "Claude Sonnet 4.5 - The smartest Claude model...",
  "api_key_required": true,
  "max_tokens": 200000,
  "supports_streaming": true
}
```

### Required Fields

- `id`: Unique identifier for the model
- `provider`: Provider name (anthropic, openai, google, etc.)
- `model`: Actual model name used in API calls
- `version`: Model version
- `enabled`: Whether the model is available for use
- `description`: What the model is good at and when to use it
- `api_key_required`: Whether an API key is needed
- `max_tokens`: Maximum context length
- `supports_streaming`: Whether streaming is supported

### Environment Variables

Set API keys as environment variables:

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export GOOGLE_API_KEY="your-key-here"
export MISTRAL_API_KEY="your-key-here"
export DEEPSEEK_API_KEY="your-key-here"
```

For AWS Bedrock, configure AWS credentials via boto3:

```bash
aws configure
```

## Usage

### Admin Interface

1. **Access LLM Management**
   - Navigate to Admin → LLM Management
   - View all configured models with filtering and search
   - See status: total models, enabled count, providers

2. **Add New LLM**
   - Click "Add LLM" button
   - Fill in required fields
   - Select provider from dropdown
   - Add description explaining use cases
   - Configure max tokens and options
   - Save

3. **Edit Existing LLM**
   - Click edit icon on any model
   - Modify configuration
   - Cannot change model ID
   - Save changes

4. **Delete LLM**
   - Click delete icon
   - Cannot delete default or system models
   - Confirm deletion

5. **Set Default Model**
   - Click star icon on any model
   - This becomes the system default
   - Used when no model is explicitly selected

6. **Refresh Configuration**
   - Click "Refresh Config" to reload from file
   - Auto-refreshes every 15 minutes

### Using Models in Planner

1. **Open LangGraph Planner**
   - Navigate to Planner → LangGraph Planner

2. **Select Model**
   - Use the model dropdown at top of chat
   - Choose from enabled models
   - Leave empty to use default
   - Model info displayed when selected

3. **Chat with Planner**
   - Selected model will be used for all responses
   - Model badge shown on assistant messages

4. **Create Plan**
   - Model selection carries over to plan creation
   - Can be changed at plan creation time

## API Reference

### List Models

```
GET /api/llms
GET /api/llms?provider=anthropic
GET /api/llms?enabled_only=true
```

### Get Model

```
GET /api/llms/<model_id>
```

### Add Model

```
POST /api/llms
Content-Type: application/json

{
  "id": "custom-model",
  "provider": "openai",
  "model": "gpt-4",
  "version": "1.0",
  "enabled": true,
  "description": "Custom GPT-4 configuration",
  "api_key_required": true,
  "max_tokens": 8192,
  "supports_streaming": true
}
```

### Update Model

```
PUT /api/llms/<model_id>
Content-Type: application/json

{
  "enabled": false,
  "description": "Updated description"
}
```

### Delete Model

```
DELETE /api/llms/<model_id>
```

### Set Default

```
POST /api/llms/default
Content-Type: application/json

{
  "model_id": "claude-sonnet-4-5"
}
```

### Reload Config

```
POST /api/llms/reload
```

### Get Status

```
GET /api/llms/status
```

## LLM Facade API

### Python Usage

```python
from llm_facade import get_llm_facade

# Get singleton instance
facade = get_llm_facade()

# List all models
models = facade.list_models()

# List enabled models for a provider
models = facade.list_models(provider='anthropic', enabled_only=True)

# Get specific model
model = facade.get_model('claude-sonnet-4-5')

# Generate text (uses default model if none specified)
response = facade.generate("Hello, how are you?")

# Generate with specific model
response = facade.generate("Hello!", model_id='gpt-4o')

# Add new model
facade.add_model({
    'id': 'new-model',
    'provider': 'openai',
    'model': 'gpt-4',
    # ... other fields
})

# Update model
facade.update_model('new-model', {'enabled': False})

# Delete model
facade.delete_model('new-model')

# Set default
facade.set_default_model('claude-sonnet-4-5')

# Get status
status = facade.get_status()
```

## Pre-Configured Models

The system comes with 40+ pre-configured models:

### Anthropic Claude
- Claude Sonnet 4.5 (latest, smartest)
- Claude Sonnet 4
- Claude Opus 4.1 (most powerful)
- Claude 3.5 Sonnet
- Claude 3 Haiku (fastest)

### OpenAI
- GPT-4o (flagship multimodal)
- GPT-4o Mini (cost-effective)
- GPT-4 Turbo
- GPT-3.5 Turbo
- O1 Preview (advanced reasoning)
- O1 Mini

### Google Gemini
- Gemini 2.0 Flash (experimental)
- Gemini 1.5 Pro (2M context)
- Gemini 1.5 Flash
- Gemini 1.5 Flash 8B

### AWS Bedrock
- Claude models via Bedrock
- Llama models via Bedrock
- Mistral models via Bedrock
- Titan models

### Meta Llama
- Llama 3.1 405B
- Llama 3.1 70B
- Llama 3.1 8B
- Llama 3.2 Vision models
- Llama 3.2 lightweight (1B, 3B)

### Mistral AI
- Mistral Large
- Mistral Small
- Codestral (code specialist)
- Mixtral 8x22B
- Mixtral 8x7B

### DeepSeek
- DeepSeek V2.5
- DeepSeek Coder V2

### Alibaba Qwen
- Qwen 2.5 72B
- Qwen 2.5 32B
- Qwen 2.5 7B
- Qwen 2.5 Coder 32B

### Microsoft Phi
- Phi-4 (14B)
- Phi-3.5 Mini (3.8B)

### Mock Provider
- Mock Default (testing, no API key)

## Features

### Auto-Refresh
- Configuration automatically reloads every 15 minutes
- Manual refresh available via admin interface
- Thread-safe singleton pattern ensures consistency

### Filtering & Search
- Filter by provider
- Filter by status (enabled/disabled)
- Search by model name or description
- Real-time client-side filtering

### Model Information
- Provider-specific documentation links
- Required environment variables
- Use case descriptions
- Token limits and streaming support

### Safety
- Cannot delete default model
- Cannot delete system mock provider
- Admin-only access to management
- Validation on all operations

## Troubleshooting

### Model Not Working
1. Check API key is set in environment
2. Verify model is enabled
3. Check provider implementation in llm_facade.py
4. Review logs for error messages

### Configuration Not Updating
1. Click "Refresh Config" in admin interface
2. Check file permissions on llm.json
3. Verify JSON syntax is valid
4. Restart application if needed

### Mock Provider Issues
- Mock provider always available as fallback
- Returns predefined responses
- No API key required
- Good for testing and development

## Best Practices

1. **Testing**: Use mock provider during development
2. **Default Model**: Set a reliable, cost-effective model as default
3. **Descriptions**: Write clear, actionable descriptions
4. **API Keys**: Store securely in environment variables
5. **Monitoring**: Track usage and costs per provider
6. **Updates**: Keep model versions current in configuration
7. **Backups**: Backup llm.json before major changes

## Security

- Admin-only access to LLM management
- API keys stored in environment, not in config
- Thread-safe operations
- Input validation on all endpoints
- Cannot delete critical system models

## Contributing

When adding new providers:

1. Add integration method to llm_facade.py
2. Add provider to dropdowns in templates
3. Document required environment variables
4. Add example models to llm.json
5. Update this README

## License

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com
https://www.github.com/ajsinha/abhikarta

## Support

For issues or questions:
- GitHub: https://github.com/ajsinha/abhikarta
- Email: ajsinha@gmail.com
