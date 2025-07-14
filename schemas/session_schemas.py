from pydantic import BaseModel
from typing import List

class AskRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    
class AskResponse(BaseModel):
    success: bool
    answer: str
    
class DelSessionResponse(BaseModel):
    success: bool
    message: str
    
class VSExistsResponse(BaseModel):
    exists: bool
    
class UserDetails(BaseModel):
    username: str
    name: str
    email: str
    user_id: str
    
class Message(BaseModel):
    role: str
    content: str

class SessionDetails(BaseModel):
    session_id: str
    creation_time: str
    conversation: List[Message]