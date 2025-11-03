# LLM Management Page - Visual Guide

## 🎨 Page Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ABHIKARTA                                        🔄 Refresh   🧪 Test   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Dashboard | Planner ▼ | Workflows | DAGs | Execute ▼ | Manage ▼ | ...  │
│                                                        └─ 🧠 LLM Mgmt   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ 🧠 LLM Management                                                        │
│ Manage Language Model providers and configurations                      │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────┬───────────────┬───────────────┬───────────────┐
│ 🖥️ Providers  │ 🤖 Models     │ ⭐ Default     │ 🕐 Last Refresh│
│      8        │     23        │ anthropic/    │ 2025-10-30    │
│   (7 enabled) │ (20 enabled)  │ claude-sonnet │   15:32:10    │
└───────────────┴───────────────┴───────────────┴───────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ [All Models] [Anthropic ✓] [OpenAI ✓] [Google ✓] [Meta] [DeepSeek] ... │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Provider | Model         | Model ID        | Context | Cost | Features │
│─────────────────────────────────────────────────────────────────────────│
│ anthropic│ claude-opus-4 │ claude-opus-4-..│  200K   │ $15  │ 👁️ 💻 📡  │
│          │               │                 │         │ $75  │          │
│          │ Best for: complex reasoning, coding                         │
│          │ [Enabled] [Default]                                         │
│          │ [ℹ️ Info] [🧪 Test] [⭐ Default] [🔌 Disable]                │
│─────────────────────────────────────────────────────────────────────────│
│ anthropic│ claude-sonnet │ claude-sonnet-4.│  200K   │ $3   │ 👁️ 💻 📡  │
│          │ -4.5          │ 5-20250929      │         │ $15  │          │
│          │ Best for: workflow planning, data analysis                  │
│          │ [Enabled] [Default] ⚠️                                      │
│          │ [ℹ️ Info] [🧪 Test] [⭐ Default] [🔌 Disable]                │
│─────────────────────────────────────────────────────────────────────────│
│   ...more models...                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📱 Page Sections

### 1. Header Section
```
┌─────────────────────────────────────────────────────────┐
│ 🧠 LLM Management                [🔄 Refresh] [🧪 Test] │
│ Manage Language Model providers and configurations      │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Title with icon
- Admin-only buttons for refresh and test
- Descriptive subtitle

### 2. Summary Cards
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ PROVIDERS    │ MODELS       │ DEFAULT      │ LAST REFRESH │
│              │              │              │              │
│    8         │    23        │ anthropic/   │ 2025-10-30   │
│              │              │ claude-sonnet│   15:32:10   │
│ 7 enabled    │ 20 enabled   │ System LLM   │ Auto-refresh │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Shows:**
- Total and enabled provider count (Blue card)
- Total and enabled model count (Green card)
- Current default LLM (Yellow/Warning card)
- Last configuration refresh time (Info card)

### 3. Provider Tabs
```
┌────────────────────────────────────────────────────────┐
│ [All Models] [Anthropic ✓] [OpenAI ✓] [Google ✓] ... │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Tab for viewing all models
- Individual tabs for each provider
- Status indicator (✓ = enabled)
- Badge showing on/off status

### 4. Models Table (All Models Tab)
```
┌──────────────────────────────────────────────────────────────────┐
│ Provider | Model | Model ID | Context | Cost    | Best For | ... │
├──────────────────────────────────────────────────────────────────┤
│ anthropic│ opus-4│ claude-..│  200K   │ $15/$75 │ reasoning│ ... │
│ anthropic│ sonnet│ claude-..│  200K   │ $3/$15  │ planning │ ... │
│ openai   │ gpt-4o│ gpt-4o-..│  128K   │ $2.5/$10│ multimod.│ ... │
│ google   │ gemini│ gemini-..│ 2000K   │ $1.25/$5│ long ctx │ ... │
└──────────────────────────────────────────────────────────────────┘
```

**Columns:**
1. **Provider** - Badge with provider name
2. **Model** - Model name in bold
3. **Model ID** - Technical identifier in monospace
4. **Context** - Context window size (formatted)
5. **Cost** - Input/Output cost per 1M tokens (color coded)
6. **Best For** - Top capabilities as badges
7. **Features** - Icons for vision/function calling/streaming
8. **Status** - Enabled/Disabled badge + Default badge if applicable
9. **Actions** - Button group with actions

