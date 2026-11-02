"""Reject dangerous image headers through the real profile form boundary."""

import struct
import zlib

import pytest
from django.test import Client
from django.urls import reverse
from PIL import Image

from apps.profiles.tests.factories import TraineeProfileFactory, photo_upload


def bomb_upload(pixels: int) -> object:
    """Build a tiny PNG with a valid CRC and a hostile declared image size."""
    file = photo_upload()
    content = bytearray(file.read())
    content[16:24] = struct.pack(">II", pixels, 1)
    content[29:33] = struct.pack(">I", zlib.crc32(content[12:29]))
    file.file.seek(0)
    file.file.truncate()
    file.file.write(content)
    file.file.seek(0)
    return file


@pytest.mark.django_db
@pytest.mark.parametrize("multiplier", [1, 2], ids=["bomb-warning", "bomb-error"])
def test_decompression_bomb_is_a_form_error(client: Client, multiplier: int) -> None:
    """Refuse huge declared dimensions with a validation page rather than a 500."""
    profile = TraineeProfileFactory()
    client.force_login(profile.user)
    upload = bomb_upload(Image.MAX_IMAGE_PIXELS * multiplier + 1)
    response = client.post(reverse("profiles:trainee_edit"), {"photo": upload})
    assert response.status_code == 200
    assert "photo" in response.context["form"].errors
    profile.refresh_from_db()
    assert not profile.photo
