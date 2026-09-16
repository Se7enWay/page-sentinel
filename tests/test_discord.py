"""Unit tests for Discord embed generation, field chunking, and rate-limit handling."""

from unittest.mock import MagicMock, patch

from monitor import FileItem
from notifiers.discord import send


def test_discord_embed_chunking():
    """Verify that fields are chunked into multiple embeds at the 25-field boundary."""
    files = [FileItem(filename=f"File_{i}.pdf", url=f"http://example.com/{i}.pdf") for i in range(30)]

    with patch("notifiers.discord.get_http_session") as mock_get_session:
        mock_session = MagicMock()
        mock_session.post.return_value.status_code = 204
        mock_get_session.return_value = mock_session

        send(
            title="Batch Update Alert",
            message="Multiple documents detected.",
            files=files,
        )

        assert mock_session.post.called
        call_kwargs = mock_session.post.call_args[1]
        payload = call_kwargs["json"]

        embeds = payload["embeds"]
        assert len(embeds) == 2
        assert len(embeds[0]["fields"]) == 25
        assert len(embeds[1]["fields"]) == 5

        # Primary embed should have title and footer, secondary should not
        assert "title" in embeds[0]
        assert "title" not in embeds[1]


def test_discord_rate_limit_retry():
    """Verify that a 429 response triggers a retry after sleeping."""
    files = [FileItem(filename="Test.pdf", url="http://example.com/test.pdf")]

    with patch("notifiers.discord.get_http_session") as mock_get_session, \
         patch("notifiers.discord.time.sleep") as mock_sleep:

        mock_session = MagicMock()

        # First call returns 429, second returns 204
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {"retry_after": 2.5}

        success_response = MagicMock()
        success_response.status_code = 204

        mock_session.post.side_effect = [rate_limit_response, success_response]
        mock_get_session.return_value = mock_session

        send(title="Test", message="Test", files=files)

        assert mock_session.post.call_count == 2
        mock_sleep.assert_called_once_with(2.5)
