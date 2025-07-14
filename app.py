import streamlit as st
import os, requests
from time import sleep
from rag.document_rag import process_documents, load_vector_store, query_documents
from rag.website_rag import process_website
from gemini_llm import generate_answer
from rag.video_rag import process_youtube
from utils.db_utils import init_db, create_session_record, verify_user, add_user, update_conversation_in_db, get_all_sessions_helper
from streamlit_cookies_controller import CookieController

controller = CookieController()

def show_auth_form():
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.subheader("Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, name, email, user_id = verify_user(login_user, login_pass)
            if success:
                st.success(f"Welcome {name}!")
                st.session_state.user_id = user_id
                st.session_state.username = login_user
                st.session_state.name = name
                st.session_state.email = email
                session_id = create_session_record(user_id)
                st.session_state.session_id = session_id

                st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
                
                controller.set('user_id', user_id)
                controller.set('session_id', session_id)
                controller.set('name', name)
                controller.set('username', login_user)
                controller.set('email', email)
                sleep(1)

                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Signup")
        new_username = st.text_input("Username", key="signup_user")
        new_name = st.text_input("Name", key="signup_name")
        new_email = st.text_input("Email", key="signup_email")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Signup"):
            if new_username and new_name and new_email and new_pass:
                success, user_id = add_user(new_username, new_name, new_email, new_pass)
                if success:
                    st.success("Account created successfully!")
                    st.session_state.user_id = user_id
                    st.session_state.username = new_username
                    st.session_state.name = new_name
                    st.session_state.email = new_email

                    session_id = create_session_record(user_id)
                    st.session_state.session_id = session_id

                    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
                    
                    controller.set('user_id', user_id)
                    controller.set('session_id', session_id)
                    controller.set('name', new_name)
                    controller.set('username', new_username)
                    controller.set('email', new_email)
                    sleep(1)

                    st.rerun()
                else:
                    st.error(user_id)
            else:
                st.warning("Please fill all fields.")
    
def main():
    st.title("Multi Purpose RAG App")
    init_db()
    if 'user_id' not in st.session_state:
        user_id = controller.get('user_id')
        session_id = controller.get('session_id')
        username = controller.get('username')
        name = controller.get('name')
        email = controller.get('email')
        sleep(1)
        if user_id and session_id and username and name and email:
            st.session_state.user_id = user_id
            st.session_state.session_id = session_id
            st.session_state.username = username
            st.session_state.name = name
            st.session_state.email = email
        else:
            show_auth_form()
            return

    if 'user_id' in st.session_state:
        if 'session_id' in st.session_state:
            st.sidebar.success(f"Logged in as {st.session_state.name} (Session {st.session_state.session_id[:8]})")
        else:   
            st.sidebar.success(f"Logged in as {st.session_state.username}")

        if st.sidebar.button("Logout"):
            for key in ["user_id", "username", "name", "email", "session_id", "messages"]:
                if key in st.session_state:
                    del st.session_state[key]
            controller.remove('user_id')
            controller.remove('session_id')
            controller.remove('name')
            controller.remove('username')
            controller.remove('email')
            sleep(1)
            st.rerun()

        vector_store_path = f"vector_store/{st.session_state.user_id}_{st.session_state.session_id}"
        vector_store_exists = os.path.exists(vector_store_path)

        with st.sidebar.expander("Choose Source"):
            if vector_store_exists:
                st.info("A source is already selected for this session.")
            else:
                st.session_state.source = st.radio(label="Select Source", options=["None", "Documents", "Website", "Youtube"], horizontal=True, label_visibility="collapsed")

                if st.session_state.source == "Documents":
                    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, type=["pdf", "txt", "md"])
                    if uploaded_files:
                        st.session_state.uploaded_files = uploaded_files
                elif st.session_state.source == "Website":
                    url = st.text_input("Enter Website URL:")
                    if url:
                        st.session_state.source_url = url
                elif st.session_state.source == "Youtube":
                    url = st.text_input("Enter YouTube Video URL:")
                    if url:
                        st.session_state.source_url = url

        if st.sidebar.button("➕ Add New Session"):
            new_session_id = create_session_record(st.session_state.user_id)
            st.session_state.session_id = new_session_id
            st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]
            st.session_state.source = "None"
            st.session_state.uploaded_files = []
            st.session_state.source_url = ""
            st.rerun()

        st.sidebar.markdown("### All Sessions")

        try:
            session_list = get_all_sessions_helper(st.session_state.user_id)

            if session_list:
                for sess in session_list:
                    label = f"Session {sess['session_id'][:8]}"
                    if st.sidebar.button(label=label, key=sess["session_id"]):
                        controller.set('session_id', sess["session_id"])  
                        st.session_state.session_id = sess["session_id"]  
                        st.session_state.messages = sess["conversation"] 
                        st.rerun()
            else:
                st.sidebar.info("No sessions found.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

        if "source" not in st.session_state:
            st.session_state.source = "None"

        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        # Show conversation
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # User prompt input
        if prompt := st.chat_input("Enter your query..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                context_docs = []

                if vector_store_exists:
                    vector_store = load_vector_store(st.session_state.user_id, store_name=st.session_state.session_id)
                    if vector_store:
                        context_docs = query_documents(vector_store, prompt, k=5)
                else:
                    if st.session_state.source == "Documents" and st.session_state.get("uploaded_files"):
                        vector_store = process_documents(st.session_state.uploaded_files, st.session_state.user_id, store_name=st.session_state.session_id)
                        if vector_store:
                            context_docs = query_documents(vector_store, prompt, k=5)
                    elif st.session_state.source == "Website" and st.session_state.get("source_url"):
                        vector_store = process_website(st.session_state.source_url, st.session_state.user_id, store_name=st.session_state.session_id)
                        if vector_store:
                            context_docs = query_documents(vector_store, prompt, k=5)
                    elif st.session_state.source == "Youtube":
                        vector_store = process_youtube(st.session_state.source_url, st.session_state.user_id, store_name=st.session_state.session_id)
                        if vector_store:
                            context_docs = query_documents(vector_store, prompt, k=5)
                                
                with st.spinner("Generating response..."):
                    try:
                        if not context_docs:
                            answer = generate_answer(prompt)
                        else:
                            answer = generate_answer(prompt, context_docs)
                    except Exception as e:
                        answer = f"Error generating response: {e}"

                message_placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            update_conversation_in_db(st.session_state.session_id, st.session_state.messages)


if __name__ == "__main__":
    main()