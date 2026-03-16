"""
Interactive chatbot for the CP-AM-DRILL maintenance assistant.

Maintains full conversation history in Streamlit session_state and retrieves
relevant document chunks for each user query.
"""

import anthropic
from ai.prompts import SYSTEM_CONTEXT, CHATBOT_SYSTEM_PROMPT
from knowledge.document_index import retrieve_chunks


def get_chatbot_response(
    user_message: str,
    conversation_history: list[dict],
    diagnostic_report: str,
    all_chunks: list[dict],
) -> str:
    """
    Call Claude Sonnet 4.6 to answer a user question.

    Args:
        user_message:         The user's current question.
        conversation_history: List of {"role": "user"/"assistant", "content": "..."} dicts.
        diagnostic_report:    The generated report (cached in session_state).
        all_chunks:           All document chunks (to search for relevant context).

    Returns:
        Assistant response string.
    """
    client = anthropic.Anthropic()

    # Retrieve relevant chunks for this specific question
    relevant_chunks = retrieve_chunks(user_message, all_chunks, top_k=8)
    doc_context = _build_doc_context(relevant_chunks)

    system_prompt = (
        SYSTEM_CONTEXT
        + "\n\n"
        + CHATBOT_SYSTEM_PROMPT.format(
            doc_context=doc_context,
            diagnostic_report=diagnostic_report or "No report generated yet.",
        )
    )

    messages = conversation_history + [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            temperature=0,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIConnectionError:
        return (
            "I'm unable to connect to the AI service right now. "
            "Please check your network connection and API key, then try again."
        )
    except anthropic.APIStatusError as e:
        return f"API error ({e.status_code}): {e.message}. Please try again."


def _build_doc_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"--- {c['doc_name']}, Page {c['page']} ---\n{c['content']}"
        for c in chunks
    )
