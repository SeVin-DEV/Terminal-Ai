import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL')
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not set", allow_module_level=True)
BASE_URL = BASE_URL.rstrip('/')


class TestHealthAndInfo:
    """API root health check and info endpoint"""

    def test_api_root(self, api_client):
        """Test GET /api/ returns API info"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message' field"
        assert "version" in data, "Response should contain 'version' field"
        assert data["message"] == "TermuxAI API", f"Expected 'TermuxAI API', got {data.get('message')}"
        print(f"✓ API root endpoint working: {data}")

    def test_health_endpoint(self, api_client):
        """Test GET /api/health returns health status with storage type and terminal status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "status" in data, "Response should contain 'status' field"
        assert "storage" in data, "Response should contain 'storage' field"
        assert "terminal_active" in data, "Response should contain 'terminal_active' field"
        assert "version" in data, "Response should contain 'version' field"
        
        assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
        assert data["storage"] in ["mongodb", "json"], f"Storage should be 'mongodb' or 'json', got {data.get('storage')}"
        assert isinstance(data["terminal_active"], bool), "terminal_active should be boolean"
        assert data["version"] == "1.0.0", f"Expected version '1.0.0', got {data.get('version')}"
        
        print(f"✓ Health endpoint working: status={data['status']}, storage={data['storage']}, terminal_active={data['terminal_active']}")

    def test_termux_setup_script(self, api_client):
        """Test GET /api/termux-setup returns bash setup script"""
        response = api_client.get(f"{BASE_URL}/api/termux-setup")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        script = response.text
        assert len(script) > 0, "Setup script should not be empty"
        assert "#!/data/data/com.termux/files/usr/bin/bash" in script, "Script should have Termux shebang"
        assert "pkg install" in script, "Script should contain 'pkg install' command"
        assert "pip install" in script, "Script should contain 'pip install' command"
        assert "tmux" in script, "Script should mention tmux"
        assert "fastapi" in script.lower(), "Script should install FastAPI"
        assert "uvicorn" in script.lower(), "Script should install uvicorn"
        assert "start.sh" in script, "Script should create start.sh"
        assert "stop.sh" in script, "Script should create stop.sh"
        assert "status.sh" in script, "Script should create status.sh"
        
        print(f"✓ Termux setup script endpoint working: {len(script)} chars, contains all required commands")

    def test_download_server_py(self, api_client):
        """Test GET /api/download/server.py returns server.py file content"""
        response = api_client.get(f"{BASE_URL}/api/download/server.py")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        content = response.text
        assert len(content) > 0, "Server.py content should not be empty"
        assert "from fastapi import FastAPI" in content, "Should contain FastAPI import"
        assert "app = FastAPI()" in content, "Should contain FastAPI app initialization"
        assert "def health_check" in content or "@api_router.get(\"/health\")" in content, "Should contain health endpoint"
        assert "AsyncIOMotorClient" in content or "_JDB" in content, "Should contain database client code"
        
        print(f"✓ Download server.py endpoint working: {len(content)} chars, valid Python FastAPI code")


class TestConfigManagement:
    """Config API endpoints: POST and GET /api/config"""

    def test_create_config_and_verify(self, api_client):
        """Test POST /api/config creates config and GET retrieves it"""
        # First, clear any existing config by creating a new one
        config_payload = {
            "provider": "openai",
            "api_key": "TEST_sk-test-key-12345",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o",
            "agent_name": "TestAgent",
            "system_prompt": "You are a test assistant",
            "theme": "cyberpunk_void",
            "auto_execute": False
        }
        
        # POST config
        create_response = api_client.post(f"{BASE_URL}/api/config", json=config_payload)
        assert create_response.status_code == 200, f"Expected 200, got {create_response.status_code}: {create_response.text}"
        
        created = create_response.json()
        assert created["provider"] == config_payload["provider"], "Provider mismatch"
        assert created["endpoint"] == config_payload["endpoint"], "Endpoint mismatch"
        assert created["model"] == config_payload["model"], "Model mismatch"
        assert created["agent_name"] == config_payload["agent_name"], "Agent name mismatch"
        assert created["theme"] == config_payload["theme"], "Theme mismatch"
        assert created["auto_execute"] == config_payload["auto_execute"], "Auto execute mismatch"
        assert created["has_api_key"] is True, "Should indicate API key is present"
        assert "id" in created, "Should have ID"
        assert "created_at" in created, "Should have created_at timestamp"
        assert "updated_at" in created, "Should have updated_at timestamp"
        print(f"✓ Config created successfully: ID={created['id']}")
        
        # GET config to verify persistence
        get_response = api_client.get(f"{BASE_URL}/api/config")
        assert get_response.status_code == 200, f"Expected 200, got {get_response.status_code}"
        
        retrieved = get_response.json()
        assert retrieved["provider"] == config_payload["provider"], "Retrieved provider mismatch"
        assert retrieved["endpoint"] == config_payload["endpoint"], "Retrieved endpoint mismatch"
        assert retrieved["model"] == config_payload["model"], "Retrieved model mismatch"
        assert retrieved["agent_name"] == config_payload["agent_name"], "Retrieved agent name mismatch"
        assert retrieved["has_api_key"] is True, "Retrieved config should show has_api_key=True"
        assert "api_key" not in retrieved, "API key should not be in response"
        print(f"✓ Config retrieved and verified from database")

    def test_update_config(self, api_client):
        """Test POST /api/config updates existing config"""
        # Update config
        update_payload = {
            "provider": "anthropic",
            "api_key": "TEST_sk-ant-updated-key",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "model": "claude-sonnet-4-20250514",
            "agent_name": "UpdatedAgent",
            "system_prompt": "Updated prompt",
            "theme": "monokai_pro",
            "auto_execute": True
        }
        
        update_response = api_client.post(f"{BASE_URL}/api/config", json=update_payload)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        updated = update_response.json()
        assert updated["provider"] == "anthropic", "Provider should be updated"
        assert updated["model"] == "claude-sonnet-4-20250514", "Model should be updated"
        assert updated["agent_name"] == "UpdatedAgent", "Agent name should be updated"
        assert updated["theme"] == "monokai_pro", "Theme should be updated"
        assert updated["auto_execute"] is True, "Auto execute should be updated"
        print(f"✓ Config updated successfully")


