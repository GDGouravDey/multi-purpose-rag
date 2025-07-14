from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_answer(query, context_docs=None):
    if context_docs is None:
        prompt = f"""You are a precise and trustworthy assistant.

Your task is to answer the user's question *accurately*. If you do not have enough information to answer reliably, respond with:

"I don't have enough information to answer that question."

Only use your own internal knowledge — do not make up facts.

### Question:
{query}
"""

        response = client.models.generate_content(model="gemini-2.5-flash",contents=prompt)
        return response.text.strip()
    else:
        context = "\n\n".join([doc.page_content for doc in context_docs])

        prompt = f"""You are a precise and trustworthy assistant.

Use the following context to answer the user's question as accurately as possible.
If the answer is not contained in the context, say:

"I don't have enough information in the provided context to answer that question."

Do not use your own assumptions or external knowledge.

    ### Context:
    {context}

    ### Question:
    {query}
    """

        response = client.models.generate_content(model="gemini-2.5-flash",contents=prompt)
        return response.text.strip()
