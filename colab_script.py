# Google Colab Script for SERP Data Processing and JSON Analysis

## Section 1: Install Necessary Libraries
```python
!pip install pandas openpyxl
```

## Section 2: Import Libraries and Setup Environment
```python
import os
import requests
import json
import re
import pandas as pd
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
```

## Section 3: Set API Keys
```python
SERPER_API_KEYS = [
    'Your API Key Here'  # Replace with your API keys
]
```

## Section 4: Define Utility Functions
```python
# Function to create safe filenames (removes invalid characters)
def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# Function to read keywords from a text file
def read_keywords(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    with open(file_path, 'r', encoding='utf-8') as file:
        keywords = [line.strip() for line in file.readlines()]
    return keywords

# Function to fetch SERP data and save as JSON files
def fetch_and_save_serp_data(keywords, gl="ir", autocorrect=True, batch_size=90, output_folder='serp_data'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    url = "https://google.serper.dev/search"
    key_index = 0

    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i + batch_size]
        payload = json.dumps([{"q": keyword, "gl": gl, "num": 50, "autocorrect": autocorrect} for keyword in batch])

        while key_index < len(SERPER_API_KEYS):
            headers = {
                'X-API-KEY': SERPER_API_KEYS[key_index],
                'Content-Type': 'application/json'
            }

            try:
                response = requests.post(url, headers=headers, data=payload)
                if response.status_code == 200:
                    serp_responses = response.json()

                    for j, keyword in enumerate(batch):
                        keyword_data = serp_responses[j]
                        filename = safe_filename(keyword) + '.json'
                        with open(os.path.join(output_folder, filename), 'w', encoding='utf-8') as f:
                            json.dump(keyword_data, f)
                    break
                else:
                    key_index += 1
            except requests.exceptions.RequestException as e:
                key_index += 1

            if key_index == len(SERPER_API_KEYS):
                raise Exception("All API keys exhausted. Unable to fetch data.")
```

## Section 5: Process JSON Files
```python
# Function to process JSON files and extract relevant data
def process_json_file(filename, urls_to_process, data_folder):
    local_results = []
    file_path = os.path.join(data_folder, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if "organic" in data and "searchParameters" in data:
                query = data["searchParameters"].get("q", "")
                for result in data["organic"]:
                    link = result["link"]
                    domain = urlparse(link).netloc
                    if domain in urls_to_process:
                        position = result.get("position", "")
                        title = result.get("title", "")
                        local_results.append([domain, query, position, title, link])
    except Exception as e:
        print(f"Error processing file {filename}: {e}")

    return local_results
```

## Section 6: Main Workflow
```python
from google.colab import files

# Upload keywords file
print("Please upload your keywords.txt file.")
keywords_file = files.upload()

# Upload URLs list file
print("Please upload your urls_list.xlsx file.")
urls_file = files.upload()

# Read keywords and URLs
keywords = read_keywords(next(iter(keywords_file.keys())))
urls_df = pd.read_excel(next(iter(urls_file.keys())))
urls_to_process = urls_df['URLs'].tolist()

# Fetch and save SERP data
fetch_and_save_serp_data(keywords, output_folder='serp_data')

# Process JSON files
data_folder = 'serp_data'
results = []

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(process_json_file, filename, urls_to_process, data_folder) for filename in os.listdir(data_folder) if filename.endswith('.json')]

    for future in futures:
        results.extend(future.result())

# Save results to Excel
output_file = 'domains_queries_with_details.xlsx'
df_results = pd.DataFrame(results, columns=["Domain", "Query", "Position", "Title", "Link"])
df_results.to_excel(output_file, index=False)

# Download the results
files.download(output_file)
```

## Section 7: Notes
Ensure that the following files are prepared before running the script:
1. `keywords.txt` - A text file containing the list of keywords to process.
2. `urls_list.xlsx` - An Excel file containing the list of URLs to match.
