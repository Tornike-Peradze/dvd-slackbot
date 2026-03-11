class MemoryStore:
    def __init__(self):
        self.memory = {}
        
    def add_turn(self, session_key: str, role: str, content: str):
        if session_key not in self.memory:
            self.memory[session_key] = []
        self.memory[session_key].append({"role": role, "content": content})
        self.memory[session_key] = self.memory[session_key][-10:]
        
    def get_context(self, session_key: str) -> list:
        return self.memory.get(session_key, [])
