from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import hashlib
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import JSONLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables where APIs are stored
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/upsert")
def upsert_documents():
    # Initialize Pinecone
    pinecone = Pinecone(os.getenv("PINECONE_API_KEY"))
    cloud = os.environ.get('PINECONE_CLOUD') or 'aws'
    region = os.environ.get('PINECONE_REGION') or 'us-east-1'
    spec = ServerlessSpec(cloud=cloud, region=region)                                                           

    # Load the JSON file
    loader = JSONLoader(file_path="product.json", jq_schema=".", text_content=False)
    json_docs = loader.load()

    # Set up embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    # Generate unique stable IDs using a hash function based on the document content
    for doc in json_docs:
        doc_content = str(doc.page_content)  # or use any unique identifier within the document
        doc_hash = hashlib.md5(doc_content.encode('utf-8')).hexdigest()
        doc.metadata['id'] = f'doc-{doc_hash}'

    # Pinecone index setup
    index_name = "rag-index"
    namespace = 'product'
    if index_name not in pinecone.list_indexes().names():
        pinecone.create_index(
            name=index_name,
            dimension=embeddings.dimension,
            metric="cosine",
            spec=spec,
        )
        while not pinecone.describe_index(index_name).status['ready']:
            time.sleep(1)

    # Directly upsert all documents into Pinecone (no duplicate check)
    pinecone_vector_store = PineconeVectorStore.from_documents(
        json_docs, embeddings, index_name=index_name, namespace=namespace)

    return {"message": "Documents upserted successfully"}


@app.post("/query")
def query_documents(request: QueryRequest):
    question = request.question

    # Set up the model
    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")

    # Set up the parser
    parser = StrOutputParser()

    # Create the PineconeVectorStore retriever (connect to the existing index)
    index_name = "mvp"
    namespace = 'shopify'
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

    # Invoke the chain to get the response
    response = chain.invoke(question)
    
    return {"answer": response}