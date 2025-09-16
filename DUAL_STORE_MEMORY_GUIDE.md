# 🧠 Dual Store Memory Management Guide

## Overview

This guide shows how to implement a **dual store memory system** that combines:

- **Regular LangGraph Store**: Key-value operations for structured data
- **Semantic Search Store**: Embedding-based similarity search for conversations

## 🎯 Why Dual Stores?

| Store Type         | Use Case                                    | Performance      | Data Type         |
| ------------------ | ------------------------------------------- | ---------------- | ----------------- |
| **Regular Store**  | User preferences, settings, metadata        | Fast key-value   | Structured        |
| **Semantic Store** | Conversation search, similar cases, context | Smart similarity | Unstructured text |

## 📁 Implementation Structure

```
your_project/
├── src/
│   ├── memory_manager.py          # Main memory manager class
│   ├── supervisor_agent/
│   │   ├── graph.py               # Updated supervisor with memory
│   │   ├── chitchat_memory.py     # ChitChatResponder memory logic
│   │   └── escalation_memory.py   # HumanEscalation memory logic
│   └── deep_agent/
│       └── memory_utils.py        # Deep agent memory logic
```

## 🛠️ Core Implementation

### 1. Memory Manager Class

```python
# src/memory_manager.py
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

class DualStoreMemoryManager:
    """Memory manager supporting both regular and semantic stores"""

    def __init__(self, regular_store, semantic_store=None):
        self.regular_store = regular_store
        self.semantic_store = semantic_store

    # === REGULAR STORE OPERATIONS ===
    async def store_user_data(self, assistant_id: str, key: str, data: Dict):
        """Store structured data in regular store"""
        await self.regular_store.put(["user_data", assistant_id], key, {
            **data,
            "updated_at": datetime.now().isoformat()
        })

    async def get_user_data(self, assistant_id: str, key: str) -> Dict:
        """Retrieve structured data from regular store"""
        item = await self.regular_store.get(["user_data", assistant_id], key)
        return item.value if item else {}

    # === SEMANTIC STORE OPERATIONS ===
    async def store_conversation(self, assistant_id: str, conversation: Dict):
        """Store conversation for semantic search"""
        if not self.semantic_store:
            return

        semantic_data = {
            "text": conversation.get("text", ""),
            "topics": conversation.get("topics", []),
            "sentiment": conversation.get("sentiment", "neutral"),
            "timestamp": datetime.now().isoformat()
        }

        await self.semantic_store.put(
            namespace=["conversations", assistant_id],
            key=f"conv_{conversation.get('id', datetime.now().timestamp())}",
            value=semantic_data
        )

    async def search_conversations(self, assistant_id: str, query: str, limit: int = 3):
        """Search conversations semantically"""
        if not self.semantic_store:
            return []

        results = await self.semantic_store.search(
            namespace=["conversations", assistant_id],
            query=query,
            limit=limit
        )

        return [result.value for result in results]

    # === HYBRID CONTEXT RETRIEVAL ===
    async def get_context_for_query(self, assistant_id: str, user_query: str):
        """Get comprehensive context using both stores"""
        # Structured data from regular store
        user_prefs = await self.get_user_data(assistant_id, "preferences")
        conversation_history = await self.get_user_data(assistant_id, "history")

        # Semantic data from semantic store
        relevant_conversations = []
        if self.semantic_store:
            relevant_conversations = await self.search_conversations(
                assistant_id, user_query, limit=2
            )

        return {
            "user_preferences": user_prefs,
            "conversation_history": conversation_history,
            "relevant_conversations": relevant_conversations,
            "query": user_query
        }
```

### 2. Store Initialization

```python
# In your graph setup
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings

# Regular store for structured data
regular_store = InMemoryStore()

# Semantic store for conversation search
semantic_store = InMemoryStore(
    index={
        "embed": init_embeddings("openai:text-embedding-3-small"),
        "dims": 1536,
        "fields": ["text", "topics", "$"]  # Fields to embed
    }
)

# Create dual store manager
memory_manager = DualStoreMemoryManager(regular_store, semantic_store)
```

## 🎭 Agent-Specific Implementations

### Supervisor Agent Memory

```python
# src/supervisor_agent/graph.py
async def supervisor_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")
    user_message = state.get("user_message", "")

    # Get context from both stores
    context = await memory_manager.get_context_for_query(assistant_id, user_message)

    # Use context for intelligent routing
    user_prefs = context.get("user_preferences", {})
    relevant_history = context.get("relevant_conversations", [])

    # Route based on learned patterns and context
    if should_route_to_chitchat(user_message, user_prefs):
        return {"next": "ChitChatResponder", "context": context}
    elif should_route_to_deep_agent(user_message, relevant_history):
        return {"next": "deep_agent", "context": context}
    else:
        return {"next": "HumanEscalation", "context": context}
```

### ChitChatResponder Memory

