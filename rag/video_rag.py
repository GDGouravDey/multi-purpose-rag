import os
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def process_youtube(video_url, user_id, store_name = "default"):
    try:
        transcript_text = fetch_youtube_transcript(video_url)

        if not transcript_text.strip():
            print("No transcript found.")
            return None

        docs = [Document(page_content=transcript_text, metadata={"source": video_url})]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(docs)

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
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
        print(f"Error processing YouTube video: {e}")
        return None
    
def fetch_youtube_transcript(video_url):
    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[-1].split("?")[0]
        else:
            raise ValueError("Invalid YouTube URL format")

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return ""
