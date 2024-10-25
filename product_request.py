import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve Shopify API token
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
app_secret = os.getenv('SHOPIFY_APP_SECRET')

# Shopify GraphQL API endpoint
url = 'https://mvptestingstore.myshopify.com/admin/api/2024-10/graphql.json'

# Define the GraphQL query for products
query = '''
query GetProducts($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        title
        createdAt
        updatedAt
        variants(first: 10) {
          edges {
            node {
              id
              title
              sku
              price
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
'''

# Initialize variables for pagination
variables = {
    'first': 100,
    'after': None
}

# Request headers
headers = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': token,
    'X-Shopify-App-Secret': app_secret  # Include the app secret key if required
}

# Load existing data from products.json, if available and not empty
try:
    if os.path.getsize("products.json") > 0:  # Check if file is not empty
        with open("products.json", "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = {"data": {"products": {"edges": []}}, "pageInfo": {}}
except (FileNotFoundError, json.JSONDecodeError):
    existing_data = {"data": {"products": {"edges": []}}, "pageInfo": {}}

# Track existing product IDs to avoid duplicates
existing_ids = {product["node"]["id"] for product in existing_data["data"]["products"]["edges"]}

# Pagination loop to fetch all products
while True:
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    
    # Process the response
    if response.status_code == 200:
        try:
            new_data = response.json()
            products = new_data["data"]["products"]["edges"]

            # Append only unique products
            for product in products:
                if product["node"]["id"] not in existing_ids:
                    existing_data["data"]["products"]["edges"].append(product)
                    existing_ids.add(product["node"]["id"])

            # Update pageInfo in the JSON file
            existing_data["pageInfo"] = new_data["data"]["products"]["pageInfo"]

            # Check if there's another page of products
            if new_data["data"]["products"]["pageInfo"]["hasNextPage"]:
                variables["after"] = new_data["data"]["products"]["pageInfo"]["endCursor"]
            else:
                break
        except json.JSONDecodeError:
            print("Failed to decode JSON. Raw response:", response.text)
            break
    else:
        print(f"Query failed with code {response.status_code}: {response.text}")
        break

# Save updated data, including pageInfo, to products.json
with open("products.json", "w") as file:
    json.dump(existing_data, file, indent=4)
print("Product data with pageInfo saved to products.json without duplicates.")