```python
# src/supervisor_agent/chitchat_memory.py
async def chitchat_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")

    # Learn from conversation patterns
    conversation_data = {
        "id": f"chitchat_{datetime.now().timestamp()}",
        "text": state.get("user_message", ""),
        "topics": ["casual", "conversation"],
        "sentiment": "friendly"
    }

    # Store for future semantic search
    await memory_manager.store_conversation(assistant_id, conversation_data)

    # Update user preferences based on interaction
    current_prefs = await memory_manager.get_user_data(assistant_id, "preferences")
    updated_prefs = learn_from_chitchat_interaction(current_prefs, state)

    await memory_manager.store_user_data(assistant_id, "preferences", updated_prefs)

    # Generate personalized response
    response = generate_chitchat_response(state, updated_prefs)

    return {"response": response}
```

### Deep Agent Memory

```python
# src/deep_agent/memory_utils.py
async def deep_agent_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")
    user_query = state.get("user_message", "")

    # Search for similar past analyses
    similar_analyses = await memory_manager.search_conversations(
        assistant_id, user_query, limit=3
    )

    # Use similar cases to inform current analysis
    analysis = perform_deep_analysis(user_query, similar_analyses)

    # Store this analysis for future searches
    analysis_data = {
        "id": f"analysis_{datetime.now().timestamp()}",
        "text": f"Analysis request: {user_query}",
        "topics": ["analysis", "research", "deep_dive"],
        "sentiment": "analytical"
    }

    await memory_manager.store_conversation(assistant_id, analysis_data)

    return {"response": analysis}
```

### HumanEscalation Memory

```python
# src/supervisor_agent/escalation_memory.py
async def escalation_node(state, config):
    memory_manager = config.get("memory_manager")
    assistant_id = config.get("assistant_id")

    # Record escalation pattern
    escalation_data = {
        "id": f"escalation_{datetime.now().timestamp()}",
        "text": state.get("user_message", ""),
        "topics": ["escalation", "unclear", "human_needed"],
        "sentiment": "frustrated"
    }

    await memory_manager.store_conversation(assistant_id, escalation_data)

    # Update escalation patterns for learning
    current_patterns = await memory_manager.get_user_data(assistant_id, "escalation_patterns")
    updated_patterns = update_escalation_patterns(current_patterns, state)

    await memory_manager.store_user_data(assistant_id, "escalation_patterns", updated_patterns)

    # Escalate to human
    return {"response": "Escalating to human agent", "escalated": True}
```

## 🔄 Data Flow Architecture

```
User Query → Supervisor Agent → Memory Manager
                              ↓
                    ┌─────────┴─────────┐
                    │                  │
            Regular Store     Semantic Store
            (Structured)      (Conversations)
                   │                  │
            Preferences       Similarity Search
            Settings          Context Retrieval
            Metadata          Pattern Matching
```

## 🎯 Benefits

### Performance Benefits

- **Fast Structured Access**: Regular store for frequent operations
- **Intelligent Search**: Semantic store for complex queries
- **Optimized Storage**: Right tool for each data type

### Intelligence Benefits

- **Context Awareness**: Understand conversation history semantically
- **Personalization**: Learn user preferences and patterns
- **Pattern Recognition**: Identify similar situations automatically

### Scalability Benefits

- **Modular Design**: Add new store types as needed
- **Independent Scaling**: Each store can scale separately
- **Fallback Support**: Continue working if one store fails

## 🚀 Getting Started

1. **Install Dependencies**:

```bash
pip install langgraph langchain langchain-openai
```

2. **Create Memory Manager**:

```python
# Copy the DualStoreMemoryManager class to your project
# Initialize with your stores
```

3. **Update Agent Nodes**:

```python
# Add memory_manager to your graph config
# Update each agent node to use memory operations
```

4. **Test Incrementally**:

```python
# Start with regular store only
# Add semantic store gradually
# Test each agent with memory integration
```

## 📊 Usage Examples

### Storing User Preferences

```python
await memory_manager.store_user_data(
    assistant_id="user_123",
    key="preferences",
    data={"theme": "dark", "language": "python", "verbosity": "concise"}
)
```

### Semantic Conversation Search

```python
relevant_conversations = await memory_manager.search_conversations(
    assistant_id="user_123",
    query="How do I implement authentication?",
    limit=3
)
```

### Context-Aware Response Generation

```python
context = await memory_manager.get_context_for_query(
    assistant_id="user_123",
    user_query="I need help with API design"
)

# Use context to generate personalized response
response = generate_response_with_context(user_query, context)
```

This dual store approach gives you the best of both worlds: fast, structured data access combined with intelligent, semantic search capabilities! 🎉</content>
</xai:function_call=python>  
<xai:function_call>  
<xai:function_call name="read">
<parameter name="filePath">/home/user/Journey/Mine/ML/open-canvas/dual_store_memory_example.py
