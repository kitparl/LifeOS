import pytest
from app import main
from fastapi import HTTPException


def test_drawio_assets_cached_long():
    static = main.STATIC_DIR.resolve()
    assert main._static_headers(static / "drawio/24.0.0/js/app.min.js") == main.IMMUTABLE_HEADERS
    assert main._static_headers(static / "drawio/24.0.0/index.html") == main.IMMUTABLE_HEADERS


def test_non_drawio_unhashed_file_still_revalidated():
    static = main.STATIC_DIR.resolve()
    assert main._static_headers(static / "other/app.js") == main.NO_CACHE_HEADERS
    assert main._static_headers(static / "index.html") == main.NO_CACHE_HEADERS


@pytest.fixture
def static_dir(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<app-root></app-root>")
    (tmp_path / "drawio" / "24.0.0").mkdir(parents=True)
    (tmp_path / "drawio" / "24.0.0" / "index.html").write_text("drawio")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    return tmp_path


async def test_missing_drawio_file_is_404_not_spa_index(static_dir):
    with pytest.raises(HTTPException) as exc:
        await main.spa_files("drawio/23.0.0/index.html")
    assert exc.value.status_code == 404


async def test_existing_drawio_file_is_served(static_dir):
    response = await main.spa_files("drawio/24.0.0/index.html")
    assert response.path == (static_dir / "drawio/24.0.0/index.html").resolve()


async def test_missing_app_route_falls_back_to_spa_index(static_dir):
    response = await main.spa_files("planner")
    assert response.path == static_dir / "index.html"
