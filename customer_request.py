import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the access token from environment variables
token = os.getenv('SHOPIFY_ACCESS_TOKEN')
app_secret = os.getenv('SHOPIFY_APP_SECRET')

# Define the Shopify GraphQL API endpoint
url = 'https://mvptestingstore.myshopify.com/admin/api/2024-10/graphql.json'

# Define the GraphQL query for customers
query = '''
query GetCustomers($first: Int!, $after: String) {
  customers(first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        firstName
        lastName
        email
        phone
        numberOfOrders
        amountSpent {
          amount
          currencyCode
        }
        createdAt
        updatedAt
        note
        verifiedEmail
        validEmailAddress
        tags
        lifetimeDuration
        defaultAddress {
          formattedArea
          address1
        }
        addresses {
          address1
        }
        image {
          src
        }
        canDelete
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
    'after': None  # Initial request
}

# Define the request headers, including the access token
headers = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': token,
    'X-Shopify-App-Secret': app_secret  # Include the app secret key if required
}

# Load existing data from customer.json, if it exists and not empty
try:
    if os.path.getsize("customer.json") > 0:
        with open("customer.json", "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = {"data": {"customers": {"edges": []}}, "pageInfo": {}}
except (FileNotFoundError, json.JSONDecodeError):
    existing_data = {"data": {"customers": {"edges": []}}, "pageInfo": {}}

# Get existing customer IDs to avoid duplicates
existing_ids = {customer["node"]["id"] for customer in existing_data["data"]["customers"]["edges"]}

# Pagination loop to fetch all customers
while True:
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

    # Process the response
    if response.status_code == 200:
        try:
            new_data = response.json()
            customers = new_data["data"]["customers"]["edges"]

            # Append only unique customers
            for customer in customers:
                if customer["node"]["id"] not in existing_ids:
                    existing_data["data"]["customers"]["edges"].append(customer)
                    existing_ids.add(customer["node"]["id"])

            # Update pageInfo in the JSON file
            existing_data["pageInfo"] = new_data["data"]["customers"]["pageInfo"]

            # Check if there's another page of customers
            if new_data["data"]["customers"]["pageInfo"]["hasNextPage"]:
                variables["after"] = new_data["data"]["customers"]["pageInfo"]["endCursor"]
            else:
                break
        except json.JSONDecodeError:
            print("Failed to decode JSON. Raw response:", response.text)
            break
    else:
        print(f"Query failed with code {response.status_code}: {response.text}")
        break

# Save updated data, including pageInfo, to customer.json
with open("customer.json", "w") as file:
    json.dump(existing_data, file, indent=4)
print("Customer data with pageInfo saved to customer.json without duplicates.")
