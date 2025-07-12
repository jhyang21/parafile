# AI-Powered File Renamer and Organizer

Automatically rename and organize PDF and Word documents in your Downloads folder using AI-powered categorization and smart renaming.

## Overview

This desktop application monitors a specified folder (like Downloads) for new PDF and Word documents, extracts their text content, and uses OpenAI's API to intelligently categorize and rename files based on your custom rules. Files are automatically moved to organized subfolders with meaningful, structured names.

## Features

- **🔍 Automatic File Monitoring**: Background service watches for new `.pdf` and `.docx` files
- **🤖 AI-Powered Categorization**: Uses OpenAI API to analyze document content and determine appropriate categories
- **📝 Smart Renaming**: Generates structured filenames based on document content and your naming patterns
- **📁 Organized Storage**: Automatically creates category subfolders and moves files accordingly
- **⚙️ User-Friendly Configuration**: Simple GUI to manage watched folders and category rules
- **🔧 Customizable Rules**: Define your own categories, descriptions, and naming patterns
- **🏷️ Custom Variables**: Create reusable variables that the AI can extract from documents

## Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/rename-download-files.git
   cd rename-download-files
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your_actual_api_key_here
   ```

### Usage

1. **Configure your settings** (first time setup):
   ```bash
   python gui.py
   ```
   - Set your watched folder (e.g., Downloads)
   - Define variables that the AI can extract from documents
   - Create categories with naming patterns using your variables
   - Save your configuration

2. **Start the file organizer**:
   ```bash
   python organizer.py
   ```
   - The service will run in the background
   - New PDF/Word files will be automatically processed
   - Press `Ctrl+C` to stop

## Configuration

The application uses a two-tier system: **Variables** and **Categories**.

### Variables

Variables are reusable placeholders that the AI can extract from document content:

- **Name**: The variable identifier (e.g., `vendor`, `date`, `amount`)
- **Description**: Helps the AI understand what information to extract from documents

### Categories

Categories define how files are organized and named:

- **Name**: Category identifier (becomes subfolder name)
- **Description**: Helps AI understand what documents belong in this category
- **Naming Pattern**: Template for renaming files with placeholders

#### Example Configuration

```json
{
  "watched_folder": "C:\\Users\\YourName\\Downloads",
  "variables": [
    {
      "name": "vendor", 
      "description": "Name of the company or person that issued the invoice or receipt."
    },
    {
      "name": "project_name",
      "description": "The project identifier or name found within the document."
    },
    {
      "name": "document_type", 
      "description": "The type of document such as invoice, report, proposal, etc."
    },
    {
      "name": "date",
      "description": "The primary date mentioned in the document (YYYY-MM-DD format)."
    },
    {
      "name": "amount",
      "description": "The monetary amount or total value mentioned in the document."
    }
  ],
  "categories": [
    {
      "name": "Invoices and Receipts",
      "naming_pattern": "{date}_{vendor}_invoice",
      "description": "Any document related to a purchase or service. This includes invoices, bills, receipts, and payment confirmations."
    },
    {
      "name": "Project Documents", 
      "naming_pattern": "Project_{project_name}_{document_type}_{date}",
      "description": "Documents related to work projects, such as status reports, project plans, meeting notes, or client proposals."
    }
  ]
}
```

#### How It Works

1. **Define Variables**: Create variables like `vendor`, `date`, `amount` with descriptions
2. **Create Categories**: Set up categories with naming patterns using your variables
3. **AI Processing**: The AI analyzes documents, extracts variable values, and applies naming patterns

#### Common Variable Examples

- **Financial**: `vendor`, `amount`, `invoice_number`, `account_number`
- **Project**: `project_name`, `client_name`, `phase`, `deliverable`
- **Legal**: `contract_type`, `party_name`, `effective_date`, `jurisdiction`
- **Academic**: `course_name`, `professor`, `semester`, `assignment_type`
- **Medical**: `patient_name`, `procedure`, `diagnosis`, `doctor_name`

### Example File Processing

**Before**: `Invoice_ABC_Company_Dec2024.pdf` (in Downloads)

**After**: `2024-12-15_ABC_Company_invoice.pdf` (in Downloads/Invoices and Receipts/)

## Project Structure

```
rename-download-files/
├── requirements.txt         # Project dependencies
├── env.example             # Environment template
├── config.json             # User configuration
├── config_manager.py       # Configuration file handling
├── text_extractor.py       # PDF/Word text extraction
├── ai_processor.py         # OpenAI API integration
├── organizer.py           # Main background service
├── gui.py                 # Configuration interface
└── README.md              # This file
```

## Dependencies

- **watchdog==6.0.0** - File system monitoring
- **openai==1.95.0** - OpenAI API client
- **python-docx==1.2.0** - Word document processing
- **PyPDF2==3.0.1** - PDF text extraction
- **python-dotenv==1.1.1** - Environment variables
- **pyinstaller==6.14.2** - Executable packaging

## Advanced Usage

### Running as a Service

For continuous operation, you can run the organizer as a background service or scheduled task.

### Packaging as Executable

Create a standalone executable:

```bash
pyinstaller --onefile --windowed gui.py
pyinstaller --onefile organizer.py
```

### Custom Categories

Add specialized categories and variables for your workflow:

```json
{
  "variables": [
    {
      "name": "tax_year",
      "description": "The tax year this document pertains to (YYYY format)."
    },
    {
      "name": "form_type", 
      "description": "The specific tax form type (e.g., W-2, 1099, Schedule C)."
    },
    {
      "name": "entity",
      "description": "The business or individual entity name on the tax document."
    }
  ],
  "categories": [
    {
      "name": "Tax Documents",
      "naming_pattern": "Tax_{tax_year}_{form_type}_{entity}",
      "description": "Tax-related documents including forms, receipts, and correspondence from tax authorities."
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Ensure `.env` file exists with your API key
   - Check the key format: `OPENAI_API_KEY=sk-...`

2. **Files not being processed**
   - Verify the watched folder path exists
   - Check file permissions
   - Ensure files are `.pdf` or `.docx` format

3. **AI categorization errors**
   - Review category descriptions for clarity
   - Check OpenAI API quota and billing
   - Verify internet connection

### Logs and Debugging

The organizer outputs detailed logs to help diagnose issues:

```bash
python organizer.py
# 2024-12-15 10:30:15 - INFO - Started monitoring 'C:\Users\...\Downloads' for new documents...
# 2024-12-15 10:31:20 - INFO - New file detected: invoice.pdf
# 2024-12-15 10:31:25 - INFO - AI suggestion: category='Invoices and Receipts', name='2024-12-15_supplier_invoice'
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 Documentation: This README
- 🐛 Bug Reports: GitHub Issues
- 💡 Feature Requests: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

**Note**: This application sends document text to OpenAI's API for processing. Ensure you're comfortable with OpenAI's data usage policies before processing sensitive documents.
