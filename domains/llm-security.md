# LLM / AI Security Audit Module

> Loaded when the project integrates LLMs, AI/ML models, or AI Agents

## Prompt Injection

### Direct Injection
- [ ] Is user input directly concatenated into the system prompt (e.g., f-string/format insertion into system message)
- [ ] Is there an isolation mechanism between prompt templates and user input (user input only as HumanMessage)
- [ ] Are historical messages sanitized in multi-turn conversations

### Indirect Injection
- [ ] Is external data (web pages, documents, emails) injected as context into the LLM
- [ ] Can RAG retrieval results be poisoned by attackers (publicly editable data sources)
- [ ] Are tool call results passed back to the LLM without validation

### Common Injection Vectors
- `ignore previous instructions` / `you are now` / `new instructions` patterns
- Embedding instructions in external documents (indirect injection triggered via RAG retrieval)
- Injecting links or images in LLM output via markdown/HTML (data exfiltration)

## Model Output Security

- [ ] Is LLM output used directly in `eval()`/`exec()` (highest risk)
- [ ] Is LLM output used directly for SQL query construction
- [ ] Is LLM output used directly for system command execution
- [ ] Is LLM output rendered directly into HTML (XSS)
- [ ] Does the prompt contain API Keys, passwords, or other sensitive information
- [ ] Can the model potentially leak system prompt contents
- [ ] Are conversation logs securely stored (containing user privacy data)

## AI Agent Security

- [ ] Do the tools callable by the Agent follow the principle of least privilege (whitelist rather than open all)
- [ ] Is file system access sandboxed
- [ ] Is there a domain whitelist for network requests
- [ ] Are database operations restricted to read-only
- [ ] Does the Agent loop have a maximum iteration limit (preventing infinite loops consuming resources)
- [ ] Do high-risk operations have a human approval process (human-in-the-loop)

## RAG Security

- [ ] Are the data sources for the vector database trusted
- [ ] Is there content moderation for document uploads
- [ ] Is data isolated between different tenants (namespace/collection level)
- [ ] Are retrieval results filtered by permissions

## Grep Search Patterns

```
Grep: system.*prompt|system_message|system_instruction
Grep: f".*{user|\.format\(.*user|template.*user
Grep: langchain|llama_index|LlamaIndex|openai\.chat|anthropic
Grep: tool_call|function_call|tool_use|tools\s*=
Grep: eval\(.*response|exec\(.*response|eval\(.*output
Grep: ChatCompletion|chat\.completions\.create
Grep: agent|Agent|auto_gpt|autogen
Grep: max_iterations|max_steps|max_turns
Grep: human_approval|human_in_the_loop
Grep: vectorstore|vector_db|chromadb|pinecone|weaviate|milvus
Grep: embedding|embed_query|embed_documents
Grep: similarity_search|retriever|retrieve
Grep: tenant|namespace|collection
Grep: \.invoke\(|\.run\(|\.call\(.*agent
```

## Cross-References

- Related domain modules: domains/api-security.md (API Key security, rate limiting), domains/command-injection.md (LLM output executing commands), domains/sql-injection.md (LLM output constructing SQL)
