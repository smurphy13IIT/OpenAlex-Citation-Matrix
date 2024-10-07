import requests
import json

# Set the base URL for OpenAlex API
base_url = "https://api.openalex.org/"

# Set the endpoint for a specific entity (e.g., works, authors, concepts, venues, institutions)
# This example fetches works by a specific author ID
source_endpoint = "sources/"

# Perform the GET request
issn_query = "issn:1547-7185"
source_url = f"{base_url}{source_endpoint}{issn_query}"
response = requests.get(source_url)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Print the JSON response
    json_formatted_str = json.dumps(data, indent=2)
    print(json_formatted_str)
    print(source_url)

else:
    print(f"Error: {response.status_code}")