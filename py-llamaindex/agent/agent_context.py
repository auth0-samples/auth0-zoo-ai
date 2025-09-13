from contextvars import ContextVar


agent_context = ContextVar("agent_context", default={})

def get_agent_context():
    return agent_context.get()

def clean_agent_context():
    agent_context.set({})