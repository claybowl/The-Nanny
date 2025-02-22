import os
import subprocess
import platform
from pathlib import Path
from typing import List, Optional

class SystemActionHandler:
    def __init__(self):
        self.os_type = platform.system().lower()
    
    def open_application(self, app_name: str) -> bool:
        """Open an application by name."""
        try:
            if self.os_type == "windows":
                os.startfile(app_name)
            elif self.os_type == "darwin":  # macOS
                subprocess.run(["open", "-a", app_name])
            else:  # Linux
                subprocess.Popen([app_name])
            return True
        except Exception as e:
            print(f"Error opening application {app_name}: {e}")
            return False
    
    def search_files(self, query: str, path: Optional[Path] = None) -> List[Path]:
        """Search for files matching the query."""
        if path is None:
            path = Path.home()
        
        results = []
        try:
            for item in path.rglob(f"*{query}*"):
                if item.is_file():
                    results.append(item)
        except Exception as e:
            print(f"Error searching files: {e}")
        
        return results[:10]  # Limit results to 10 files
    
    def create_note(self, content: str, filename: Optional[str] = None) -> Optional[Path]:
        """Create a text note."""
        try:
            notes_dir = Path.home() / "Documents" / "CLAWD_Notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            if not filename:
                from datetime import datetime
                filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            file_path = notes_dir / filename
            file_path.write_text(content)
            return file_path
        except Exception as e:
            print(f"Error creating note: {e}")
            return None 