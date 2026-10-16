from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from file_routes import download_file


def test_user_cannot_download_another_users_file():
    attacker = SimpleNamespace(id=202, email="userb@example.com")

    query = MagicMock()
    query.filter.return_value.first.return_value = None

    db = MagicMock()
    db.query.return_value = query

    with patch("file_routes.log_security_event") as security_log:
        with pytest.raises(HTTPException) as error:
            download_file(
                file_id="private-file-123",
                current_user=attacker,
                db=db,
            )

    assert error.value.status_code == 404
    assert error.value.detail == "File not found"

    query.filter.assert_called_once()

    security_log.assert_called_once()
    assert security_log.call_args.args[0] == "FILE_ACCESS_DENIED"
    assert security_log.call_args.kwargs["user_id"] == attacker.id


def test_download_query_checks_file_owner():
    attacker = SimpleNamespace(id=202, email="userb@example.com")

    query = MagicMock()
    query.filter.return_value.first.return_value = None

    db = MagicMock()
    db.query.return_value = query

    with pytest.raises(HTTPException) as error:
        download_file(
            file_id="private-file-123",
            current_user=attacker,
            db=db,
        )

    assert error.value.status_code == 404

    query.filter.assert_called_once()
    filters = query.filter.call_args.args

    assert len(filters) == 2
    assert "files.file_id" in str(filters[0])
    assert "files.owner_id" in str(filters[1])
