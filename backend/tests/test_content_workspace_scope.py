from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.db.repositories.chunks_repo import search_similar_chunks


def test_vector_search_uses_scoped_rpc_and_workspace_filter() -> None:
    client = Mock()
    client.rpc.return_value.execute.return_value = SimpleNamespace(data=[])
    with patch("app.db.repositories.chunks_repo.get_supabase_client", return_value=client):
        search_similar_chunks([0.1, 0.2], match_count=7, match_threshold=0.5, workspace_id="workspace-a")
    client.rpc.assert_called_once_with("match_chunks_scoped", {
        "query_embedding": [0.1, 0.2],
        "match_count": 7,
        "match_threshold": 0.5,
        "filter_workspace_id": "workspace-a",
    })


def test_workspace_migration_filters_before_vector_ranking() -> None:
    migration = (
        Path(__file__).parents[1] / "migrations" / "019_content_workspace_isolation.sql"
    ).read_text(encoding="utf-8").casefold()
    assert "create or replace function public.match_chunks_scoped" in migration
    assert "where c.workspace_id = filter_workspace_id" in migration
    assert migration.index("where c.workspace_id = filter_workspace_id") < migration.index("order by c.embedding")
