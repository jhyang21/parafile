# Parafile: AI-Powered File Renamer and Organizer

Automatically rename and organize your PDF and Word documents with your naming and organization rules. Simply drop files in your monitored folder and watch them get intelligently renamed and organized!

## 🎥 Demo

[Watch the Parafile Demo Video](https://youtu.be/6As2GGTU0gk)

## **Prerequisites**
1. Python 3.10+ installed
2. OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## 🚀 Quick Start

### 1. Install & Setup
```bash
# Clone repository
git clone https://github.com/jhyang21/parafile.git
cd parafile

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your OpenAI API key
cp env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

### 2. Configure
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows use: venv\Scripts\activate

python main.py
```
- Select the folder to be monitored
- Create categories (e.g., "Invoices", "Reports")
- Add variables (e.g., "vendor", "date", "amount")
- Set naming patterns (e.g., "{date}_{vendor}_invoice")

### 3. Start Monitoring
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows use: venv\Scripts\activate

python main.py monitor
```
Now drop PDF/Word files in your monitored folder and watch them get organized automatically!

## ✨ How It Works

1. **Drop a file** in your monitored folder
2. **AI analyzes** the document content
3. **File gets categorized** and renamed automatically
4. **File moves** to the appropriate subfolder

### Example
**Before:** `Invoice_ABC_Company_Dec2024.pdf` (in Downloads/)

**After:** `2024-12-15_ABC_Company_invoice.pdf` (in Downloads/Invoices/)

## ⚙️ Configuration

### Variables
Define what information to extract from documents:
- `vendor` - Company name
- `date` - Document date
- `amount` - Monetary value
- `project_name` - Project identifier

### Categories
Define how to organize files:
- **Name:** Folder name (e.g., "Invoices")
- **Description:** What documents belong here
- **Naming Pattern:** How to rename files (e.g., `{date}_{vendor}_invoice`)

### Example Setup
```json
{
  "categories": [
    {
      "name": "Invoices",
      "naming_pattern": "{date}_{vendor}_invoice",
      "description": "Financial documents like invoices and receipts"
    },
    {
      "name": "Reports", 
      "naming_pattern": "Report_{project_name}_{date}",
      "description": "Project reports and status updates"
    }
  ],
  "variables": [
    {
      "name": "vendor",
      "description": "Company that issued the document"
    },
    {
      "name": "date", 
      "description": "Document date (YYYY-MM-DD)"
    }
  ]
}
```

## 🔧 Features

- **📁 Auto-organization** - Files move to category folders
- **🤖 AI-powered** - Uses OpenAI to understand document content
- **📝 Smart renaming** - Structured, consistent filenames
- **⚙️ Easy setup** - Simple GUI configuration
- **🔄 Real-time** - Monitors folder for new files

## 🆘 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**
- Make sure `.env` file exists with your API key
- Format: `OPENAI_API_KEY=sk-...`

**Files not being processed**
- Check that files are `.pdf` or `.docx`
- Verify the folder path exists
- Ensure files aren't open in other apps

**Permission errors**
- The app automatically retries after delays
- Close any apps that might have the file open

### Getting Help
```bash
# Run with detailed logs
python main.py monitor

# Example output:
# 2024-12-15 10:30:15 - INFO - Started monitoring Downloads
# 2024-12-15 10:31:20 - INFO - New file: invoice.pdf
# 2024-12-15 10:31:25 - INFO - Moved to: Invoices/2024-12-15_supplier_invoice.pdf
```

## 📁 Project Structure

```
parafile/
│
├── main.py                # Entry point for CLI (gui/monitor commands)
├── src/                   # Source code directory
│   ├── __init__.py        # Package initialization
│   ├── gui.py             # GUI configuration interface
│   ├── organizer.py       # File monitoring and organizing logic
│   ├── ai_processor.py    # AI document analysis and variable extraction
│   ├── text_extractor.py  # PDF/Word text extraction utilities
│   └── config_manager.py  # Configuration loading and saving
│
├── config.json            # User configuration (categories, variables, etc.)
├── env.example            # Example environment variables
├── requirements.txt       # Python dependencies
├── LICENSE
├── README.md
└── RELEASE_NOTES.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Need help?** Check the [Release Notes](RELEASE_NOTES.md) for detailed technical information.
