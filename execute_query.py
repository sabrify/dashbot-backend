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
Answer the question based on the context below. If you can't 
answer the question, reply "I don't know".

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

response = chain.invoke("What is the first product?")
print(response)
