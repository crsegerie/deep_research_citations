# Markdown Citation Processor

This script processes markdown files containing citations and their sources, transforming citations in the body text into a more readable format with author information and proper links. It uses Google's Gemini AI to intelligently extract author and publication year information from webpage content.

## Features

- Extracts citations from markdown text
- Uses Gemini AI to intelligently extract author and publication year information
- Shows progress with a progress bar
- Transforms citations into a `[Author, Year](URL)` format
- Preserves the original sources section
- Smart fallbacks if Gemini can't find information (uses domain name as author)

## Requirements

- Python 3.7+
- Google Gemini API key
- Required Python packages (install using `requirements.txt`):
  - google-generativeai
  - requests
  - beautifulsoup4
  - tqdm
  - lxml

## Installation

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Usage

Run the script using:

```bash
python process_citations.py input_file.md output_file.md --api-key YOUR_GEMINI_API_KEY
```

### Arguments

- `input_file.md`: Path to your input markdown file
- `output_file.md`: Path where the processed markdown will be saved
- `--api-key`: Your Google Gemini API key

## Input Format

The input markdown should have:
1. Citations in the text as superscript numbers (e.g., "text6")
2. A sources section at the end with the following format:

```markdown
### **Sources des citations**

1. Title, URL
2. Title, URL
...
```

## Output Format

The script will:
1. Transform citations in the body text into the format: `text ([Author, Year](URL))`
2. Leave the sources section unchanged
3. Use Gemini AI to:
   - Extract author names from webpage content
   - Identify publication years
   - Fall back to domain name as author if not found
   - Use "Unknown" for year if not found 