# 🛡️ GVM Vulnerability Report Builder

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]() [![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)]() [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Build with PyInstaller](https://img.shields.io/badge/Build-PyInstaller-orange)]()

**Transform raw GVM/OpenVAS vulnerability scan reports into professional, client-ready documents with automated image processing, OCR text extraction, and intelligent report generation.**

<img width="2900" height="737" alt="Banner" src="https://github.com/user-attachments/assets/2104c94c-c565-43c1-aafa-2f91b82a7c6f" />

---

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [Report Generation Levels](#-report-generation-levels)
- [Output Files](#-output-files)
- [Building Executable](#️-building-executable)
- [Project Structure](#-project-structure)
- [Technical Details](#-technical-details)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Capabilities
- **Dual Input Processing**: Parse both TXT and PDF reports from GVM/OpenVAS simultaneously
- **Intelligent Image Extraction**: Automatically extract and process vulnerability screenshots from PDF reports
- **OCR Text Recognition**: Integrated Tesseract OCR for extracting text from images (packaged with executable)
- **Smart Image Classification**: Automatically categorize images by color (Red/Critical, Orange/High, Yellow/Medium)
- **Multi-Level Detail Reports**: Choose between 3 detail levels (Precise, Super Precise, No Details)
- **Portable Executable**: No installation required - run directly from any location without dependencies

### 📊 Report Outputs
- **📝 Word Document** (`VulnReport.docx`): 
  - Complete vulnerability details with CVSS scores
  - Embedded screenshots with automatic placement
  - Mitigation and solution recommendations
  - Professional formatting with headers and tables
  
- **📈 Excel Spreadsheet** (`Table.xlsx`):
  - Tabular vulnerability summary by host
  - Color-coded severity levels
  - CVSS scores and risk ratings
  - Solution/mitigation column
  - Styled headers and borders
  
- **📄 Text Summary** (`Summary.txt`):
  - Clean, structured vulnerability listing
  - Host-based organization
  - Quick reference format

### 🖥️ Modern GUI Features
- **Real-time Progress Tracking**: Live progress bar with percentage updates during processing
- **Interactive Console**: Color-coded log messages (Success: Green, Warning: Orange, Error: Red)
- **Immediate Cancellation**: Stop execution instantly with the Cancel button
- **Read-only File Paths**: Force users to select files via dialogs for error prevention
- **Visual Feedback**: Hover effects on buttons with darker colors when disabled
- **Dark Theme Interface**: Professional dark UI with custom color scheme

### ⚡ Advanced Features
- **Multi-threaded Processing**: Background execution prevents GUI freezing
- **Progress Callbacks**: Each processing stage reports progress individually
- **Graceful Error Handling**: FileNotFoundError and missing file handling
- **Natural Sorting**: Images sorted intelligently (img1, img2, img10 instead of img1, img10, img2)
- **Automatic Directory Creation**: Creates output folders automatically
- **PyInstaller Ready**: Easy compilation to standalone executable

---

## 📖 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum (8GB recommended for large reports)
- **Storage**: 500MB free space for dependencies and Tesseract

### Required Tools
- **Tesseract OCR**: Already included in `tesseract/` directory for Windows builds
  - For manual installation: [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)
- **GVM/OpenVAS**: To generate initial vulnerability reports

---

## 🔨 Installation

### Option 1: From Source

1. **Clone the repository**
```bash
git clone https://github.com/RaymundoBaca/GVM-Report-Builder.git
cd GVM-Report-Builder
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python GVM_Report_Builder.py
```

### Option 2: Standalone Executable

1. **Download** the latest release from [Releases](https://github.com/RaymundoBaca/GVM-Report-Builder/releases)
2. **Extract** the ZIP file
3. **Run** `GVM Report Builder.exe` (Windows) - No installation required!

---

## 🎮 Usage

### Step-by-Step Guide

1. **Launch the Application**
   ```bash
   python GVM_Report_Builder.py
   ```
   Or double-click `GVM Report Builder.exe` if using the compiled version.

2. **Select Detail Level**
   - **1 - Precise**: Detailed vulnerability descriptions with context
   - **2 - Super Precise**: Maximum detail including all technical information
   - **3 - No Details**: Summary only, minimal descriptions

3. **Select Your PDF Report**
   - Click `Browse PDF` button
   - Navigate to your GVM/OpenVAS PDF export

4. **Select Your TXT Report**
   - Click `Browse TXT` button
   - Navigate to your GVM/OpenVAS TXT export

5. **Select Output Folder** (Optional)
   - Click `Select` button to choose custom output location
   - Default: `Results/` folder in application directory

6. **Run Processing**
   - Click `Run` button
   - Monitor real-time progress in the console
   - Watch the progress bar advance through each stage
   - Button turns dark and shows "Running..." while processing

7. **Cancel Anytime**
   - Click `Cancel` button to stop execution immediately
   - All progress will be lost

### Processing Stages

The application processes reports through **9 sequential stages**:

| Stage | Script | Description | Progress |
|-------|--------|-------------|----------|
| 1 | `rAI1_0.py` | Extract images from PDF | 0-11% |
| 2 | `rAI1_1.py` | Process and filter images | 11-22% |
| 3 | `rAI1_2.py` | Classify images by color | 22-33% |
| 4 | `rAI1_3.py` | Rename and organize images | 33-44% |
| 5 | `rAI1_4.py` | OCR text extraction | 44-55% |
| 6 | `rAI2_x.py` | Parse vulnerabilities (level-dependent) | 55-66% |
| 7 | `rAI2_5.py` | Host-based analysis | 66-77% |
| 8 | `rAI3.py` | Generate Excel table | 77-88% |
| 9 | `rAI4.py` | Generate Word report | 88-99% |
| 10 | `rAI5.py` | Generate text summary | 99-100% |

---

## 📸 Screenshots

<div align="center">

### Main Interface

<img width="541" height="451" alt="image1" src="https://github.com/user-attachments/assets/86687d25-3ca6-42d1-b9e4-3e8569860cb6"/>

*Modern dark-themed GUI with intuitive file selection and real-time progress tracking*

### Processing in Action

<img width="541" height="451" alt="image2" src="https://github.com/user-attachments/assets/2531a505-8ec6-4c6e-912b-8fd8cd37d3fb"/>

*Live console output with color-coded messages (Success: Green, Warning: Orange, Error: Red)*

### Generated Reports Preview

<img width="1144" height="512" alt="image3" src="https://github.com/user-attachments/assets/ee514781-8a61-4e5d-a56a-7d3467105427"/>

*Professional Word, Excel, and Text output files ready for client delivery*

</div>

---

## 📊 Report Generation Levels

### Level 1: Precise
- **Best for**: Standard penetration test reports
- **Detail**: Comprehensive vulnerability descriptions
- **Use case**: Client deliverables requiring technical depth

### Level 2: Super Precise
- **Best for**: Detailed technical audits
- **Detail**: Maximum information including all detection methods
- **Use case**: Internal security team reviews

### Level 3: No Details
- **Best for**: Executive summaries
- **Detail**: Vulnerability names and CVSS scores only
- **Use case**: High-level management reports

---

## 📁 Output Files

After successful processing, you'll find these files in your output directory:

```
Results/
├── 📄 Summary.txt           # Clean text summary of vulnerabilities
├── 📊 Table.xlsx            # Excel spreadsheet with color-coded severity
├── 📝 VulnReport.docx           # Professional Word document with images
```

### File Descriptions

#### `Summary.txt`
- Structured vulnerability list
- Organized by host IP
- Includes CVSS scores, severity, and mitigation steps
- Plain text format for easy searching

#### `Table.xlsx`
- Excel spreadsheet with professional styling
- Columns: Host, Vulnerability Name, CVSS Score, Severity, Solution
- Color-coded rows by severity
- Filterable and sortable data

#### `Report.docx`
- Complete Word document
- Title page with scan metadata
- Vulnerability sections with:
  - Host information
  - CVSS score and severity rating
  - Detailed description
  - Impact assessment
  - Remediation steps
  - Embedded screenshots
- Professional formatting with headers and page breaks

---

## 🏗️ Building Executable

### Using PyInstaller

**For Windows:**

```bash
pyinstaller --onefile --noconsole --icon=favicon.ico --add-data "Hackalotl.png;." --add-data "favicon.ico;." --add-data "sc;sc" --add-data "tesseract;tesseract" GVM_Report_Builder.py
```

**For Linux/macOS:**

```bash
pyinstaller --onefile --noconsole --icon=favicon.ico --add-data "Hackalotl.png:." --add-data "favicon.ico:." --add-data "sc:sc" --add-data "tesseract:tesseract" GVM_Report_Builder.py
```

**Important Notes:**
- Use `;` as separator on Windows, `:` on Linux/macOS
- `--add-data "sc;sc"` includes all processing scripts
- `--add-data "tesseract;tesseract"` bundles OCR engine
- The executable will be in `dist/GVM Report Builder.exe`
- First build may take several minutes to bundle all dependencies

---

## 📂 Project Structure

```
GVM-Report-Builder/
├── 📄 GVM_Report_Builder.py      # Main GUI application
├── 📄 requirements.txt           # Python dependencies
├── 📄 README.md                  # This file
├── 🖼️ Hackalotl.png              # Main application mascot
├── 🎨 favicon.ico                # Application icon (Windows)
│
├── 📁 sc/                       # Processing scripts package
│   ├── rAI1_0.py                # PDF image extraction
│   ├── rAI1_1.py                # Image filtering
│   ├── rAI1_2.py                # Color classification
│   ├── rAI1_3.py                # Image renaming/organization
│   ├── rAI1_4.py                # OCR processing
│   ├── rAI2_1.py                # Vulnerability parsing (Precise)
│   ├── rAI2_2.py                # Vulnerability parsing (Super Precise)
│   ├── rAI2_3.py                # Vulnerability parsing (No Details)
│   ├── rAI2_5.py                # Host-based grouping
│   ├── rAI3.py                  # Excel generation
│   ├── rAI4.py                  # Word report generation
│   └── rAI5.py                  # Delete leftover files
│
└── 📁 tesseract/                 # OCR Engine (Windows)
    ├── tesseract.exe
    ├── *.dll                    # Required libraries
    └── tessdata/                # Language data files
```

**Note**: When running the application, it will automatically create a `Results/` folder for output files.

---

## 🔬 Technical Details

### Technologies Used
- **PySide6**: Modern Qt6 bindings for Python GUI
- **PyMuPDF (fitz)**: PDF manipulation and image extraction
- **Pillow (PIL)**: Image processing and analysis
- **pytesseract**: OCR text extraction wrapper
- **python-docx**: Word document generation
- **openpyxl**: Excel file creation and styling
- **pandas**: Data manipulation and analysis
- **natsort**: Natural sorting for filenames

### Architecture

#### Threading Model
- **Main Thread**: GUI event loop and user interactions
- **Worker Thread**: Background script execution (daemon)
- **Signal/Slot Communication**: Thread-safe GUI updates

#### Progress Tracking System
- Each script reports internal progress (0.0 to 1.0)
- Main app calculates global progress: `(script_index / 9) * 100 + (internal_progress / 9) * 100`
- Real-time updates via `QApplication.processEvents()`

#### Cancellation Mechanism
- Custom `CancelledException` raised on user cancel
- Checked in progress callbacks and log wrappers
- Immediate propagation through call stack

#### Error Handling
- Try-except blocks around file operations
- Defensive `exists()` checks before file access
- User-friendly error messages in GUI
- Detailed stack traces in console output

### Key Code Patterns

**Progress Callback**:
```python
def update_progress(progress):
    if self.cancelled:
        raise CancelledException("User cancelled")
    # progress: 0.0 to 1.0
    self.progress_signal.emit(int(progress * 100))
    QApplication.processEvents()
```

**Log Wrapper**:
```python
def log_wrapper(message, type_="info"):
    if self.cancelled:
        raise CancelledException("User cancelled")
    self.log_signal.emit(message, type_)
    QApplication.processEvents()
```

**Event Filter for Hover Effects**:
```python
def eventFilter(self, obj, event):
    if not obj.isEnabled():
        return super().eventFilter(obj, event)
    # Apply hover styling...
```

---

## 🐛 Troubleshooting

### Common Issues

#### "Module 'sc' not found"
**Solution**: Make sure you're running from the project root directory where `sc/` folder exists.

#### "Tesseract not found"
**Solution**: 
- For source install: Install Tesseract OCR system-wide
- For .exe: Ensure `tesseract/` folder is in same directory as executable

#### Images not appearing in Word report
**Solution**: 
- Check that PDF contains actual images (not just screenshots)
- Verify images are extracted to `tablas_png/` folder
- Ensure images follow naming convention: `color_number.png`

#### Progress bar stuck at certain percentage
**Solution**: 
- Check console for error messages
- Verify input files are valid GVM/OpenVAS exports
- Try with smaller test report first

#### GUI freezes or becomes unresponsive
**Solution**: 
- This shouldn't happen with current threading implementation
- If it does, click Cancel and restart
- Check if you're using the latest version

#### Excel file won't open
**Solution**: 
- Ensure OpenPyXL is installed: `pip install openpyxl`
- Check that output directory is writable
- Close any existing Excel instance that might lock the file

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/RaymundoBaca/GVM-Report-Builder.git
cd GVM-Report-Builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest  # Optional: code formatting and testing

# Run the application
python GVM_Report_Builder.py
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic sections

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**José Raymundo Baca Hernández**

- 🐙 GitHub: [@RaymundoBaca](https://github.com/RaymundoBaca)
- 📧 Email: ray.mundo@outlook.es
- 💼 LinkedIn: [RaymundoBaca](https://www.linkedin.com/in/RaymundoBaca)

---

## 🙏 Acknowledgments

- **Greenbone/OpenVAS** team for the vulnerability scanning framework
- **Tesseract OCR** project for text extraction capabilities
- **PySide6/Qt** team for the excellent GUI framework
- **Python-docx** maintainers for Word document generation
- All contributors who help improve this tool

---

## 🔮 Future Enhancements

- [ ] Support for additional vulnerability scanners (Nessus, Qualys)
- [ ] Customizable report templates
- [ ] Vulnerability trend analysis and charts
- [ ] Multi-language support

---

## 📞 Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/RaymundoBaca/GVM-Report-Builder/issues)
3. Open a [new issue](https://github.com/RaymundoBaca/GVM-Report-Builder/issues/new) with:
   - Detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, Python version)

---

<p align="center">
  <img src="favicon.ico" width="200">
  <br>
  <em>Built with ❤️ for security professionals</em>
</p>

---

**⭐ If you find this tool useful, please consider giving it a star on GitHub!**
