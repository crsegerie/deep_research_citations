# Markdown Citation Processor

This script processes markdown files containing citations and their sources, transforming them into a more readable format with author information and proper links. It uses Google's Gemini AI to extract information about the sources.

## Features

- Extracts citations from markdown text
- Processes source URLs to get author and publication year information
- Shows progress with a progress bar
- Transforms citations into a `[Author, Year](URL)` format
- Preserves original markdown structure

## Requirements

- Python 3.7+
- Google Gemini API key
- Required Python packages (install using `requirements.txt`)

## Installation

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

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

The script will transform citations into the format:
```markdown
text ([Author, Year](URL))
``` 