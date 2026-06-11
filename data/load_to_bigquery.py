"""Load seed CSVs into BigQuery."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

try:
    from tqdm.auto import tqdm
except ImportError:
    class tqdm:  # type: ignore[no-redef]
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable
            self.desc = kwargs.get("desc", "")

        def __iter__(self):
            if self.iterable is None:
                return iter(())
            return iter(self.iterable)

        def __enter__(self):
            if self.desc:
                print(f"{self.desc}...")
            return self

        def __exit__(self, *_):
            return False

        def update(self, _=1):
            return None

        def set_postfix_str(self, _):
            return None

        @staticmethod
        def write(message):
            print(message)

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

parser = argparse.ArgumentParser(description="Load StreamWorks seed CSVs into BigQuery.")
parser.add_argument("--dry-run", action="store_true", help="Validate inputs and show progress without creating or overwriting tables.")
args = parser.parse_args()

PROJECT_ID = os.environ.get("BQ_PROJECT_ID") or os.environ.get("GCP_PROJECT_ID")
DATASET_ID = os.environ.get("BQ_RAW_DATASET") or os.environ.get("BIGQUERY_DATASET", "margintrust")
SEED_DIR = Path(__file__).parent / "seed_data"
SCHEMA_DIR = Path(__file__).parent / "schemas"

if not PROJECT_ID:
    raise SystemExit("BQ_PROJECT_ID or GCP_PROJECT_ID is required in .env or the shell to load seed data into BigQuery.")

credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
if credentials_path:
    path = Path(credentials_path).expanduser()
    if not path.is_absolute():
        path = ROOT_DIR / path
    credentials = service_account.Credentials.from_service_account_file(path)
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
else:
    client = bigquery.Client(project=PROJECT_ID)
dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"

tables = [
    "accounts",
    "contracts",
    "product_usage_events",
    "invoices",
    "opportunities",
    "customer_health",
    "marketing_spend",
    "support_tickets",
    "fivetran_connector_status",
    "metric_dependency_map",
]

with tqdm(total=2, desc="BigQuery setup", unit="step") as setup:
    setup.set_postfix_str("client ready")
    _ = client.project
    setup.update()

    setup.set_postfix_str("dataset")
    try:
        client.get_dataset(dataset_ref)
        tqdm.write(f"Dataset {dataset_ref} already exists.")
    except Exception:
        if args.dry_run:
            tqdm.write(f"Dataset {dataset_ref} would be created.")
            setup.update()
            raise SystemExit("Dry run stopped before dataset creation.")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        tqdm.write(f"Created dataset {dataset_ref}.")
    setup.update()

for table_name in tqdm(tables, desc="BigQuery tables", unit="table"):
    csv_path = SEED_DIR / f"{table_name}.csv"
    schema_path = SCHEMA_DIR / f"{table_name}.json"
    with tqdm(total=4, desc=f"  {table_name}", unit="step", leave=False) as phase:
        phase.set_postfix_str("validate csv")
        if not csv_path.exists():
            tqdm.write(f"  skipping {table_name}: CSV not found")
            continue
        csv_rows = max(0, sum(1 for _ in csv_path.open(newline="")) - 1)
        phase.update()

        phase.set_postfix_str(f"prepare schema, {csv_rows:,} rows")
        table_ref = f"{dataset_ref}.{table_name}"
        schema = client.schema_from_json(str(schema_path)) if schema_path.exists() else None
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            schema=schema,
            autodetect=schema is None,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        phase.update()

        if args.dry_run:
            phase.set_postfix_str("dry-run upload")
            phase.update()

            phase.set_postfix_str("dry-run verify")
            phase.update()
            tqdm.write(f"  {table_name}: {csv_rows} rows ready for load")
            continue

        phase.set_postfix_str("upload csv")
        with csv_path.open("rb") as f:
            job = client.load_table_from_file(f, table_ref, job_config=job_config)
        phase.update()

        phase.set_postfix_str("wait and verify")
        job.result()
        table = client.get_table(table_ref)
        phase.update()

    tqdm.write(f"  {table_name}: {table.num_rows} rows loaded")

if args.dry_run:
    tqdm.write("\nDry run complete. No BigQuery tables were created or overwritten.")
else:
    tqdm.write("\nAll tables loaded.")
