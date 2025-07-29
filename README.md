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

# Install dependencies
pip install -r requirements.txt

# Set up your OpenAI API key
cp env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

### 2. Configure
```bash
python main.py
```
- Select the folder to be monitored
- Create categories (e.g., "Invoices", "Reports")
- Add variables (e.g., "name", "date", "amount")
- Set naming patterns (e.g., "{date}_{fullname}_invoice")

### 3. Start Monitoring

Click on the "Start Monitoring" button; Drop PDF/Word files in your monitored folder and watch them get organized automatically!

## ✨ How It Works

1.  **Drop a file** in your monitored folder.
2.  The application **extracts text** from the document.
3.  **AI analyzes** the text to determine the best category.
4.  **AI extracts** key information (like name, date, etc.) based on your configured variables.
5.  The **file is renamed** using your naming pattern and the extracted data.
6.  The renamed **file moves** to the appropriate category subfolder. (toggleable feature)

### Example

**Before:** A file named `invoice123.pdf` is dropped into the main monitored folder.

**After:** The file is renamed to `2024-12-25_MegaCorp_invoice.pdf` and moved to the `Invoices` subfolder.

## ⚙️ Configuration

The application's behavior is controlled by a `config.json` file, which you can set up using the built-in GUI.

### Variables

Define the specific pieces of information you want the AI to find in your documents.

-   **`name`**: The full name of the company or individual.
-   **`date`**: The primary date on the document (e.g., invoice date, report date).
-   **`amount`**: The monetary value for the entire invoice.
-   **`project_name`**: A specific project identifier.

### Categories

Set up rules for how different types of files should be organized.

-   **Name**: The name of the category (and the subfolder it will create).
-   **Description**: A brief explanation to help the AI understand what belongs in this category.
-   **Naming Pattern**: The template for how files in this category should be renamed. Use curly braces `{}` to include variables (e.g., `{date}_{name}_invoice`).

### Example `config.json`

```json
{
  "monitored_folder": "path/to/your/documents",
  "enable_organization": true,
  "categories": [
    {
      "name": "Invoices",
      "naming_pattern": "{date}_{name}_invoice.pdf",
      "description": "Financial documents, including invoices and receipts from vendors."
    },
    {
      "name": "Reports",
      "naming_pattern": "Report_{project_name}_{date}.pdf",
      "description": "Internal and external project reports and status updates."
    }
  ],
  "variables": [
    {
      "name": "name",
      "description": "The full name of the company or entity that issued the document."
    },
    {
      "name": "date",
      "description": "The primary date on the document, formatted as YYYY-MM-DD."
    }
  ]
}
```

## 🔧 Features

-   **🤖 AI-Powered Analysis**: Leverages OpenAI's models to understand and categorize document content.
-   **📝 Smart Renaming**: Consistently renames files based on extracted data and user-defined patterns.
-   **📁 Automated Organization (Toggleable)**: Automatically moves files into categorized subfolders.
-   **⚙️ Simple GUI Setup**: An easy-to-use interface for initial configuration.
-   **🔄 Real-Time Monitoring**: Watches your folder for new files and processes them on the fly.
-   **📄 Supports PDF and Word**: Extracts text from both `.pdf` and `.docx` files.
-   **💪 Resilient Fallback**: If the AI cannot extract a piece of information, it uses a placeholder (e.g., `<NAME>`) instead of failing, ensuring the file is still organized.

## 🆘 Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**

-   Ensure the `.env` file exists in the project root and contains your API key.
-   The format should be `OPENAI_API_KEY=sk-...`.

**Files Not Being Processed**

-   Confirm that the files are of a supported format (`.pdf` or `.docx`).
-   Verify that the monitored folder path in `config.json` is correct.
-   Organization within the subfolders of the main monitored folder is not supported at this time.

**Incorrectly Named Files**

-   If a filename contains a placeholder like `<NAME>`, it means the AI could not confidently extract that specific piece of information. You may need to refine the variable's description in the config GUI to be more specific.
-   Check the logs within the terminal for any error messages related to the AI analysis.

### Getting Help

For more detailed insight, you can check the logs within the terminal 'main.py' was run in. It contains detailed information about each step of the process.

If you encounter persistent issues, please [open an issue](https://github.com/jhyang21/parafile/issues) on GitHub.

## 📁 Project Structure

```
parafile/
│
├── .github/               # GitHub Actions CI/CD workflows
├── config_templates/      # Default configuration templates
├── docs/                  # Project documentation
├── src/                   # Core source code
│   ├── ai_processor.py    # AI analysis and data extraction
│   ├── config_manager.py  # Configuration management
│   ├── gui.py             # GUI for configuration
│   ├── organizer.py       # File monitoring and organization
│   └── text_extractor.py  # Text extraction from documents
│
├── tests/                 # Unit and integration tests
├── .env                   # Environment variables (API key)
├── .gitignore             # Git ignore rules
├── config.json            # User-defined settings
├── main.py                # Main CLI entry point
├── LICENSE                # Project license
├── README.md              # This file
└── requirements.txt       # Project dependencies
```

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
