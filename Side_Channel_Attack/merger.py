import os
import json
import gdown
import shutil

# Manually specify the direct Google Drive links to .json files here
JSON_FILE_LINKS = [
    "https://drive.google.com/file/d/18qKwKByMUlttW3DRiirpd9d3RlUogrXd/view?usp=drive_link", # 2005001
    "https://drive.google.com/file/d/1h9cKWcnMTU3YyfZqTw1ZzGNMLYQ-pGE3/view?usp=drive_link", # 2005004
    "https://drive.google.com/file/d/1LFo-NZRmR5HMU241-3SQPBgqfyH7ZxR6/view?usp=drive_link", # 2005005
    "https://drive.google.com/file/d/1JA23_iGYSZtzEFO1SROXEeWHXx-Ldniz/view?usp=drive_link", # 2005006
    "https://drive.google.com/file/d/1ABQVHDR_ZK8-aeuv2gi8sgIgMBvnXn4U/view?usp=drive_link", # 2005017
    "https://drive.google.com/file/d/1U6tHzOO3jwqN70esv1Z9UULcJt0epfeD/view?usp=drive_link", # 2005020
    "https://drive.google.com/file/d/1bsN1pBFyq4SowP9VVO6zPXGdiQdV0edl/view?usp=drive_link", # 2005021
    "https://drive.google.com/file/d/12BpZGllel0qt2rKHXlxlw4aCZZS_I-dO/view?usp=drive_link", # 2005027
    "https://drive.google.com/file/d/14JsM7Aa2Up1XQEBVc50q8tYYBeMxLCKE/view?usp=drive_link", # 2005045
    "https://drive.google.com/file/d/1DEvR7nvmg6JOwkRKD1CSUibT56VoO8Jq/view?usp=drive_link", # 2005055
    "https://drive.google.com/file/d/18PGcg-ugN3wGsCRiHw2EPXtSxPp65coV/view?usp=drive_link", # 2005067
    "https://drive.google.com/file/d/1vYBG0p7unmQJBqSzDvl-HRnRoTssw26u/view?usp=drive_link", # 2005070
    "https://drive.google.com/file/d/1Rw__6xl7yd21mgIzMXrGqns8BdoDlvL2/view?usp=drive_link", # 2005077
    "https://drive.google.com/file/d/1g9oJ9PBsOBGHjfbY8qp5BjlBsGgAaO71/view?usp=drive_link", # 2005084
    "https://drive.google.com/file/d/1uhwxNoP0TZi2dTRM6N5wdV56Lb3bVNB2/view?usp=drive_link", # 2005107
    # Add more direct .json file links as needed, e.g., "https://drive.google.com/uc?id=FILE_ID"
]

def download_json_files(file_links, output_dir="/kaggle/working/downloaded_data"):
    """Download .json files from provided Google Drive links."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    downloaded_files = []
    
    for i, link in enumerate(file_links):
        output_file = os.path.join(output_dir, f"file_{i}.json")
        try:
            gdown.download(link, output_file, quiet=False, fuzzy=True)
            if os.path.exists(output_file):
                # Verify if the file is likely a valid JSON
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith('{') or content.startswith('['):
                        downloaded_files.append(output_file)
                    else:
                        print(f"Downloaded file {output_file} is not a valid JSON (likely an HTML page). Check the link: {link}")
                        os.remove(output_file)
            else:
                print(f"Failed to download file from {link}")
        except Exception as e:
            print(f"Error downloading {link}: {e}")
    
    return downloaded_files

def merge_json_files(downloaded_files):
    """Merge all .json files into a single dataset_merged.json with compact trace_data."""
    merged_data = []
    
    for json_file in downloaded_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both single dict and array of dicts
                if isinstance(data, dict) and all(key in data for key in ["website", "website_index", "trace_data"]):
                    merged_data.append(data)
                elif isinstance(data, list):
                    # Process each item in the array
                    for item in data:
                        if isinstance(item, dict) and all(key in item for key in ["website", "website_index", "trace_data"]):
                            merged_data.append(item)
                        else:
                            print(f"Skipping item in {json_file}: Invalid structure. Expected keys: website, website_index, trace_data")
                            print(f"Item (first 500 chars): {json.dumps(item)[:500]}...")
                else:
                    print(f"Skipping {json_file}: Invalid structure. Expected dict or list of dicts with keys: website, website_index, trace_data")
                    print(f"Actual data (first 500 chars): {json.dumps(data)[:500]}...")
        except json.JSONDecodeError as e:
            print(f"Error reading {json_file}: Invalid JSON format - {e}")
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    if not merged_data:
        print("No valid JSON objects were processed.")
        return None
    
    # Write merged data to dataset_merged.json with custom formatting
    output_file = "/kaggle/working/dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[')
        for i, item in enumerate(merged_data):
            # Format each object manually for compact trace_data
            trace_data_str = f"[{','.join(map(str, item['trace_data']))}]"
            obj_str = f'{{"website":"{item["website"]}","website_index":{item["website_index"]},"trace_data":{trace_data_str}}}'
            f.write(obj_str)
            if i < len(merged_data) - 1:
                f.write(',')
        f.write(']')
    
    print(f"Merged {len(merged_data)} JSON objects into {output_file}")
    return output_file

def main():
    # Validate links
    if not JSON_FILE_LINKS:
        print("No JSON file links provided. Please update JSON_FILE_LINKS in the script.")
        return
    
    # Download the .json files
    downloaded_files = download_json_files(JSON_FILE_LINKS)
    
    if not downloaded_files:
        print("No files were downloaded. Check the provided links and their sharing permissions.")
        return
    
    # Merge the .json files
    merge_json_files(downloaded_files)
    
    # Clean up downloaded data directory
    shutil.rmtree("/kaggle/working/downloaded_data", ignore_errors=True)

if __name__ == "__main__":
    main()