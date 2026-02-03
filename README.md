# PaperTrail <img width="175" height="165" alt="Screenshot 2026-02-03 at 18 32 59" src="https://github.com/user-attachments/assets/af54be48-0a6d-4e20-8e9e-461400d42b32" />


A desktop citation management application that helps you organize and format academic references in multiple citation styles (Vancouver, APA, MLA).

## Features

- **Multiple Citation Styles**: Support for Vancouver, APA, and MLA formatting
- **Automatic Metadata Extraction**: Fetch citation information from URLs
- **Manual Entry**: Add citations manually with custom fields
- **Local Database**: All citations stored locally on your computer using SQLite
- **Export Options**: Save formatted bibliographies to text files
- **Live Preview**: See formatted citations before exporting
- **Cross-platform**: Works on Windows, Mac, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Download or clone this repository**
   ```bash
   git clone https://github.com/yourusername/papertrail.git
   cd papertrail
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python papertrail.py
   ```

## Usage

### Adding Citations from URLs

1. Paste a URL into the "Add Citation from URL" field
2. Click "Fetch & Add"
3. The app will automatically extract metadata (title, authors, year, etc.)
4. Citation is saved to your local database

### Adding Citations Manually

1. Fill in the fields in the "Manual Entry" section
2. At minimum, provide a title
3. Click "Add Citation"
4. Citation is saved to your local database

### Managing Citations

- **View All**: See all your citations in the list
- **Delete**: Select a citation and click "Delete Selected"
- **Clear All**: Remove all citations (with confirmation)

### Exporting Bibliography

1. Select your preferred citation style (Vancouver, APA, or MLA)
2. Click "Preview" to see formatted output
3. Click "Export to File" to save as a text file
4. Choose location and filename

## Citation Styles

### Vancouver
- Numbered citations [1], [2], etc.
- Author format: Surname Initials
- Example: `1. Smith J, Doe A. Article title. Journal Name 2024;10(2):123-45.`

### APA
- Author-date format
- Author format: Surname, Initials
- Example: `Smith, J., & Doe, A. (2024). Article title. Journal Name, 10(2), 123-45.`

### MLA
- Author-page format
- Author format: Surname, First Name
- Example: `Smith, John, et al. "Article title." Journal Name, vol. 10, no. 2, 2024, pp. 123-45.`

## Building Standalone Executable

To create a standalone executable that doesn't require Python:

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**
   ```bash
   pyinstaller --onefile --windowed papertrail.py
   ```

3. **Find your executable**
   - Windows: `dist/papertrail.exe`
   - Mac: `dist/papertrail.app`
   - Linux: `dist/papertrail`

## Data Storage

- All citations are stored in a local SQLite database file (`citations.db`)
- The database is created automatically in the same directory as the application
- Your data never leaves your computer

## Troubleshooting

**"Python not found"**
- Make sure Python is installed and added to your system PATH
- Try using `python3` instead of `python`

**Dependencies won't install**
- Try: `python -m pip install -r requirements.txt`
- Make sure you have an active internet connection

**Can't fetch metadata from URL**
- Some websites may block automated requests
- Try manual entry instead
- Check your internet connection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
