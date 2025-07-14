from fastapi import FastAPI, HTTPException
import os
from typing import List, Dict, Any
from rag.document_rag import load_vector_store, query_documents, delete_vector_store
from gemini_llm import generate_answer
from utils.db_utils import update_conversation_in_db, get_all_messages_helper, get_session_details_helper, get_all_sessions_helper, get_all_users_helper, delete_session_helper, verify_user, add_user
from fastapi.middleware.cors import CORSMiddleware
from schemas.auth_schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from schemas.session_schemas import AskRequest, AskResponse, DelSessionResponse, VSExistsResponse, UserDetails, SessionDetails, Message
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "users.db"

@app.get("/")
def base():
    return {"status": "ok", "message": "FastAPI running successfully"}

@app.get("/users/{user_id}/{session_id}/get_messages", response_model=List[Message])
def get_all_messages(user_id: str, session_id: str):
    try:
        return get_all_messages_helper(user_id, session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/users/{user_id}/{session_id}/get_session_details", response_model=SessionDetails)
def get_session_details(user_id: str, session_id: str):
    try:
        return get_session_details_helper(user_id, session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/users/{user_id}/get_all_sessions", response_model=List[SessionDetails])
def get_all_sessions(user_id: str):
    try:
        return get_all_sessions_helper(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/get_all_users", response_model=List[UserDetails])
def get_all_users():
    try:
        return get_all_users_helper()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@app.get("/users/{user_id}/{session_id}/vector_store_exists", response_model = VSExistsResponse)
def vector_store_exists(user_id: str, session_id: str):
    try:
        path = f"vector_store/{user_id}_{session_id}"
        return {"exists": os.path.exists(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@app.post("/ask_chatbot", response_model = AskResponse)
def ask_chatbot(ask : AskRequest):
    try:
        user_id = ask.user_id
        session_id = ask.session_id
        query = ask.query
        messages = get_all_messages(user_id, session_id)
        context_docs = []
        if vector_store_exists(user_id, session_id)["exists"] == True:
            vector_store = load_vector_store(user_id, store_name=session_id)
            if vector_store:
                context_docs = query_documents(vector_store, query, k=5)
        try:
            if not context_docs:
                answer = generate_answer(query)
            else:
                answer = generate_answer(query, context_docs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
        messages.append({"role": "user", "content": query})
        messages.append({"role": "assistant", "content": answer})
        update_conversation_in_db(session_id, messages)
        return { "success": True, "answer": answer }
    except HTTPException as e:
        raise e       
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@app.delete("/users/{user_id}/{session_id}/delete_session", response_model=DelSessionResponse)
def delete_session(user_id: str, session_id: str):
    try:
        get_session_details(user_id, session_id)
        if(vector_store_exists(user_id, session_id)["exists"] == True):
            delete_vector_store(user_id, session_id)
        return delete_session_helper(user_id, session_id)
    except HTTPException as e:
            raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@app.post("/login", response_model=LoginResponse)
def login_user(login: LoginRequest):
    try:
        success, name, username, user_id =  verify_user(login.username, login.password)
        return { "success": success, "name": name, "username": username, "user_id": user_id }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/register", response_model=RegisterResponse)
def register_user(register: RegisterRequest):
    try:
        status, user_id = add_user(register.username, register.name, register.email, register.password)
        return { "status" : status, "user_id" : user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    