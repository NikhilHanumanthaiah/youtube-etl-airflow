from datetime import datetime, timezone
from pathlib import Path
import json, requests
from airflow.models import Variable

def fetch_trending(region: str = "IN", target_count: int | None = None) -> tuple[Path, str]:
    """
    Download ALL trending videos for the given region.

    • If target_count is None → fetch every page until the API stops returning nextPageToken.
    • If target_count is an int  → stop once that many items are collected.
    Returns: (local_path, filename)
    """
    api_key = Variable.get("youtube_api_key")
    url     = "https://www.googleapis.com/youtube/v3/videos"

    params_base = {
        "part"      : "snippet,statistics",
        "chart"     : "mostPopular",
        "regionCode": region,
        "maxResults": 50,           # hard cap per request for this endpoint
        "key"       : api_key,
    }

    all_items, page_token = [], None
    while True:
        params = params_base.copy()
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        all_items.extend(payload.get("items", []))

        # Stop if we've hit the target_count (when provided)
        if target_count and len(all_items) >= target_count:
            all_items = all_items[:target_count]
            break

        page_token = payload.get("nextPageToken")
        if not page_token:
            break  # no more pages

    # Build final payload
    payload_final = {
        "kind"       : "youtube#videoListResponse",
        "etag"       : payload.get("etag"),
        "page_info"  : {"items_fetched": len(all_items)},
        "items"      : all_items,
        "fetched_at" : datetime.now(timezone.utc).isoformat()
    }

    ts        = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename  = f"youtube_trending_{region}_{ts}.json"
    local_path = Path("/tmp") / filename
    local_path.write_text(json.dumps(payload_final, indent=2))

    return local_path, filename
