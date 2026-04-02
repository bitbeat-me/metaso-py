from metaso.types import (
    Book,
    ChatResponse,
    File,
    ReaderResponse,
    SearchResponse,
    SearchResult,
    Topic,
    UserInfo,
)


def test_search_result_creation():
    r = SearchResult(
        id="1", title="Test", url="https://example.com", snippet="hello", source="webpage"
    )
    assert r.id == "1"
    assert r.source == "webpage"


def test_search_response_with_optional_fields():
    r = SearchResponse(query="test", results=[])
    assert r.summary is None
    assert r.session_id is None


def test_search_response_with_results():
    result = SearchResult(id="1", title="T", url="https://x.com", snippet="s", source="webpage")
    resp = SearchResponse(query="q", results=[result], summary="AI summary", session_id="sess-1")
    assert len(resp.results) == 1
    assert resp.summary == "AI summary"


def test_reader_response():
    r = ReaderResponse(url="https://example.com", content="# Hello", format="markdown")
    assert r.format == "markdown"


def test_chat_response():
    r = ChatResponse(message="what is AI", answer="AI is...", model="fast")
    assert r.model == "fast"


def test_chat_response_default_model():
    r = ChatResponse(message="q", answer="a")
    assert r.model == "fast"


def test_topic_minimal():
    t = Topic(id="t1", name="Research")
    assert t.dir_root_id is None


def test_file_defaults():
    f = File(id="f1", file_name="paper.pdf", parent_id="p1")
    assert f.progress == 0
    assert f.status == "processing"


def test_book_defaults():
    b = Book(id="b1", title="My Book", file_id="f1")
    assert b.progress == 0


def test_user_info_minimal():
    u = UserInfo(uid="u1")
    assert u.nickname is None
    assert u.vip_level == 0
