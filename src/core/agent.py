from typing import Dict, Any, Optional
from pathlib import Path
import re
import webbrowser
from urllib.parse import quote

from .system_actions import SystemActionHandler

class CommandParser:
    """Parse natural language commands into structured actions."""
    
    COMMAND_PATTERNS = {
        "open_app": r"(?:open|launch|start)\s+(?:the\s+)?(?:app|application\s+)?([a-zA-Z0-9\s]+)",
        "search_files": r"(?:find|search|locate)\s+(?:for\s+)?(?:files?|documents?)\s+(?:with|containing)\s+([a-zA-Z0-9\s]+)",
        "create_note": r"(?:create|make|write)\s+(?:a\s+)?note\s+(?:saying\s+)?(.+)",
        "web_search": r"(?:google|search|look up|find)\s+(?:for\s+)?(.+?)(?:\s+for\s+(?:me|us))?$"
    }
    
    @classmethod
    def parse_command(cls, text: str) -> Optional[Dict[str, Any]]:
        """Parse natural language text into a structured command."""
        text = text.lower().strip()
        
        for action, pattern in cls.COMMAND_PATTERNS.items():
            if match := re.search(pattern, text):
                return {
                    "action": action,
                    "params": match.group(1).strip()
                }
        
        return None

class ComputerAgent:
    """Main agent for handling computer control commands."""
    
    def __init__(self):
        self.system = SystemActionHandler()
        self.parser = CommandParser()
    
    async def execute_command(self, command_text: str) -> Dict[str, Any]:
        """Execute a natural language command."""
        
        # Parse the command
        parsed = self.parser.parse_command(command_text)
        if not parsed:
            return {
                "status": "error",
                "message": "Could not understand command",
                "original_text": command_text
            }
        
        # Execute the appropriate action
        try:
            if parsed["action"] == "open_app":
                success = self.system.open_application(parsed["params"])
                return {
                    "status": "success" if success else "error",
                    "action": "open_app",
                    "app_name": parsed["params"],
                    "message": f"{'Opened' if success else 'Failed to open'} {parsed['params']}"
                }
                
            elif parsed["action"] == "search_files":
                results = self.system.search_files(parsed["params"])
                return {
                    "status": "success",
                    "action": "search_files",
                    "query": parsed["params"],
                    "results": [str(p) for p in results],
                    "message": f"Found {len(results)} files matching '{parsed['params']}'"
                }
                
            elif parsed["action"] == "create_note":
                note_path = self.system.create_note(parsed["params"])
                return {
                    "status": "success" if note_path else "error",
                    "action": "create_note",
                    "note_path": str(note_path) if note_path else None,
                    "message": f"{'Created note at' if note_path else 'Failed to create note'} {note_path}"
                }
                
            elif parsed["action"] == "web_search":
                search_query = quote(parsed["params"])
                search_url = f"https://www.google.com/search?q={search_query}"
                webbrowser.open(search_url)
                return {
                    "status": "success",
                    "action": "web_search",
                    "query": parsed["params"],
                    "url": search_url,
                    "message": f"Opened Google search for '{parsed['params']}'"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "action": parsed["action"],
                "message": f"Error executing command: {str(e)}",
                "original_text": command_text
            }
        
        return {
            "status": "error",
            "message": "Unsupported command",
            "original_text": command_text
        } 