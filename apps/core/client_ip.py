"""Read proxy headers only when an operator explicitly trusts the chain length."""

from ipaddress import ip_address

from django.conf import settings
from django.http import HttpRequest


def client_ip(request: HttpRequest) -> str:
    """Ignore spoofable forwarded IPs by default and take trusted Nth-from-right."""
    direct = request.META.get("REMOTE_ADDR") or "unknown"
    count = settings.TRUSTED_PROXY_COUNT
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    if count <= 0 or len(forwarded) < count:
        return direct
    try:
        return str(ip_address(forwarded[-count].strip()))
    except ValueError:
        return direct
