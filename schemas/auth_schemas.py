from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
    
class LoginResponse(BaseModel):
    success: bool
    name: str | None
    username: str | None
    user_id: str | None

class RegisterRequest(BaseModel):
    username: str
    name: str
    email: str
    password: str
    
class RegisterResponse(BaseModel):
    success: bool
    user_id: str