### 5. Provider-Specific Tabs
```
┌─────────────────────────────────────────────────────────┐
│ Anthropic Provider                                       │
│                                                          │
│ Status: [Enabled ✓]                                     │
│ API Key: ANTHROPIC_API_KEY                              │
│ Base URL: https://api.anthropic.com                     │
│ Models: 4 total                          [🔌 Disable All]│
│                                                          │
│ ┌───────────────────────────────────────────────────┐  │
│ │ Model      │ Description        │ Cost    │ Status │  │
│ ├───────────────────────────────────────────────────┤  │
│ │ opus-4     │ Most powerful...   │ $15/$75 │ ✓      │  │
│ │ sonnet-4.5 │ Smartest model...  │ $3/$15  │ ✓ ⚠️   │  │
│ └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Shows:**
- Provider configuration details
- Provider-wide enable/disable
- Simplified model table for that provider

### 6. Action Buttons

**Info Button (ℹ️)**
```
┌─────────────────────────────────────┐
│ Model Details                    [×]│
├─────────────────────────────────────┤
│ anthropic / claude-sonnet-4.5       │
│ ─────────────────────────────────── │
│ Model ID: claude-sonnet-4-5-2025... │
│ Version: 20250929                   │
│ Description: Smartest model...      │
│ Context Window: 200,000 tokens      │
│ Max Tokens: 200,000                 │
│ ─────────────────────────────────── │
│ Pricing                             │
│ Input: $3.00 per 1M tokens          │
│ Output: $15.00 per 1M tokens        │
│ ─────────────────────────────────── │
│ Best For                            │
│ • workflow planning                 │
│ • data analysis                     │
│ • code generation                   │
│ ─────────────────────────────────── │
│ Features                            │
│ [Vision ✓] [Functions ✓] [Stream ✓]│
└─────────────────────────────────────┘
```

**Test Button (🧪)**
```
┌─────────────────────────────────────┐
│ Test Results                     [×]│
├─────────────────────────────────────┤
│ Testing anthropic / claude-sonnet...│
│                                     │
│ [🔄 Spinner]                        │
│ Testing model...                    │
│                                     │
│ ─── After completion ───            │
│                                     │
│ ✓ Test Successful                   │
│                                     │
│ Response:                           │
│ ┌─────────────────────────────────┐ │
│ │ Hello! I'm Claude, and I'm     │ │
│ │ working correctly. How can I    │ │
│ │ help you today?                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Duration: 1.23 seconds              │
└─────────────────────────────────────┘
```

## 🎨 Color Scheme

### Provider Badges
- **Anthropic**: Blue (`badge bg-primary`)
- **OpenAI**: Blue (`badge bg-primary`)
- **Google**: Blue (`badge bg-primary`)
- **Meta**: Blue (`badge bg-primary`)
- All providers use consistent blue for uniformity

### Status Badges
- **Enabled**: Green (`badge bg-success`)
- **Disabled**: Gray (`badge bg-secondary`)
- **Default**: Yellow/Warning (`badge bg-warning text-dark`)

### Cost Display
- **Input cost**: Green text (`text-success`)
- **Output cost**: Red text (`text-danger`)

### Capability Tags
- **Best for tags**: Info blue (`badge bg-info text-dark`)
- **Additional count**: Light gray (`badge bg-light text-dark`)

### Summary Cards
- **Providers**: Primary blue background
- **Models**: Success green background
- **Default**: Info blue background
- **Last Refresh**: Warning yellow background

## 🔍 Interactive Elements

### Hover Effects
- Table rows highlight on hover
- Buttons show hand cursor
- Tooltips appear on icon hover

### Click Actions
1. **Info icon**: Opens modal with model details
2. **Test icon**: Opens modal and runs test
3. **Star icon**: Sets model as default (with confirmation)
4. **Toggle icon**: Enables/disables model (with confirmation)
5. **Provider tabs**: Switches between provider views

### Modals
- Centered on screen
- Blur background
- Close with X or clicking outside
- Animated fade-in

## 📊 Data Visualization

### Model Features Icons
```
👁️ Vision support (fas fa-eye)
💻 Function calling (fas fa-code)
📡 Streaming (fas fa-stream)
```

### Provider Icons
```
🧠 Anthropic (fas fa-brain)
🤖 OpenAI (fas fa-robot)
🔍 Google (fab fa-google)
📘 Meta (fab fa-meta)
☁️ AWS (fab fa-aws)
🤗 HuggingFace (fas fa-server)
```

## 🎯 User Flow

### View Models
```
1. Login → Navigate to Manage → LLM Management
2. See summary of providers/models
3. Browse all models in table
4. Switch to provider-specific tab for details
```

### Test a Model
```
1. Find model in table
2. Click test icon (🧪)
3. Wait for modal to show results
4. See response and duration
5. Close modal
```

### Set Default LLM (Admin)
```
1. Find desired model
2. Click star icon (⭐)
3. Confirm in dialog
4. See page reload with new default
5. New default shown in summary card
```

### Enable/Disable Model (Admin)
```
1. Find model to toggle
2. Click enable/disable button
3. Confirm action
4. See page reload with updated status
```

## 📱 Responsive Design

### Desktop (>992px)
- Full table width
- 4 summary cards in row
- All columns visible
- Side-by-side buttons

### Tablet (768px - 992px)
- Scrollable table
- 2 summary cards per row
- Key columns visible
- Stacked buttons

### Mobile (<768px)
- Horizontal scroll for table
- 1 summary card per row
- Minimal columns
- Icon-only buttons

## ✨ Special Features

### Auto-Refresh Indicator
```
🕐 Last Refresh
2025-10-30 15:32:10
Auto-refresh every 10 min
```

### Default Model Indicator
```
Model Name
[Enabled] [Default ⚠️]
```

### Provider Status in Tabs
```
[Anthropic ✓]  ← Enabled provider
[DeepSeek]     ← Disabled provider
```

### Cost Comparison
```
Input:  $3.00/1M  (green)
Output: $15.00/1M (red)
```

Shows at-a-glance cost for quick comparison.

---

**This visual guide shows the complete UI/UX of the LLM management page.**
