import os
import pytest
from pathlib import Path

from sheet import GoogleSheetsClient


def test_guess_mimetype_png_and_jpg():
    assert GoogleSheetsClient._guess_mimetype('image.png') == 'image/png'
    assert GoogleSheetsClient._guess_mimetype('IMAGE.PNG') == 'image/png'
    assert GoogleSheetsClient._guess_mimetype('photo.jpg') == 'image/jpeg'
    assert GoogleSheetsClient._guess_mimetype('photo.JPEG') == 'image/jpeg'
    # default to jpeg for unknown extensions
    assert GoogleSheetsClient._guess_mimetype('file.unknown') == 'image/jpeg'


def test_resolve_json_path_absolute(tmp_path):
    p = tmp_path / 'sa.json'
    p.write_text('{}')

    class D: pass

    D.resolve = GoogleSheetsClient._resolve_json_path
    resolved = D().resolve(str(p))
    assert Path(resolved).exists()
    assert Path(resolved).samefile(p)


def test_resolve_json_path_relative_prefers_credential_json(tmp_path, monkeypatch):
    # create credential.json in cwd
    cred = tmp_path / 'credential.json'
    cred.write_text('{}')

    monkeypatch.chdir(tmp_path)

    class D: pass

    D.resolve = GoogleSheetsClient._resolve_json_path
    # give a non-existing path, should fallback to credential.json
    resolved = D().resolve('nonexistent.json')
    assert Path(resolved).exists()
    assert Path(resolved).samefile(cred)


def test_resolve_json_path_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class D: pass

    D.resolve = GoogleSheetsClient._resolve_json_path
    with pytest.raises(FileNotFoundError):
        D().resolve('no_such_file.json')
