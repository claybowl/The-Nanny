import pytest
from src.core.agent import CommandParser, ComputerAgent

@pytest.fixture
def agent():
    return ComputerAgent()

class TestCommandParser:
    def test_open_app_command(self):
        test_cases = [
            "open chrome",
            "launch chrome browser",
            "start the application chrome",
            "open the app chrome",
        ]
        for test in test_cases:
            result = CommandParser.parse_command(test)
            assert result is not None
            assert result["action"] == "open_app"
            assert "chrome" in result["params"]

    def test_search_files_command(self):
        test_cases = [
            "search for files with report",
            "find documents containing budget",
            "locate files with presentation",
        ]
        for test in test_cases:
            result = CommandParser.parse_command(test)
            assert result is not None
            assert result["action"] == "search_files"
            assert any(word in result["params"] for word in ["report", "budget", "presentation"])

    def test_create_note_command(self):
        test_cases = [
            "create a note saying remember to buy milk",
            "write note buy groceries",
            "make a note saying call mom tomorrow",
        ]
        for test in test_cases:
            result = CommandParser.parse_command(test)
            assert result is not None
            assert result["action"] == "create_note"
            assert len(result["params"]) > 0

    def test_invalid_command(self):
        test_cases = [
            "do something random",
            "invalid command here",
            "",
            "   ",
        ]
        for test in test_cases:
            result = CommandParser.parse_command(test)
            assert result is None

class TestComputerAgent:
    @pytest.mark.asyncio
    async def test_execute_invalid_command(self, agent):
        result = await agent.execute_command("do something invalid")
        assert result["status"] == "error"
        assert "Could not understand command" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_open_app(self, agent):
        # Test with a non-existent app to avoid actually opening anything
        result = await agent.execute_command("open nonexistentapp123")
        assert result["status"] == "error"
        assert result["action"] == "open_app"
        assert "nonexistentapp123" in result["app_name"]

    @pytest.mark.asyncio
    async def test_execute_search_files(self, agent):
        result = await agent.execute_command("search for files with test")
        assert result["status"] == "success"
        assert result["action"] == "search_files"
        assert "test" in result["query"]
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_execute_create_note(self, agent):
        test_content = "test note content"
        result = await agent.execute_command(f"create note saying {test_content}")
        assert result["status"] == "success"
        assert result["action"] == "create_note"
        assert result["note_path"] is not None 