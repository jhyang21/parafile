# Release Notes - Version 0.0.2

**Release Date:** July 28, 2025  
**License:** MIT License  
**Author:** Andrew Yang

---

## 🚀 What's in v0.0.2

This release had a strong focus on enhancing the core AI capabilities, improving user flexibility, and establishing a robust development and CI/CD pipeline.

### **✨ Key Features & Enhancements**

-   **Intelligent Naming with Resilient Fallback Logic**: The AI-powered renaming function, `generate_ai_filename`, has been significantly improved. It now includes a fallback mechanism where if the AI cannot extract a specific variable, it will insert a clear placeholder (e.g., `<NAME>`) into the filename. This prevents the renaming process from failing and ensures that every file is still organized, even if some data points are ambiguous.

-   **Toggleable File Organization**: To provide users with more control over their file structures, the auto-organization feature is now toggleable. You can choose whether Parafile automatically moves renamed files into categorized subfolders or leaves them in the main monitored directory.

-   **Streamlined Configuration**: The configuration process has been simplified by removing the concept of "variable types." The AI now intelligently infers the type of data to extract based on the variable's description, making the initial setup faster and more intuitive.

-   **Enhanced Document Support**: Added support for password-protected PDF files, allowing Parafile to process a wider range of documents securely.

-   **Improved AI Workflow**: The AI workflow has been optimized for better performance and more accurate variable extraction from documents.

### **🛠️ Development & CI/CD Pipeline**

-   **Comprehensive CI/CD Automation**: A full-featured CI/CD pipeline has been established using GitHub Actions.
    -   **Automated Formatting and Linting**: `black`, `isort`, and `autopep8` are now run automatically to enforce a consistent code style across the entire project.
    -   **Multi-Version Python Testing**: The application is now tested against Python versions 3.10, 3.11, and 3.12 to ensure broad compatibility.
    -   **Optimized Workflows**: The pipeline is configured to run checks only on `main` and `dev` branches to conserve resources.

-   **Code Quality and Refactoring**:
    -   Numerous small refactoring changes have been made to improve code readability and maintainability.
    -   Fixed a wide range of formatting inconsistencies and applied best practices.

---

## 🔮 Future Roadmap

### **Planned Features**
- [ ] Support for additional file formats (Excel, PowerPoint, Videos, Images, Audio)
- [ ] Batch processing of existing files
- [ ] Advanced pattern matching rules
- [ ] System tray integration
- [ ] Multi-folder monitoring with independent rules per folder
- [ ] Full file change detection (new, modified, overwritten files)
- [ ] Variable validation to enforce consistent naming patterns
- [ ] Variable picker UI for easy naming pattern creation
- [ ] AI-powered category suggestions for uncategorized documents