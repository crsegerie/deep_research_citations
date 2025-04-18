# %%
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time
import random
import google.generativeai as genai
import os
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

def extract_author_and_year(content, url, api_key):
    """Extract author and year information using Gemini."""
    try:
        # Configure Gemini
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

def extract_urls(url: str, api_key: str) -> tuple:
    """return the author and publication year of the url
    
    1. get the content of the url
    2. extract the author and publication year with gemini
    3. return the author and publication year
    
    """

    # get the content of the url
    content = scrape_url_content(url)

    # extract the author and publication year with gemini
    author, year = extract_author_and_year(content, url, api_key)
    
    # Format the output as a markdown citation with author, year, and URL
    formatted_output = f"([{author}, {year}]({url}))"
    return formatted_output

# %%
def extract_urls_from_file(file_path: str, api_key: str) -> list:
    """for each line in the path:
    1. extract the url
    2. use the extract_urls function to get the author and publication year
    3. replace the url in the line with output of the extract_urls function
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        # Extract URL from the line using regex
        url_match = re.search(r'https?://[^\s,)]+', line.strip())
        url = url_match.group(0) if url_match else None
        if url:
            author_year = extract_urls(url, api_key)
            line = line.replace(url, author_year)
            new_lines.append(line)
    return new_lines


# %%
def main():
    """main function"""
    api_key = os.getenv("GEMINI_API_KEY")
    file_path = "input.md"
    output_path = "output.md"
    lines = extract_urls_from_file(file_path, api_key)
    with open(output_path, 'w') as file:
        file.writelines(lines)

if __name__ == "__main__":
    main()

# %%
