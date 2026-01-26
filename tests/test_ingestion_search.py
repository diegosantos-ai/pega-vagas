from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ingestion.scrapers.api_scrapers import GupySearchScraper


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient", new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_gupy_search_jobs_basic(mock_httpx_client):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": 123,
                "name": "Data Engineer",
                "companyName": "Tech Corp",
                "careerPageUrl": "https://techcorp.gupy.io",
                "description": "Python, SQL"
            }
        ]
    }
    
    # Instance scraper (mock client is created inside init, so we patch it globally or inject)
    # Better approach: patch the client instance on the scraper object
    scraper = GupySearchScraper()
    scraper.client.get = AsyncMock(return_value=mock_response)
    
    jobs = await scraper.search_jobs(query="Data Engineer", limit=1)
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Data Engineer"
    assert jobs[0]["company"] == "Tech Corp"
    assert "url" in jobs[0]
    assert "https://techcorp.gupy.io/job/123" in jobs[0]["url"]

@pytest.mark.asyncio
async def test_gupy_pagination():
    scraper = GupySearchScraper()
    scraper.client.get = AsyncMock()
    
    # Page 1 response
    page1 = MagicMock()
    page1.status_code = 200
    page1.json.return_value = {
        "data": [{"id": i, "name": f"Job {i}"} for i in range(1, 11)] # 10 jobs
    }
    
    # Page 2 response
    page2 = MagicMock()
    page2.status_code = 200
    page2.json.return_value = {
        "data": [{"id": i, "name": f"Job {i}"} for i in range(11, 16)] # 5 jobs
    }
    
    scraper.client.get.side_effect = [page1, page2]
    
    # Request 15 jobs, but page 1 only has 10
    jobs = await scraper.search_jobs(query="test", limit=15)
    
    assert len(jobs) == 15
    assert scraper.client.get.call_count == 2
    assert jobs[0]["title"] == "Job 1"
    assert jobs[14]["title"] == "Job 15"
