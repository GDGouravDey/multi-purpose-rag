import sqlite3
import uuid
import bcrypt
from datetime import datetime
import json
from fastapi import HTTPException

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            creation_time TEXT,
            conversation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, name, email, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, name, email, password, user_id) VALUES (?, ?, ?, ?, ?)",
                  (username, name, email, hashed_pw, user_id))
        conn.commit()
        conn.close()
        return True, user_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username or email already exists"

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name, email, password, user_id FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row:
        name, email, hashed_pw, user_id = row
        if bcrypt.checkpw(password.encode(), hashed_pw.encode()):
            return True, name, email, user_id
    return False, None, None, None

def create_session_record(user_id):
    session_id = str(uuid.uuid4())
    creation_time = datetime.now().isoformat()
    conversation = [{"role": "assistant", "content": "How can I help you?"}]
    conversation_json = json.dumps(conversation)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sessions (session_id, user_id, creation_time, conversation)
        VALUES (?, ?, ?, ?)
    ''', (session_id, user_id, creation_time, conversation_json))
    conn.commit()
    conn.close()
    return session_id

def update_conversation_in_db(session_id, messages):
    conversation_json = json.dumps(messages)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE sessions SET conversation = ? WHERE session_id = ?
    ''', (conversation_json, session_id))
    conn.commit()
    conn.close()
    
def get_all_messages_helper(user_id, session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT conversation FROM sessions
            WHERE user_id = ? AND session_id = ?
        ''', (user_id, session_id))
        row = c.fetchone()
    except sqlite3.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found for given user_id and session_id")

    conversation_json = row[0]
    try:
        conversation = json.loads(conversation_json)
    except json.JSONDecodeError:
        conversation = []

    return conversation

def get_session_details_helper(user_id, session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT session_id, creation_time, conversation
            FROM sessions
            WHERE user_id = ? AND session_id = ?
        ''', (user_id, session_id))
        row = c.fetchone()
    except sqlite3.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found for given user_id and session_id")

    session_id, creation_time, conversation_json = row

    try:
        conversation = json.loads(conversation_json)
    except json.JSONDecodeError:
        conversation = []

    return {
        "session_id": session_id,
        "creation_time": creation_time,
        "conversation": conversation
    }
    
def get_all_sessions_helper(user_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT session_id, creation_time, conversation FROM sessions
            WHERE user_id = ?
            ORDER BY creation_time DESC
        ''', (user_id,))
        rows = c.fetchall()
    except sqlite3.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No sessions found for given user_id")

    sessions = []
    for session_id, creation_time, conversation_json in rows:
        try:
            conversation = json.loads(conversation_json)
        except json.JSONDecodeError:
            conversation = []
        sessions.append({
            "session_id": session_id,
            "creation_time": creation_time,
            "conversation": conversation
        })

    return sessions

def get_all_users_helper():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT username, name, email, user_id FROM users
        ''')
        rows = c.fetchall()
    except sqlite3.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No users found")

    users = []
    for username, name, email, user_id in rows:
        users.append({
            "username": username,
            "name": name,
            "email": email,
            "user_id": user_id
        })

    return users

def delete_session_helper(user_id: str, session_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            DELETE FROM sessions WHERE user_id = ? AND session_id = ?
        ''', (user_id, session_id))
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        if deleted_count == 0:
            return {"success": False, "message": "No such session found"}
        return {"success": True, "message": "Session deleted successfully"}
    except sqlite3.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")