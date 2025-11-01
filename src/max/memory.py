from langchain_classic.memory import ConversationBufferMemory

# Singleton instance for conversation memory
_memory_instance = None

def get_memory():
    """Get or create the conversation memory singleton.

    This ensures the same memory instance is used throughout the application,
    maintaining conversation history across multiple calls.
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
    return _memory_instance