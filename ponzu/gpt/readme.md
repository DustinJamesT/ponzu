
# GPT LANGCHAIN WRAPPER 

The code is broken out into 
 - api: base apt for interacting with objects like vectorstore and openai 
 - chains: langchain chains for executing llm
 - actions: use api and chains to execute actions like summarize. can be bigger chains 
 - tools: tool wrappers for actions (used by agents and chains)
- agents: dynamic agents that use actions to do things like summarize text