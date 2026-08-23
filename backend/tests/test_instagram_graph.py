from app.integrations.instagram.graph import graph_base, refresh_url


def test_instagram_login_token_uses_instagram_graph():
    assert graph_base("IGAA-example").startswith("https://graph.instagram.com/v25.0")
    assert refresh_url("IGAA-example") == "https://graph.instagram.com/refresh_access_token"


def test_page_token_uses_facebook_graph():
    assert graph_base("EAA-example").startswith("https://graph.facebook.com/v25.0")
