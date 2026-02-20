# 🧊 Fridge Tracker

An AI-powered desktop app that helps you track what's in your fridge and reduce food waste.

## Features

- 📷 **Scan fridge photos** — AI automatically identifies food items
- ➕ **Manual entry** — Add items and expiry dates yourself
- 📊 **Smart sorting** — Items sorted by expiry date (soonest first)
- ⚠️ **Expiry alerts** — Warning popup when you open the app
- 🎨 **Color-coded status** — Red (expired), Yellow (soon), Green (fresh)

## Tech Stack

- Python 3
- Tkinter (GUI)
- Anthropic Claude API (image recognition)

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install anthropic python-dotenv
   ```
3. Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```
4. Run the app:
   ```
   python main.py
   ```

## Getting an API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and generate an API key
3. Add it to your `.env` file

## Future Plans

- [ ] Daily email notifications for expiring items
- [ ] Mobile integration
- [ ] Recipe suggestions based on expiring ingredients

## License

MIT