from __future__ import annotations
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# ── Add scripts/ to Python path ──────────────────────

from youtube_helpers import fetch_trending
import blob_helpers as bh

TMP = Path(tempfile.gettempdir())

def fetch_and_upload(**_):
    local, blob = fetch_trending(region="IN")
    bh.upload_blob(local, blob)
    return blob  # XCom → downstream

def process_blob(blob_name: str, **_):
    local_path = bh.download_blob(blob_name, TMP / blob_name)
    df = bh.flatten_json(local_path)
    bh.load_dataframe(df, blob_name)
    bh.delete_blob(blob_name)
    local_path.unlink(missing_ok=True)  # clean /tmp

with DAG(
    dag_id="youtube_full_etl",
    start_date=datetime.now() - timedelta(days=1),
    schedule="@daily",
    catchup=False,
    tags=["youtube","azure","postgres"],
) as dag:

    fetch_upload = PythonOperator(
        task_id="fetch_and_upload",
        python_callable=fetch_and_upload,   # returns blob name
    )

    def process_new_blob(ti, **_):
        blob_name = ti.xcom_pull(task_ids="fetch_and_upload")
        process_blob(blob_name)             # call helper that DL → transform → load → delete

    process_task = PythonOperator(
        task_id="process_blob",
        python_callable=process_new_blob,
    )

    fetch_upload >> process_task
