import os
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def process_website(url, user_id, store_name="default"):
    
    docs = []
    
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        if not docs:
            return None
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        chunks = text_splitter.split_documents(docs)
        
        if not chunks:
            return None
        
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        persist_directory = f"vector_store/{user_id}_{store_name}"
        os.makedirs(persist_directory, exist_ok=True)
        
        vector_store = Chroma.from_documents(
            chunks, 
            embeddings,
            persist_directory=persist_directory,
            collection_name=f"{user_id}_{store_name}"
        )
        
        return vector_store
    
    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return None