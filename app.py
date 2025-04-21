import streamlit as st
import re
from urllib.parse import urlparse
import cloudscraper
from bs4 import BeautifulSoup
import time
import random
import google.generativeai as genai
import os
from tqdm import tqdm
import backoff
import tempfile
from pathlib import Path

st.set_page_config(page_title="URL Extraction and Citation Formatter", layout="wide")

# Functions from original script
def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ]
    return random.choice(user_agents)

@backoff.on_exception(
    backoff.expo,
    (Exception),  # Catch all exceptions for cloudscraper
    max_tries=3,
    jitter=backoff.full_jitter
)
def scrape_url_content(url):
    """Scrape content from URL with automatic retries and exponential backoff."""
    # Create a cloudscraper session
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # Basic rate limiting
    time.sleep(random.uniform(2, 4))
    
    response = scraper.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
        
    # Get text content
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    text = ' '.join(line for line in lines if line)
    
    return text

@backoff.on_exception(
    backoff.constant,  # Use constant backoff for Gemini API
    Exception,  # This will catch any Gemini API errors
    interval=60,  # Wait 60 seconds between retries
    max_tries=3,
    jitter=backoff.full_jitter
)
def extract_author_and_year(content, url, api_key):
    """Extract author and year information using Gemini with automatic retries."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel()
    
    if not content:
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].title(), 'Unknown'
        
    prompt = f"""Given this webpage content from {url}, extract the following information:
1. Author name (if available)
2. Publication year (4-digit year, e.g. 2024)

If you can't find the information, respond with 'Unknown' for that field.
Format your response exactly like this example:
Author: John Doe
Year: 2024

Keep only the name of the main author. Add et al. if there are multiple authors.

Content:
{content[:10000]}
"""
    
    # Basic rate limiting for Gemini API
    time.sleep(4)
    
    response = model.generate_content(prompt)
    response_text = response.text
    
    # Parse the response
    author_match = re.search(r'Author: (.+)', response_text)
    year_match = re.search(r'Year: (.+)', response_text)
    
    author = author_match.group(1) if author_match else None
    year = year_match.group(1) if year_match else None
    
    # Fallbacks if Gemini couldn't find the information
    if not author or author == 'Unknown':
        domain = urlparse(url).netloc
        author = domain.replace('www.', '').split('.')[0].title()
    
    if not year or year == 'Unknown':
        year_match = re.search(r'/(\d{4})/', url)
        year = year_match.group(1) if year_match else 'Unknown'
        
    return author.strip(), year.strip()

def extract_urls(url, api_key):
    """return the author and publication year of the url, or a fallback if scraping fails"""
    try:
        # get the content of the url
        content = scrape_url_content(url)
        # extract the author and publication year with gemini
        author, year = extract_author_and_year(content, url, api_key)
    except Exception as e:
        st.error(f"Skipping {url} due to error: {str(e)}")
        # Fallback: use domain name as author
        domain = urlparse(url).netloc
        author = domain.replace('www.', '').split('.')[0].title()
        year = 'Unknown'
    
    # Format the output as a markdown citation with author, year, and URL
    formatted_output = f"([{author}, {year}]({url}))"
    return formatted_output

def extract_urls_from_text(text, api_key):
    """Extract URLs from text and format citations"""
    lines = text.split('\n')
    new_lines = []
    just_author_years = []
    
    progress_bar = st.progress(0)
    
    for i, line in enumerate(lines):
        # Update progress
        progress_bar.progress((i + 1) / len(lines))
        
        # Extract URL from the line using regex
        url_match = re.search(r'https?://[^\s,)]+', line.strip())
        url = url_match.group(0) if url_match else None
        if url:
            with st.spinner(f"Processing URL: {url}"):
                author_year = extract_urls(url, api_key)
                line = line.replace(url, author_year)
                new_lines.append(line)
                just_author_years.append(author_year)
        else:
            new_lines.append(line)
            just_author_years.append(None)
    
    progress_bar.empty()
    return '\n'.join(new_lines), just_author_years

def replace_sources_with_author_year(body_text, just_author_years):
    """Replace source numbers with author/year citations"""
    for source_i, author_year in enumerate(just_author_years):
        if author_year:
            pattern = rf'X{source_i + 1}\b'
            body_text = re.sub(pattern, author_year + '.', body_text)
    return body_text

def split_the_body(body_text, custom_string):
    """Split the body text and sources"""
    lines = body_text.split('\n')
    
    # Find the line that starts with the custom string
    split_index = -1
    for i, line in enumerate(lines):
        if custom_string in line:
            split_index = i
            break
    
    if split_index == -1:
        return body_text, ""
    
    body = '\n'.join(lines[:split_index])
    sources = '\n'.join(lines[split_index+1:])
    
    # Filter out empty lines from sources
    sources_lines = [line for line in sources.split('\n') if line.strip()]
    sources = '\n'.join(sources_lines)
    
    return body, sources

@backoff.on_exception(
    backoff.constant,  # Use constant backoff for Gemini API
    Exception,  # This will catch any Gemini API errors
    interval=60,  # Wait 60 seconds between retries
    max_tries=3,
    jitter=backoff.full_jitter
)
def add_x_to_source_numbers(text, api_key):
    """
    Use Gemini 2.5 Pro to add an X before source reference numbers in text.
    This makes it easier to identify and replace source numbers later.
    """
    prompt = f"""
    recopy entirely the following text by adding an X just before all the numbers that are representing sources.

    For example "AI Safety Support Links 272" should become "AI Safety Support Links X272"

    but "AI Management Systems (e.g., ISO 42001)" should remain "AI Management Systems (e.g., ISO 42001)"


    {text}
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-pro")
    
    # Basic rate limiting for Gemini API
    time.sleep(4)
    
    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.title("URL Extraction and Citation Formatter")

