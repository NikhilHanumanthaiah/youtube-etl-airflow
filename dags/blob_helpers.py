import json
from pathlib import Path
import pandas as pd
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2.extras as extras

CONTAINER = "raw-data-airflow"

# ── Azure Blob helpers ─────────────────────────────────────

def upload_blob(local_path: Path, blob_name: str):
    WasbHook("azure_blob_conn").load_file(
        file_path=local_path.as_posix(),
        container_name=CONTAINER,
        blob_name=blob_name,
        overwrite=True,
    )

def download_blob(blob_name: str, dest: Path) -> Path:
    WasbHook("azure_blob_conn").get_file(dest.as_posix(), CONTAINER, blob_name)
    return dest

def delete_blob(blob_name: str):
    WasbHook("azure_blob_conn").delete_file(CONTAINER, blob_name)

def list_blobs() -> list[str]:
    return WasbHook("azure_blob_conn").get_blobs_list(CONTAINER)

# ── Transform + load ───────────────────────────────────────

def flatten_json(local_json: Path) -> pd.DataFrame:
    data = json.loads(local_json.read_text())
    rows = []

    for item in data.get("items", []):
        s = item.get("snippet", {})
        stats = item.get("statistics", {})

        rows.append(
            dict(
                video_id=item.get("id"),
                published_at=s.get("publishedAt"),
                channel_id=s.get("channelId"),
                channel_title=s.get("channelTitle"),
                title=s.get("title"),
                description=s.get("description"),
                category_id=int(s.get("categoryId", 0)),
                tags=s.get("tags", []),
                default_language=s.get("defaultLanguage"),
                default_audiol_anguage= s.get("defaultAudioLanguage"),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
            )
        )

    return pd.DataFrame(rows)

def load_dataframe(df: pd.DataFrame, blob_name: str):
    df['blob_filename'] = blob_name
    pg = PostgresHook('postgres_default')
    conn = pg.get_conn()
    with conn.cursor() as cur:
        extras.execute_values(
            cur,
            """
            INSERT INTO test.youtube_trending_raw (
                video_id, published_at, channel_id, channel_title,
                title, description, category_id,tags,defaultlanguage,defaultaudiolanguage,
                view_count, like_count, comment_count,blob_filename
            ) VALUES %s
            """,
            df.itertuples(index=False, name=None)
        )
    conn.commit()