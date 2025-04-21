# URL Extraction and Citation Formatter

A Streamlit app to format citations from Google Deep Research by extracting URLs, determining authors and publication years, and formatting the citations.

## Features

- Process text directly or upload markdown files
- Extract URLs from references section
- Use Gemini API to determine authors and publication years from URLs
- Format citations in the document body
- Download the formatted output files

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Gemini API key:
   - You'll need to enter your API key in the app interface
   - Or set it as an environment variable before running the app:
     ```
     export GEMINI_API_KEY=your_api_key_here
     ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and go to:
   ```
   http://localhost:8501
   ```

3. Use the app:
   - Enter your Gemini API Key
   - Choose between direct text input or file upload
   - Input your research content
   - Enter the marker text that identifies where the reference section begins (default: "Sources des citations")
   - Click "Process Text" or "Process File"
   - View and download the formatted body and sources

## Input Format

Your input should have a marker line that separates the main content from the references section. For example:

```
Main content text with source references like X1, X2, X3...

Sources des citations
1. https://example.com/article1
2. https://example.com/article2
3. https://example.com/article3
```

The app will replace "X1", "X2", etc. with formatted citations like "([Author, Year](URL))." 