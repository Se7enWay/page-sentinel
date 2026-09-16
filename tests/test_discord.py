"""Unit tests for Discord embed generation and field chunking limits."""

from unittest.mock import patch

from monitor import FileItem
from notifiers.discord import send


def test_discord_embed_chunking():
    # Create 30 mock files to trigger chunking past the 25-field limit
    files = [FileItem(filename=f"File_{i}.pdf", url=f"http://example.com/{i}.pdf") for i in range(30)]

    with patch("notifiers.discord.requests.post") as mock_post:
        mock_post.return_value.status_code = 204

        send(
            title="Batch Update Alert",
            message="Multiple documents detected.",
            files=files,
        )

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        embeds = payload["embeds"]
        # 30 items chunked at max 25 items per embed should produce exactly 2 embeds
        assert len(embeds) == 2
        assert len(embeds[0]["fields"]) == 25
        assert len(embeds[1]["fields"]) == 5