# Gemini API Key input (with masking)
api_key = st.text_input("Enter your Gemini API Key", type="password")

with st.expander("Instructions", expanded=True):
    st.markdown("""
    This app helps format citations from Google Deep Research:
    1. Paste your research content in the 'Input Body' text area.
    2. Enter the marker text that identifies where the reference section begins (e.g., 'Sources des citations').
    3. The app will extract URLs, determine authors and years, and format the citations.
    4. You can download the formatted output files when processing is complete.
    """)

# Input options
tab1, tab2 = st.tabs(["Direct Text Input", "File Upload"])

with tab1:
    body_text = st.text_area("Input Body (Paste your research text here), in markdown format, with the references at the end of the text", height=300)
    reference_marker = st.text_input("Reference Section Marker", value="Sources des citations")
    preprocess_text = st.checkbox("Preprocess text to add 'X' before source numbers", value=True, help="Uses Gemini to add an 'X' before source numbers to make them easier to identify")
    
    if st.button("Process Text", disabled=not api_key):
        if body_text:
            with st.spinner("Processing document..."):
                # Split the body
                body, sources = split_the_body(body_text, reference_marker)
                
                # Preprocess body to add X before source numbers if requested
                if preprocess_text:
                    with st.spinner("Preprocessing text with Gemini..."):
                        body = add_x_to_source_numbers(body, api_key)
                
                # Process sources
                if sources:
                    formatted_sources, author_years = extract_urls_from_text(sources, api_key)
                    
                    # Replace references in body
                    formatted_body = replace_sources_with_author_year(body, author_years)
                    
                    # Display results
                    st.subheader("Formatted Body")
                    st.text_area("Formatted Body Content", value=formatted_body, height=300)
                    st.download_button("Download Formatted Body", formatted_body, "output_body.md")
                    
                    st.subheader("Formatted Sources")
                    st.text_area("Formatted Sources", value=formatted_sources, height=300)
                    st.download_button("Download Formatted Sources", formatted_sources, "output_sources.md")
                else:
                    st.error(f"Could not find the reference marker '{reference_marker}' in the text.")
        else:
            st.error("Please enter input text.")

with tab2:
    uploaded_file = st.file_uploader("Upload a Markdown File", type=["md", "txt"])
    reference_marker = st.text_input("Reference Section Marker ", value="Sources des citations")
    preprocess_text = st.checkbox("Preprocess file to add 'X' before source numbers", value=True, help="Uses Gemini to add an 'X' before source numbers to make them easier to identify")
    
    if uploaded_file is not None and st.button("Process File", disabled=not api_key):
        with st.spinner("Processing file..."):
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name
            
            # Read the file
            with open(temp_path, 'r') as file:
                file_content = file.read()
            
            # Split the body
            body, sources = split_the_body(file_content, reference_marker)
            
            # Preprocess body to add X before source numbers if requested
            if preprocess_text:
                with st.spinner("Preprocessing text with Gemini..."):
                    body = add_x_to_source_numbers(body, api_key)
                
            # Process sources
            if sources:
                formatted_sources, author_years = extract_urls_from_text(sources, api_key)
                
                # Replace references in body
                formatted_body = replace_sources_with_author_year(body, author_years)
                
                # Display results
                st.subheader("Formatted Body")
                st.text_area("Formatted Body Content", value=formatted_body, height=300)
                st.download_button("Download Formatted Body", formatted_body, "output_body.md")
                
                st.subheader("Formatted Sources")
                st.text_area("Formatted Sources", value=formatted_sources, height=300)
                st.download_button("Download Formatted Sources", formatted_sources, "output_sources.md")
            else:
                st.error(f"Could not find the reference marker '{reference_marker}' in the text.")
            
            # Clean up temporary file
            os.unlink(temp_path) 