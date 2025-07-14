import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import shutil

def process_documents(files, user_id, store_name="default"):
    if not files:
        return None
    
    docs = []
    temp_files = []
    
    try:
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.name}") as tmp_file:
                tmp_file.write(file.getvalue())
                temp_file_path = tmp_file.name
                temp_files.append(temp_file_path)
            
            if file.name.lower().endswith(".pdf"):
                loader = PyPDFLoader(temp_file_path)
            elif file.name.lower().endswith((".txt", ".md")):
                loader = TextLoader(temp_file_path, encoding='utf-8')
            else:
                continue
            
            file_docs = loader.load()
            
            for doc in file_docs:
                doc.metadata['source'] = file.name
            
            docs.extend(file_docs)
        
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
    
    finally:
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass

def load_vector_store(user_id, store_name="default"):
    try:
        persist_directory = f"vector_store/{user_id}_{store_name}"
        
        if not os.path.exists(persist_directory):
            return None
            
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=f"{user_id}_{store_name}"
        )
        
        if vector_store._collection.count() == 0:
            return None
            
        return vector_store
        
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        return None

def query_documents(vector_store, query, k=5):
    try:
        if not vector_store:
            return []
        
        docs = vector_store.similarity_search(query, k=k)
        return docs
    
    except Exception as e:
        print(f"Error querying documents: {str(e)}")
        return []

def delete_vector_store(user_id, store_name="default"):
    try:
        persist_directory = f"vector_store/{user_id}_{store_name}"
        
        if os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)
            return True
        return False
        
    except Exception as e:
        print(f"Error deleting vector store: {str(e)}")
        return False