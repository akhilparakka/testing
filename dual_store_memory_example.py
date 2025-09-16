#!/usr/bin/env python3
"""
Dual Store Memory Manager Example
Demonstrates how to use both regular LangGraph stores and semantic search stores
"""

# === EXAMPLE IMPLEMENTATION ===

class DualStoreMemoryManager:
    """
    Example implementation of a memory manager that supports both:
    1. Regular LangGraph Store (key-value operations)
    2. Semantic Search Store (embedding-based similarity search)
    """

    def __init__(self, regular_store, semantic_store=None):
        self.regular_store = regular_store
        self.semantic_store = semantic_store

    # === REGULAR STORE METHODS ===
    async def store_user_preferences(self, assistant_id: str, preferences: dict):
        """Store user preferences in regular store"""
        await self.regular_store.put(
            ["user_data", assistant_id],
            "preferences",
            preferences
        )

    async def get_user_preferences(self, assistant_id: str):
        """Get user preferences from regular store"""
        item = await self.regular_store.get(["user_data", assistant_id], "preferences")
        return item.value if item else {}

    # === SEMANTIC STORE METHODS ===
    async def store_conversation_for_search(self, assistant_id: str, conversation: dict):
        """Store conversation in semantic store for similarity search"""
        if not self.semantic_store:
            return

        # Prepare data for semantic search
        semantic_data = {
            "text": conversation.get("text", ""),
            "topics": conversation.get("topics", []),
            "timestamp": conversation.get("timestamp"),
            "sentiment": conversation.get("sentiment", "neutral")
        }

        await self.semantic_store.put(
            namespace=["conversations", assistant_id],
            key=f"conv_{conversation.get('id', 'unknown')}",
            value=semantic_data
        )

    async def search_similar_conversations(self, assistant_id: str, query: str, limit: int = 3):
        """Search for semantically similar conversations"""
        if not self.semantic_store:
            return []

        results = await self.semantic_store.search(
            namespace=["conversations", assistant_id],
            query=query,
            limit=limit
        )

        return [result.value for result in results]

    # === HYBRID METHODS ===
    async def get_context_for_response(self, assistant_id: str, user_query: str):
        """Get comprehensive context using both stores"""
        # Get structured preferences from regular store
        preferences = await self.get_user_preferences(assistant_id)

        # Get semantically similar conversations
        similar_conversations = []
        if self.semantic_store:
            similar_conversations = await self.search_similar_conversations(
                assistant_id, user_query, limit=2
            )

        return {
            "user_preferences": preferences,
            "relevant_conversations": similar_conversations,
            "query": user_query
        }


# === USAGE IN YOUR SUPERVISOR AGENT ===

"""
# In your supervisor_agent/graph.py:

from dual_store_memory_example import DualStoreMemoryManager

# Initialize stores (this would be in your graph setup)
regular_store = InMemoryStore()  # or your actual store
semantic_store = InMemoryStore(
    index={
        "embed": init_embeddings("openai:text-embedding-3-small"),
        "dims": 1536,
        "fields": ["text", "topics", "$"]
    }
)

memory_manager = DualStoreMemoryManager(regular_store, semantic_store)

# In your supervisor node:
async def supervisor_node(state, config):
    assistant_id = config.get("assistant_id")
    user_message = state.get("user_message", "")

    # Get context from both stores
    context = await memory_manager.get_context_for_response(assistant_id, user_message)

    # Use context for decision making
    user_preferences = context.get("user_preferences", {})
    relevant_history = context.get("relevant_conversations", [])

    # Make routing decision based on context
    if should_route_to_chitchat(user_message, user_preferences):
        return {"next": "ChitChatResponder", "context": context}
    elif should_route_to_deep_agent(user_message, relevant_history):
        return {"next": "deep_agent", "context": context}
    else:
        return {"next": "HumanEscalation", "context": context}

# In your ChitChatResponder:
async def chitchat_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")

    # Learn from conversation
    conversation_data = {
        "id": f"chitchat_{datetime.now().timestamp()}",
        "text": state.get("user_message", ""),
        "topics": ["casual", "conversation"],
        "sentiment": "friendly",
        "timestamp": datetime.now().isoformat()
    }

    # Store for future semantic search
    await memory_manager.store_conversation_for_search(assistant_id, conversation_data)

    # Generate response based on learned patterns
    response = generate_chitchat_response(state, conversation_data)

    return {"response": response}

# In your deep_agent:
async def deep_agent_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")
    user_query = state.get("user_message", "")

    # Search for relevant past analyses
    similar_cases = await memory_manager.search_similar_conversations(
        assistant_id, user_query, limit=3
    )

    # Use similar cases to inform analysis
    analysis = perform_deep_analysis(user_query, similar_cases)

    # Store this analysis for future searches
    analysis_data = {
        "id": f"analysis_{datetime.now().timestamp()}",
        "text": f"Analysis of: {user_query}",
        "topics": ["analysis", "deep_research"],
        "sentiment": "analytical",
        "timestamp": datetime.now().isoformat()
    }

    await memory_manager.store_conversation_for_search(assistant_id, analysis_data)

    return {"response": analysis}
"""

# === STORE INITIALIZATION EXAMPLES ===

"""
# Example 1: Regular Store Only
regular_store = InMemoryStore()
memory_manager = DualStoreMemoryManager(regular_store)

# Use for simple key-value operations
await memory_manager.store_user_preferences("user_123", {"theme": "dark"})

# Example 2: Dual Store Setup
from langchain.embeddings import init_embeddings

regular_store = InMemoryStore()
semantic_store = InMemoryStore(
    index={
        "embed": init_embeddings("openai:text-embedding-3-small"),
        "dims": 1536,
        "fields": ["text", "topics", "$"]  # Fields to embed for search
    }
)

memory_manager = DualStoreMemoryManager(regular_store, semantic_store)

# Now you can use both:
# - Regular store for structured data (preferences, settings)
# - Semantic store for conversational search (similar messages, context)
"""

# === BENEFITS OF THIS APPROACH ===

"""
Benefits of Dual Store Memory Management:

1. **Flexible Storage**:
   - Regular store: Fast key-value operations for structured data
   - Semantic store: Intelligent similarity search for conversations

2. **Optimized Performance**:
   - Use regular store for frequent, structured operations
   - Use semantic store for complex queries and pattern matching

3. **Intelligent Context**:
   - Regular store: User preferences, settings, metadata
   - Semantic store: Conversation history, similar cases, context

4. **Scalable Architecture**:
   - Add more store types as needed (vector stores, graph stores, etc.)
   - Each agent can choose the appropriate store for its needs

5. **Fallback Support**:
   - If semantic store fails, fall back to regular store
   - Graceful degradation maintains functionality

Example Use Cases:

**ChitChatResponder**:
- Regular store: User conversation style preferences
- Semantic store: Search for similar casual conversations

**HumanEscalation**:
- Regular store: Escalation patterns and thresholds
- Semantic store: Search for similar escalation scenarios

**deep_agent**:
- Regular store: Analysis templates and methodologies
- Semantic store: Search for similar research queries and findings
"""

print("🎉 Dual Store Memory Manager example created!")
print("📁 File: dual_store_memory_example.py")
print("📚 This shows how to implement both regular and semantic stores")
print("🔧 Adapt this pattern to your supervisor agent architecture")