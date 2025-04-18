import re
from pathlib import Path
import argparse
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time
import google.generativeai as genai
import random

def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    return model

def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ]
    return random.choice(user_agents)

def scrape_url_content(url):
    """Scrape content from URL with error handling and rate limiting."""
    try:
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=15)
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
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return ""

def extract_info_with_gemini(model, url, content):
    """Extract author and year information using Gemini."""
    try:
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

Content:
{content[:10000]}
"""
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
            # Try to extract year from URL or default to consultation year
            year_match = re.search(r'/(\d{4})/', url)
            year = year_match.group(1) if year_match else 'Unknown'
            
        return author.strip(), year.strip()
        
    except Exception as e:
        print(f"Error processing with Gemini for {url}: {str(e)}")
        domain = urlparse(url).netloc
        return domain.replace('www.', '').split('.')[0].title(), 'Unknown'

def process_citation(citation, model):
    """Process a single citation line and return the formatted version."""
    # Extract components using regex
    pattern = r'(\d+)\.\s+(.+?)\s+\|\s+(.+?),\s+consulté le\s+(.+?),\s+(https?://\S+)'
    match = re.match(pattern, citation.strip())
    
    if not match:
        return citation
    
    number, title, source, date, url = match.groups()
    
    # Get content and extract information using Gemini
    content = scrape_url_content(url)
    author, year = extract_info_with_gemini(model, url, content)
    
    # Format the new citation
    formatted = f"{number}. {title} | {source}, consulté le {date}, {url}, ([{author}, {year}]({url}))"
    
    return formatted

def process_citations_file(input_file, output_file, api_key):
    """Process all citations in the input file and write to output file."""
    # Setup Gemini
    model = setup_gemini(api_key)
    
    # Read input file
    content = Path(input_file).read_text()
    
    # Process each line
    processed_lines = []
    for line in content.split('\n'):
        if line.strip():
            processed_line = process_citation(line, model)
            processed_lines.append(processed_line)
            print(f"Processed citation: {line[:50]}...")
    
    # Write output
    Path(output_file).write_text('\n'.join(processed_lines))

def main():
    parser = argparse.ArgumentParser(description='Process citation format')
    parser.add_argument('input_file', help='Input file containing citations')
    parser.add_argument('output_file', help='Output file for processed citations')
    parser.add_argument('--api-key', required=True, help='Gemini API key')
    
    args = parser.parse_args()
    process_citations_file(args.input_file, args.output_file, args.api_key)

if __name__ == "__main__":
    main() 