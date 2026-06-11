"""Create the MarginTrust BigQuery analytics views."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account
from tqdm.auto import tqdm

ROOT_DIR = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT_DIR / "sql" / "analytics_views"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _client(project_id: str) -> bigquery.Client:
    credentials_path = _env("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        path = Path(credentials_path).expanduser()
        if not path.is_absolute():
            path = ROOT_DIR / path
        credentials = service_account.Credentials.from_service_account_file(path)
        return bigquery.Client(project=project_id, credentials=credentials)
    return bigquery.Client(project=project_id)


def _render(template: str, replacements: dict[str, str]) -> str:
    sql = template
    for key, value in replacements.items():
        sql = sql.replace(f"{{{{{key}}}}}", value)
    return sql


def _table_exists(client: bigquery.Client, project_id: str, dataset_id: str, table_name: str) -> bool:
    try:
        client.get_table(f"{project_id}.{dataset_id}.{table_name}")
        return True
    except Exception:
        return False


def _choose_table(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    label: str,
    candidates: list[str],
) -> str:
    for table_name in candidates:
        if _table_exists(client, project_id, dataset_id, table_name):
            tqdm.write(f"{label}: using raw table `{project_id}.{dataset_id}.{table_name}`")
            return table_name
    candidate_list = ", ".join(candidates)
    raise SystemExit(f"Could not find a raw {label} table. Tried: {candidate_list}")


def _inspect_table(client: bigquery.Client, project_id: str, dataset_id: str, table_name: str) -> None:
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    table = client.get_table(table_ref)
    fields = ", ".join(field.name for field in table.schema)
    tqdm.write(f"{table_ref}: {table.num_rows:,} rows, fields: {fields}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create BigQuery analytics views for MarginTrust AI.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect schemas and print planned views without writing DDL.")
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")

    project_id = _env("BQ_PROJECT_ID") or _env("GCP_PROJECT_ID")
    raw_dataset = _env("BQ_RAW_DATASET") or _env("BIGQUERY_DATASET", "margintrust")
    analytics_dataset = _env("BQ_ANALYTICS_DATASET", "margintrust_analytics")
    bq_location = _env("BQ_LOCATION", "US")

    if not project_id:
        raise SystemExit("Set BQ_PROJECT_ID or GCP_PROJECT_ID before creating analytics views.")
    if not SQL_DIR.exists():
        raise SystemExit(f"SQL directory not found: {SQL_DIR}")

    client = _client(project_id)

    opportunities_table = _choose_table(
        client,
        project_id,
        raw_dataset,
        "opportunities",
        ["crm_opportunities", "opportunities"],
    )
    connector_status_table = _choose_table(
        client,
        project_id,
        raw_dataset,
        "connector status",
        ["connector_status", "fivetran_connector_status"],
    )

    raw_tables = [
        "accounts",
        "contracts",
        "product_usage_events",
        "invoices",
        opportunities_table,
        "marketing_spend",
        "support_tickets",
        connector_status_table,
        "metric_dependency_map",
    ]

    tqdm.write("\nInspecting raw BigQuery schemas:")
    for table_name in raw_tables:
        _inspect_table(client, project_id, raw_dataset, table_name)

    dataset_ref = f"{project_id}.{analytics_dataset}"
    if args.dry_run:
        tqdm.write(f"\nDry run: analytics dataset `{dataset_ref}` would be created if missing.")
    else:
        try:
            client.get_dataset(dataset_ref)
            tqdm.write(f"\nAnalytics dataset `{dataset_ref}` already exists.")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = bq_location
            client.create_dataset(dataset)
            tqdm.write(f"\nCreated analytics dataset `{dataset_ref}` in {bq_location}.")

    replacements = {
        "PROJECT_ID": project_id,
        "RAW_DATASET": raw_dataset,
        "ANALYTICS_DATASET": analytics_dataset,
        "OPPORTUNITIES_TABLE": opportunities_table,
        "CONNECTOR_STATUS_TABLE": connector_status_table,
    }

    sql_files = sorted(SQL_DIR.glob("*.sql"))
    if not sql_files:
        raise SystemExit(f"No SQL files found in {SQL_DIR}")

    for sql_file in tqdm(sql_files, desc="Analytics views", unit="view"):
        rendered = _render(sql_file.read_text(), replacements)
        view_name = sql_file.stem.split("_", 1)[-1]
        if args.dry_run:
            tqdm.write(f"Would create or replace `{dataset_ref}.{view_name}` from {sql_file.name}")
            continue
        job = client.query(rendered)
        job.result()
        tqdm.write(f"Created or replaced `{dataset_ref}.{view_name}`")

    if args.dry_run:
        tqdm.write("\nDry run complete. No analytics views were created or replaced.")
    else:
        tqdm.write("\nAnalytics layer is ready.")


if __name__ == "__main__":
    main()
