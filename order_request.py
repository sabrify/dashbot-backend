import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve Shopify API token
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
app_secret = os.getenv('SHOPIFY_APP_SECRET')

# Shopify GraphQL API endpoint
url = 'https://mvptestingstore.myshopify.com/admin/api/2024-10/graphql.json'

# Define the GraphQL query for orders
query = '''
query GetOrders($first: Int!, $after: String) {
  orders(first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        name
        createdAt
        updatedAt
        currencyCode
        totalPriceSet {
          presentmentMoney {
            amount
            currencyCode
          }
        }
        subtotalPriceSet {
          presentmentMoney {
            amount
            currencyCode
          }
        }
        customer {
          id
          firstName
          lastName
          email
        }
        lineItems(first: 10) {
          edges {
            node {
              title
              quantity
              sku
              originalUnitPrice
              variantTitle
            }
          }
        }
        shippingAddress {
          address1
          city
          zip
          country
          phone
        }
        shippingLine {
          title
          originalPriceSet {
            presentmentMoney {
              amount
              currencyCode
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

# Load existing data from orders.json, if available and not empty
try:
    if os.path.getsize("orders.json") > 0:
        with open("orders.json", "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = {"data": {"orders": {"edges": []}}, "pageInfo": {}}
except (FileNotFoundError, json.JSONDecodeError):
    existing_data = {"data": {"orders": {"edges": []}}, "pageInfo": {}}

# Track existing order IDs to avoid duplicates
existing_ids = {order["node"]["id"] for order in existing_data["data"]["orders"]["edges"]}

# Pagination loop to fetch all orders
while True:
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    
    # Process the response
    if response.status_code == 200:
        try:
            new_data = response.json()
            orders = new_data["data"]["orders"]["edges"]

            # Append only unique orders
            for order in orders:
                if order["node"]["id"] not in existing_ids:
                    existing_data["data"]["orders"]["edges"].append(order)
                    existing_ids.add(order["node"]["id"])

            # Update pageInfo in the JSON file
            existing_data["pageInfo"] = new_data["data"]["orders"]["pageInfo"]

            # Check if there's another page of orders
            if new_data["data"]["orders"]["pageInfo"]["hasNextPage"]:
                variables["after"] = new_data["data"]["orders"]["pageInfo"]["endCursor"]
            else:
                break
        except json.JSONDecodeError:
            print("Failed to decode JSON. Raw response:", response.text)
            break
    else:
        print(f"Query failed with code {response.status_code}: {response.text}")
        break

# Save updated data, including pageInfo, to orders.json
with open("orders.json", "w") as file:
    json.dump(existing_data, file, indent=4)
print("Order data with pageInfo saved to orders.json without duplicates.")
