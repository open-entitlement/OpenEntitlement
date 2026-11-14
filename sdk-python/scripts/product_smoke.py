"""Evaluate a live Product with the Python SDK; accepts credentials only on stdin."""
import json
import sys

from openentitlement import Catalog, RemoteProvider, create_client

settings = json.load(sys.stdin)
catalog = Catalog.from_dict({"features": [{"code": "limits", "name": "Limits", "privileges": [
    {"key": "seats", "valueType": "integer", "default": 0},
]}]})
client = create_client(catalog=catalog, provider=RemoteProvider(
    settings["url"], product=settings["product"], token=settings["token"],
))
value = client.get_limit("seats", {"organization_id": "acme"})
assert value == 25, f"Expected 25 seats, received {value}"
print("Python Product SDK: acme_product / acme / seats = 25")
