# Fridgic

A computer vision-powered food inventory management system designed to reduce household food waste through intelligent expiration tracking and automated item recognition.

## Abstract

Fridgic addresses the significant problem of household food waste by providing an automated system for tracking refrigerator contents and their expiration dates. The application leverages large language models with vision capabilities (Claude API) to extract food item information from photographs of refrigerator contents and grocery receipts. The system maintains a persistent database of items with their associated shelf life data, enabling users to monitor food freshness and consume items before spoilage.

## System Architecture

The application consists of two primary interfaces:

1. **Desktop Application** (`main.py`): A Python-based graphical user interface built with Tkinter for local execution
2. **Web Application** (`web_app.py`): A Flask-based REST API with a mobile-optimized HTML/JavaScript frontend

Both interfaces share common backend functionality for data persistence and API communication.

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Flask 2.x |
| Desktop GUI | Tkinter |
| Vision AI | Anthropic Claude API (claude-sonnet-4-20250514) |
| Data Storage | JSON file-based persistence |
| Frontend | Vanilla JavaScript, CSS3 |

## Features

### Core Functionality

- **Image-based Item Recognition**: Automatic identification of food items from refrigerator photographs using computer vision
- **Receipt Scanning**: Extraction of purchased items from grocery receipt images with original naming preservation (supports multilingual receipts)
- **Expiration Tracking**: Configurable shelf life database with automatic expiry date calculation
- **Status Classification**: Items categorized by freshness status (expired, expiring today, expiring soon, fresh, no date)

### User Interface Features

- **Progressive Web App (PWA)**: Mobile-installable web application with home screen icon support
- **Dark Mode**: System-wide theme toggle with persistent preference storage
- **Swipe Gestures**: Touch-optimized delete functionality with two-step confirmation
- **Multi-select Operations**: Batch selection and deletion of items
- **Search and Filtering**: Real-time search with category-based filtering
- **Collapsible Groups**: Items organized by expiration status with expandable sections

### Data Management

- **Shelf Life Learning**: System remembers shelf life durations for previously scanned items
- **Editable Entries**: Full CRUD operations for both inventory items and shelf life data
- **Automatic Sorting**: Items sorted by expiration date (soonest first)

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key with access to Claude models

### Setup Procedure

1. Clone the repository:
```bash
git clone https://github.com/[username]/fridgic.git
cd fridgic
```

2. Install required dependencies:
```bash
pip install anthropic python-dotenv flask
```

3. Configure environment variables by creating a `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
```

4. Create required directories (for web application):
```bash
mkdir -p static templates
```

5. Place `index.html` in the `templates/` directory

6. (Optional) Add application icon as `static/icon.png`

## Usage

### Desktop Application

```bash
python main.py
```

### Web Application

```bash
python web_app.py
```

The server will start on `http://0.0.0.0:5000`. Access from mobile devices using the host machine's local IP address.

### Adding to Mobile Home Screen

1. Navigate to the application URL in Safari (iOS) or Chrome (Android)
2. Access the share menu
3. Select "Add to Home Screen"

## API Reference

The web application exposes the following REST endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/items` | Retrieve all inventory items with computed status |
| POST | `/api/items` | Add new item to inventory |
| PUT | `/api/items/<name>` | Update existing item |
| DELETE | `/api/items/<name>` | Remove item from inventory |
| POST | `/api/scan` | Process image for item recognition |
| GET | `/api/shelf-life` | Retrieve shelf life database |
| POST | `/api/shelf-life` | Add shelf life entry |
| PUT | `/api/shelf-life/<name>` | Update shelf life duration |
| DELETE | `/api/shelf-life/<name>` | Remove shelf life entry |
| POST | `/api/process-receipt` | Process receipt items with shelf life matching |

## File Structure

```
fridgic/
├── main.py                 # Desktop application entry point
├── web_app.py              # Flask web server
├── templates/
│   └── index.html          # Web application frontend
├── static/
│   └── icon.png            # Application icon
├── fridge_data.json        # Inventory persistence (auto-generated)
├── shelf_life_data.json    # Shelf life database (auto-generated)
├── .env                    # Environment configuration
├── .gitignore
└── README.md
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Claude model access |

### Data Files

The application automatically generates and maintains two JSON files:

- `fridge_data.json`: Current inventory with items, quantities, and expiration dates
- `shelf_life_data.json`: Learned shelf life durations keyed by item name

## Limitations and Future Work

### Current Limitations

- Single-user design without authentication
- Local file-based storage (not suitable for distributed deployment)
- Requires manual refresh for multi-device synchronization

### Planned Enhancements

- Push notification support for expiration alerts
- Barcode scanning integration
- Recipe suggestions based on expiring ingredients
- Multi-user support with cloud synchronization
- Historical analytics and waste tracking metrics

## License

MIT License

## Acknowledgments

This project utilizes the Anthropic Claude API for vision-based item recognition. The system prompt engineering approach enables reliable extraction of structured data from unstructured image inputs.