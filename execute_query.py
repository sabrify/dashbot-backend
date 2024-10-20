import os
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate
from langchain_openai.embeddings import OpenAIEmbeddings  

# Load environment variables where APIs are stored
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")

# Set up the model
model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")

# Set up the parser
parser = StrOutputParser()


# Create the PineconeVectorStore retriever (connect to the existing index)
index_name = "rag-index"
namespace = 'product'
pinecone_vector_store = PineconeVectorStore(
    index_name=index_name, namespace=namespace, embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
)

# Create the prompt template
template = """
You are an intelligent Shopify merchant assistant that provides helpful, accurate, and concise answers based on the Shopify merchant's needs.
Instructions:
1. Answer the question based on the context provided.
2. If the context is insufficient, respond with "I don't know," and suggest possible actions the merchant can take to find more information.
3. After answering the merchant's question, ask if they would like additional tips or recommendations related to Shopify store performance improvements.


Context: {context}

Question: {question}
"""

prompt = ChatPromptTemplate.from_template(template)

# Build the chain with retriever, prompt, model, and parser
chain = (
    {"context": pinecone_vector_store.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | model
    | parser
)

response = chain.invoke("How many sales did we make")
print(response)
