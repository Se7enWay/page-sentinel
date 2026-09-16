"""Unit tests for the ntfy push notification sender."""

from unittest.mock import MagicMock, patch

from monitor import FileItem
from notifiers.ntfy import send


def test_ntfy_sends_urgent_with_click_url():
    """Verify ntfy request includes urgent priority and click URL from first file."""
    files = [
        FileItem(filename="Master_IT.pdf", url="http://fsr.ac.ma/Master_IT.pdf"),
        FileItem(filename="Master_CS.pdf", url="http://fsr.ac.ma/Master_CS.pdf"),
    ]

    with patch("notifiers.ntfy.get_http_session") as mock_get_session:
        mock_session = MagicMock()
        mock_session.post.return_value.status_code = 200
        mock_get_session.return_value = mock_session

        send(title="New Files!", message="2 new documents.", files=files)

        assert mock_session.post.called
        call_kwargs = mock_session.post.call_args[1]
        headers = call_kwargs["headers"]

        assert headers["Priority"] == "urgent"
        assert headers["Click"] == "http://fsr.ac.ma/Master_IT.pdf"
        assert "Master_IT.pdf" in headers["Actions"]


def test_ntfy_truncates_large_file_list():
    """Verify that more than 10 files are truncated in the message body."""
    files = [FileItem(filename=f"Doc_{i}.pdf", url=f"http://example.com/{i}.pdf") for i in range(15)]

    with patch("notifiers.ntfy.get_http_session") as mock_get_session:
        mock_session = MagicMock()
        mock_session.post.return_value.status_code = 200
        mock_get_session.return_value = mock_session

        send(title="Batch", message="Many files.", files=files)

        call_args = mock_session.post.call_args
        body = call_args[1]["data"].decode("utf-8")

        assert "Doc_0.pdf" in body
        assert "Doc_9.pdf" in body
        assert "Doc_10.pdf" not in body
        assert "5 more files" in body
