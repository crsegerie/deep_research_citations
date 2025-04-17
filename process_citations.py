import re
import argparse
from pathlib import Path
import google.generativeai as genai
from tqdm import tqdm
import time

def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    return model

def extract_citations_and_sources(markdown_content):
    # Extract citations in superscript format (e.g., text6)
    citations = re.findall(r'(\w+)(\d+)', markdown_content)
    
    # Extract sources section
    sources_section = re.findall(r'### \*\*Sources des citations\*\*\n\n((?:.+\n)+)', markdown_content)
    if not sources_section:
        return [], {}
    
    # Extract URLs from sources
    sources = {}
    for line in sources_section[0].split('\n'):
        if line.strip():
            match = re.match(r'(\d+)\.\s+(.+),\s+(https?://\S+)', line)
            if match:
                number, title, url = match.groups()
                sources[number] = {'title': title.strip(), 'url': url.strip()}
    
    return citations, sources

def get_url_info(model, url):
    prompt = f"""Given this URL: {url}
    Please provide the following information in a concise format:
    1. Author name (if available)
    2. Publication year
    If you can't find the exact information, respond with 'Unknown' for that field.
    Format: Author, Year"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error processing URL: {e}")
        return "Unknown, Unknown"

def process_markdown(input_file, output_file, api_key):
    # Read input markdown
    content = Path(input_file).read_text()
    
    # Extract citations and sources
    citations, sources = extract_citations_and_sources(content)
    
    # Setup Gemini
    model = setup_gemini(api_key)
    
    # Process each source with a progress bar
    processed_sources = {}
    for number, info in tqdm(sources.items(), desc="Processing sources"):
        url_info = get_url_info(model, info['url'])
        author, year = url_info.split(',')
        processed_sources[number] = {
            'author': author.strip(),
            'year': year.strip(),
            'url': info['url']
        }
        time.sleep(1)  # Rate limiting
    
    # Create new markdown content
    new_content = content
    
    # Replace citations in text
    for word, number in citations:
        if number in processed_sources:
            source = processed_sources[number]
            citation = f"{word} ([{source['author']}, {source['year']}]({source['url']}))"
            new_content = new_content.replace(f"{word}{number}", citation)
    
    # Write output
    Path(output_file).write_text(new_content)

def main():
    parser = argparse.ArgumentParser(description='Process markdown citations using Gemini')
    parser.add_argument('input_file', help='Input markdown file')
    parser.add_argument('output_file', help='Output markdown file')
    parser.add_argument('--api-key', required=True, help='Gemini API key')
    
    args = parser.parse_args()
    process_markdown(args.input_file, args.output_file, args.api_key)

if __name__ == "__main__":
    main() 