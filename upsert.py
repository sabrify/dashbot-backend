import os
import hashlib
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import JSONLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore




# Load environment variables where APIs are stored
load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")


pinecone = Pinecone(os.getenv("PINECONE_API_KEY"))
cloud = os.environ.get('PINECONE_CLOUD') or 'aws'
region = os.environ.get('PINECONE_REGION') or 'us-east-1'
spec = ServerlessSpec(cloud=cloud, region=region)                                                          


# Load the JSON file
loader = JSONLoader(file_path="products.json", jq_schema=".", text_content=False)
json_docs = loader.load()


# Set up embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)



# Pinecone index setup
index_name = "mvp"
namespace = 'shopify'
if index_name not in pinecone.list_indexes().names():
    pinecone.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=spec,
    )
    while not pinecone.describe_index(index_name).status['ready']:
        time.sleep(1)


# Directly upsert all documents into Pinecone (no duplicate check)
pinecone_vector_store = PineconeVectorStore.from_documents(
    json_docs, embeddings, index_name=index_name, namespace=namespace)


print ("Documents upserted successfully")
