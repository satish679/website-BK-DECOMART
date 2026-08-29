"""Backend API tests for BK Decomart luxury home décor website.

Covers:
- /api/health
- /api/generated-images
- /api/static/img/generated/* (static image serving)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BASE_URL:
    # Fallback: read from frontend .env directly
    env_path = '/app/frontend/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BASE_URL = line.split('=', 1)[1].strip()
                    break

assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
BASE_URL = BASE_URL.rstrip('/')


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    return s


# ---------- Health ----------
class TestHealth:
    def test_health_ok(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/health", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "ok"

    def test_root(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "BK Decomart"


# ---------- Generated images listing ----------
class TestGeneratedImages:
    def test_list_returns_json_list(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/generated-images", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "images" in data
        assert isinstance(data["images"], list)
        assert len(data["images"]) > 0, "Expected at least one pre-generated image"

    def test_hero_living_present_or_absent(self, api_client):
        """hero-living.png should be in the list (part of the 19 generated)."""
        r = api_client.get(f"{BASE_URL}/api/generated-images", timeout=15)
        assert r.status_code == 200
        images = r.json()["images"]
        # Expect at least hero-living to be in the list
        assert "hero-living" in images


# ---------- Static image serving ----------
class TestStaticServing:
    def test_hero_living_png_serves_bytes(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/static/img/generated/hero-living.png", timeout=20)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("image/")
        assert len(r.content) > 5000, f"Image too small: {len(r.content)} bytes"
        # Accept PNG or JPEG magic bytes (files are served as static image bytes)
        is_png = r.content[:8] == b"\x89PNG\r\n\x1a\n"
        is_jpeg = r.content[:3] == b"\xff\xd8\xff"
        assert is_png or is_jpeg, f"Not a valid image: first bytes {r.content[:8].hex()}"

    def test_missing_image_404(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/static/img/generated/definitely-nonexistent-xyz.png", timeout=15)
        assert r.status_code == 404
