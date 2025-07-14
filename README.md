# 📺 YouTube Trending ETL Pipeline with Apache Airflow 3

An end‑to‑end **data‑engineering portfolio project** that

1. **Extracts** the complete “Trending / Most‑Popular” list from the YouTube Data API  
2. **Stores** the raw JSON in **Azure Blob Storage**  
3. **Transforms** and **loads** the data into an **Azure‑hosted PostgreSQL** table  
4. **Cleans up** the raw file once each load succeeds  

The project is orchestrated by a single **Apache Airflow 3 DAG** running in Docker, and demonstrates intermediate‑level Airflow patterns: XComs, custom helpers, secret management, dynamic pagination, Azure + Postgres hooks, and sequential task dependencies.

---

## 🔥 Why this project?

| Career Skill | Where it shows |
|--------------|----------------|
| Cloud‑native storage + compute | Uses Azure Blob + Azure PostgreSQL |
| Modern orchestration | Airflow 3 in Docker, with custom hooks/operators |
| External APIs & OAuth keys | YouTube Data API v3, API key stored in Airflow Variables |
| Robust ETL design | Pagination, retries, idempotent loads, cleanup |
| Intermediate Airflow concepts | XComs, Trigger Rules, TaskGroups, provider packages |

Use it as a template for **any API → Blob → Warehouse** workflow.

---

## 🗂 Folder Layout
```
youtube-etl-airflow/
│
├── dags/
│   ├── youtube_full_etl.py      # The orchestration DAG
│   ├── youtube_helpers.py       # YouTube API + pagination logic
│   └── blob_helpers.py          # Azure Blob helpers + transform/load
│
├── docker-compose.yaml          # Local Airflow stack
├── requirements.txt             # Python deps (exported from container)
├── .gitignore
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Stack |
|-------|-------|
| Orchestration | **Apache Airflow 3.0** (Docker) |
| Data Source   | **YouTube Data API v3** |
| Raw Storage   | **Azure Blob Storage** (container: `youtube-raw-data`) |
| Transform     | **pandas** (flatten JSON -> DataFrame) |
| Warehouse     | **Azure Database for PostgreSQL** |
| Providers     | `apache-airflow-providers-microsoft-azure`, `apache-airflow-providers-postgres` |

---

## 🛠️ Setup & Run Locally

> **Prerequisites**: Docker Desktop, Git, YouTube API key, Azure Storage account, Azure PostgreSQL instance.

1. **Clone**
   ```bash
   git clone https://github.com/<your-username>/youtube-etl-airflow.git
   cd youtube-etl-airflow
   ```

2. **Configure Airflow connections**
   | Connection ID | Type | What to enter |
   |---------------|------|---------------|
   | `azure_blob_conn` | *Azure Blob Storage* | Extra → `{"connection_string": "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"}` |
   | `postgres_default` | *Postgres* | host, db, user, pwd, port 5432, SSL = require |
   | Variable          |  | `youtube_api_key = <YOUR_KEY>` |

3. **Spin up Airflow**
   ```bash
   docker compose up -d
   ```

4. **Create target table**
   ```sql
   CREATE SCHEMA IF NOT EXISTS test;
   CREATE TABLE test.youtube_trending_raw (
       video_id        TEXT,
       published_at    TIMESTAMP,
       channel_id      TEXT,
       channel_title   TEXT,
       title           TEXT,
       description     TEXT,
       category_id     INT,
       tags            TEXT,
       view_count      BIGINT,
       like_count      BIGINT,
       comment_count   BIGINT,
       blob_filename   TEXT,
       load_ts         TIMESTAMP DEFAULT now()
   );
   ```

5. **Enable & Trigger DAG**
   - Airflow UI → `youtube_full_etl` → **On** → *Trigger*  
   - Watch tasks `fetch_and_upload → process_blob` succeed.

---

## 🏗️ DAG Architecture

```
fetch_and_upload   -->   process_blob
(YouTube API +          (download JSON,
Azure upload)            transform, load,
                         delete blob)
```
*Strict dependency chain prevents race conditions and guarantees exactly‑once processing.*

---

## 🔑 Key Implementation Details

| Feature | Code |
|---------|------|
| **Pagination** | `youtube_helpers.fetch_trending` loops through `nextPageToken` until all pages are fetched (≈ 50 per page). |
| **Temporary files** | Raw JSON saved to `/tmp`, then uploaded, then removed. |
| **XCom usage** | Upload task returns the blob name → consumed by the processing task. |
| **Blob cleanup** | Blob deleted only after Postgres commit (`TriggerRule.ALL_SUCCESS`). |
| **Tag column** | Stored as plain CSV (`tag1,tag2,...`) to avoid Postgres array literal issues. |

---

## 📊 What You Can Demo

- **Airflow UI screenshots**: Graph view, logs, XComs.
- **Azure Portal**: container briefly holds raw JSON.
- **Postgres**: `SELECT COUNT(*) FROM test.youtube_trending_raw;`
- **Extensibility**: Easily swap Azure for S3/GCS or add a reporting DAG (e.g., EmailOperator to mail daily top‑10 CSV).

---

## 🚀 Future Enhancements

- ✅ Change `tags` to `text[]` with psycopg2 `execute_values`.
- ✅ Add data‑quality checks (`GreatExpectationsOperator`).
- ✅ Deploy Airflow via Helm on AKS or use Astro/Cloud Composer.
- ✅ Build a Power BI dashboard on the warehouse table.
- ✅ Parameterize multiple regions via Airflow Variables + TaskGroups.

---

## 📝 Author

**Nikhil H** – *Data Engineer*  
[LinkedIn][https://www.linkedin.com/in/nikhilhanumanthaiah]