class TestTerminal:
    """Terminal API endpoints: POST /api/terminal/execute, GET /api/terminal/history"""

    def test_terminal_execute_command(self, api_client):
        """Test POST /api/terminal/execute sends command"""
        command_payload = {"command": "echo 'TEST_COMMAND_OUTPUT'"}
        
        response = api_client.post(f"{BASE_URL}/api/terminal/execute", json=command_payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Should have message field"
        assert "command" in data, "Should echo back command"
        assert data["command"] == command_payload["command"], "Command mismatch"
        print(f"✓ Terminal execute endpoint working")

    def test_terminal_get_history(self, api_client):
        """Test GET /api/terminal/history returns history"""
        # First execute a command
        api_client.post(f"{BASE_URL}/api/terminal/execute", json={"command": "echo 'HISTORY_TEST'\n"})
        time.sleep(0.5)  # Wait for command to execute
        
        response = api_client.get(f"{BASE_URL}/api/terminal/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "history" in data, "Should have history field"
        assert isinstance(data["history"], str), "History should be a string"
        print(f"✓ Terminal history endpoint working (length: {len(data['history'])} chars)")


class TestChat:
    """Chat API endpoints: POST /api/chat, GET /api/chat/history, DELETE /api/chat/history"""

    def test_chat_get_history(self, api_client):
        """Test GET /api/chat/history returns chat messages"""
        response = api_client.get(f"{BASE_URL}/api/chat/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Chat history should be a list"
        print(f"✓ Chat history endpoint working (messages: {len(data)})")

    def test_chat_clear_history(self, api_client):
        """Test DELETE /api/chat/history clears messages"""
        # Clear history
        delete_response = api_client.delete(f"{BASE_URL}/api/chat/history")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        
        delete_data = delete_response.json()
        assert "message" in delete_data, "Should have message field"
        print(f"✓ Chat history cleared")
        
        # Verify history is empty
        get_response = api_client.get(f"{BASE_URL}/api/chat/history")
        assert get_response.status_code == 200
        history = get_response.json()
        assert isinstance(history, list), "Should return list"
        assert len(history) == 0, "History should be empty after delete"
        print(f"✓ Chat history verified empty")

    def test_chat_send_message(self, api_client):
        """Test POST /api/chat with a message (will fail without valid API key)"""
        # Note: This will fail because we don't have a real API key
        # We're testing that the endpoint accepts the request format
        message_payload = {"content": "Hello, this is a test message"}
        
        response = api_client.post(f"{BASE_URL}/api/chat", json=message_payload)
        
        # We expect either 200 (if mock key works) or 500 (if AI provider fails)
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data, "Should have message ID"
            assert "role" in data, "Should have role"
            assert "content" in data, "Should have content"
            assert data["role"] == "assistant", "Should be assistant response"
            print(f"✓ Chat message endpoint working (got AI response)")
        else:
            # API key is test key, so AI provider will fail
            data = response.json()
            assert "detail" in data, "Error should have detail"
            print(f"✓ Chat endpoint properly returns error for invalid API key: {data['detail'][:100]}")
