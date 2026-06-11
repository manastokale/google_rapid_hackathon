"""Synthetic data generator for MarginTrust AI / StreamWorks Cloud demo.

Generates 10 interconnected CSV files with stable headline POC storylines:
1. $126K underbilling exposure across 14 accounts
2. $420K annual expansion revenue gap across 8 accounts
3. Trust score of 62/100 on revenue dashboard due to stale/broken connectors
4. $18K duplicate marketing spend leakage

The remaining rows add broad supporting coverage for the POC: healthy accounts,
fully billed overages, high usage with an existing expansion opportunity, near
limit usage, sub-threshold invoice variance, underutilization, renewal pressure,
churn risk, stale customer health data, ticket spikes, and multiple connector
health states.

Usage:
    python data/generate_seed_data.py
"""

import csv
import random
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

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

OUTPUT_DIR = Path(__file__).parent / "seed_data"
OUTPUT_DIR.mkdir(exist_ok=True)

random.seed(42)

NOW = datetime(2025, 7, 10, 14, 0, 0)
BILLING_DAYS = 30
MARKETING_DAYS = 90
NUM_ACCOUNTS = 750

TIERS = ["Enterprise", "Growth", "Starter"]
ACCOUNT_EXECS = ["Sarah Chen", "Marcus Johnson", "Priya Patel", "James Wilson", "Ana Rodriguez"]
CSMS = ["Mike Rivera", "Lisa Chang", "Tom Bradley", "Rachel Kim", "David Park"]
EVENT_TYPES = ["api_call", "data_processed_gb", "compute_minutes"]
CHANNELS = ["google_ads", "linkedin", "content_marketing", "events", "webinars", "email"]
TICKET_CATEGORIES = ["billing", "technical", "feature_request", "bug", "onboarding"]

COMPANY_NAMES = [
    "DataStream Corp", "CloudPeak Analytics", "MetricFlow Inc", "SignalPath Systems",
    "NexusData Solutions", "PulsePoint Technologies", "StreamForge Labs", "DataBridge AI",
    "FlowState Computing", "Quantum Metrics Corp", "TerraData Systems", "AeroSync Inc",
    "VortexCloud Solutions", "PrismAnalytics Co", "CipherStream Tech",
    "HyperScale Data", "MeridianFlow Inc", "ApexCloud Systems", "NovaMetrics Labs",
    "ZenithData Corp", "SynapseStream Inc", "VertexAnalytics Co", "PolarisData Tech",
    "EchoStream Solutions", "AtlasFlow Computing", "OrbitalData Inc",
    "SpectrumCloud Labs", "VectorMetrics Corp", "TitanStream Systems", "GenesiData Analytics",
    "CatalystCloud Co", "IonFlow Technologies", "NimbusData Corp", "ArcLight Analytics",
    "TridentStream Inc", "KineticData Labs", "StellarFlow Systems", "PhoenixMetrics Co",
    "DeltaCloud Solutions", "HorizonData Tech", "PinnacleStream Corp", "RadiantFlow Inc",
    "QuantumBridge Labs", "NexGenData Systems", "AlphaStream Analytics",
    "OmegaCloud Corp", "FusionMetrics Inc", "ZephyrData Solutions", "CosmicFlow Tech",
    "InfinityStream Labs", "AuroraData Corp", "TerraForge Analytics",
    "CelestialCloud Inc", "VanguardMetrics Co", "ThunderData Systems",
    "LuminousStream Labs", "EternalFlow Corp", "MajesticData Inc",
    "SovereignCloud Tech", "GalacticMetrics Solutions",
]

COMPANY_PREFIXES = [
    "Northstar", "BluePeak", "ClearPath", "Evergreen", "Silverline", "Keystone",
    "Summit", "Riverbend", "Ironclad", "BrightForge", "CoreSignal", "TrueNorth",
]
COMPANY_INDUSTRIES = [
    "Analytics", "Cloud", "Data", "Metrics", "Ops", "Revenue", "Workflow",
    "Automation", "Security", "Commerce", "Health", "Logistics",
]
COMPANY_SUFFIXES = ["Labs", "Systems", "Group", "Technologies", "Software", "AI", "Networks"]

UNDERBILLED_ACCOUNT_INDICES = [2, 6, 8, 13, 15, 19, 22, 25, 28, 31, 34, 37, 41, 44]
EXPANSION_GAP_INDICES = [3, 7, 11, 16, 20, 26, 33, 39]
UNDERBILLING_TARGETS = [15000, 13000, 12000, 11000, 10500, 9500, 9000, 8500, 8000, 7500, 7000, 6500, 5000, 3500]
EXPANSION_TARGETS = [75000, 68000, 62000, 55000, 50000, 45000, 37000, 28000]
DUPLICATE_SPEND_TARGETS = [5000, 4000, 3000, 2500, 2000, 1500]


def distribute_total(total: int, parts: int) -> list[int]:
    base = total // parts
    values = [base] * parts
    for idx in range(total - base * parts):
        values[idx % parts] += 1
    random.shuffle(values)
    return values


def scenario_for_index(idx: int) -> str:
    if idx in UNDERBILLED_ACCOUNT_INDICES:
        return "underbilling"
    if idx in EXPANSION_GAP_INDICES:
        return "expansion_gap"
    if idx % 53 == 0:
        return "churned"
    if idx % 47 == 0:
        return "churn_risk"
    if idx % 43 == 0:
        return "ticket_spike"
    if idx % 37 == 0:
        return "paid_overage"
    if idx % 31 == 0:
        return "high_usage_with_expansion"
    if idx % 29 == 0:
        return "subthreshold_invoice_variance"
    if idx % 23 == 0:
        return "near_limit"
    if idx % 19 == 0:
        return "underutilized"
    if idx % 17 == 0:
        return "renewal_soon"
    if idx % 13 == 0:
        return "stale_health"
    if idx % 11 == 0:
        return "seasonal_spike"
    return "healthy"


def company_name(idx: int) -> str:
    if idx < len(COMPANY_NAMES):
        return COMPANY_NAMES[idx]
    prefix = COMPANY_PREFIXES[idx % len(COMPANY_PREFIXES)]
    industry = COMPANY_INDUSTRIES[(idx // len(COMPANY_PREFIXES)) % len(COMPANY_INDUSTRIES)]
    suffix = COMPANY_SUFFIXES[(idx // (len(COMPANY_PREFIXES) * len(COMPANY_INDUSTRIES))) % len(COMPANY_SUFFIXES)]
    return f"{prefix}{industry} {suffix} {idx + 1:03d}"


def tier_and_segment(scenario: str) -> tuple[str, str]:
    if scenario in {"underbilling", "expansion_gap", "paid_overage", "high_usage_with_expansion"}:
        tier = random.choices(["Enterprise", "Growth"], [0.7, 0.3])[0]
    elif scenario in {"churn_risk", "underutilized"}:
        tier = random.choices(["Growth", "Starter"], [0.55, 0.45])[0]
    else:
        tier = random.choices(TIERS, [0.28, 0.5, 0.22])[0]

    segment = "Enterprise" if tier == "Enterprise" else "Mid-Market" if tier == "Growth" else "SMB"
    return tier, segment


def arr_for_tier(tier: str) -> float:
    if tier == "Enterprise":
        return round(random.uniform(180000, 680000), 2)
    if tier == "Growth":
        return round(random.uniform(42000, 220000), 2)
    return round(random.uniform(8000, 42000), 2)


def generate_accounts():
    rows = []
    for idx in tqdm(range(NUM_ACCOUNTS), desc="accounts", unit="account", leave=False):
        scenario = scenario_for_index(idx)
        tier, segment = tier_and_segment(scenario)
        arr = arr_for_tier(tier)
        status = "churned" if scenario == "churned" else "active"
        pricing_model = "usage-based" if tier in {"Enterprise", "Growth"} else random.choice(["usage-based", "hybrid"])

        rows.append({
            "account_id": f"ACC-{idx + 1:03d}",
            "account_name": company_name(idx),
            "tier": tier,
            "arr": arr,
            "mrr": round(arr / 12, 2),
            "pricing_model": pricing_model,
            "owner": random.choice(ACCOUNT_EXECS),
            "csm": random.choice(CSMS),
            "segment": segment,
            "status": status,
            "created_at": (NOW - timedelta(days=random.randint(45, 900))).isoformat(timespec="seconds"),
        })
    return rows


def generate_contracts(accounts):
    rows = []
    under_target_map = dict(zip(UNDERBILLED_ACCOUNT_INDICES, UNDERBILLING_TARGETS))
    expansion_target_map = dict(zip(EXPANSION_GAP_INDICES, EXPANSION_TARGETS))

    for acc in tqdm(accounts, desc="contracts", unit="account", leave=False):
        if acc["status"] == "churned":
            continue

        idx = int(acc["account_id"].split("-")[1]) - 1
        scenario = scenario_for_index(idx)
        if idx in under_target_map:
            included = 120000 + (idx % 5) * 10000
            overage = 0.05
        elif idx in expansion_target_map:
            included = 90000 + (idx % 4) * 10000
            overage = 0.05
        elif scenario in {"paid_overage", "high_usage_with_expansion"}:
            included = 70000 + (idx % 12) * 6000
            overage = round(random.uniform(0.025, 0.045), 4)
        elif scenario == "subthreshold_invoice_variance":
            included = 45000 + (idx % 8) * 4000
            overage = round(random.uniform(0.022, 0.04), 4)
        elif acc["tier"] == "Enterprise":
            included = random.randint(80000, 240000)
            overage = round(random.uniform(0.008, 0.025), 4)
        elif acc["tier"] == "Growth":
            included = random.randint(24000, 85000)
            overage = round(random.uniform(0.015, 0.045), 4)
        else:
            included = random.randint(5000, 22000)
            overage = round(random.uniform(0.03, 0.065), 4)

        if scenario == "renewal_soon":
            end = NOW + timedelta(days=random.randint(15, 45))
            start = end - timedelta(days=365)
        else:
            start = NOW - timedelta(days=random.randint(45, 320))
            end = start + timedelta(days=365)

        rows.append({
            "contract_id": f"CTR-{acc['account_id'].split('-')[1]}",
            "account_id": acc["account_id"],
            "pricing_type": acc["pricing_model"],
            "included_usage_units": included,
            "overage_rate": round(overage, 4),
            "contract_start": start.date().isoformat(),
            "contract_end": end.date().isoformat(),
            "renewal_date": end.date().isoformat(),
            "auto_renew": random.choice([True, False]),
        })
    return rows


def monthly_usage_units(acc: dict, contract: dict) -> int:
    idx = int(acc["account_id"].split("-")[1]) - 1
    scenario = scenario_for_index(idx)
    included = int(contract["included_usage_units"])
    overage = float(contract["overage_rate"])
    under_target_map = dict(zip(UNDERBILLED_ACCOUNT_INDICES, UNDERBILLING_TARGETS))
    expansion_target_map = dict(zip(EXPANSION_GAP_INDICES, EXPANSION_TARGETS))

    if idx in under_target_map:
        return included + round(under_target_map[idx] / overage)
    if idx in expansion_target_map:
        return included + round((expansion_target_map[idx] / 12) / overage)
    if scenario == "paid_overage":
        return int(included * random.uniform(1.24, 1.55))
    if scenario == "high_usage_with_expansion":
        return int(included * random.uniform(1.35, 1.8))
    if scenario == "subthreshold_invoice_variance":
        return included + max(1, round(85 / overage))
    if scenario == "near_limit":
        return int(included * random.uniform(0.96, 1.0))
    if scenario == "underutilized":
        return int(included * random.uniform(0.22, 0.45))
    if scenario == "churn_risk":
        return int(included * random.uniform(0.25, 0.55))
    if scenario == "seasonal_spike":
        return int(included * random.uniform(1.02, 1.12))
    return int(included * random.uniform(0.52, 0.98))


def generate_usage_events(accounts, contracts):
    rows = []
    contract_map = {c["account_id"]: c for c in contracts}

    for acc in tqdm(accounts, desc="usage events", unit="account", leave=False):
        if acc["status"] == "churned" or acc["account_id"] not in contract_map:
            continue

        monthly_usage = monthly_usage_units(acc, contract_map[acc["account_id"]])
        event_count = BILLING_DAYS * len(EVENT_TYPES)
        quantities = distribute_total(monthly_usage, event_count)
        quantity_idx = 0

        for day_offset in range(BILLING_DAYS):
            event_date = NOW - timedelta(days=day_offset)
            for event_type in EVENT_TYPES:
                rows.append({
                    "event_id": str(uuid.uuid4())[:12],
                    "account_id": acc["account_id"],
                    "event_type": event_type,
                    "quantity": quantities[quantity_idx],
                    "event_timestamp": (
                        event_date - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    ).isoformat(timespec="seconds"),
                    "source_system": "product_telemetry",
                })
                quantity_idx += 1
    return rows


def generate_invoices(accounts, contracts, usage_events):
    rows = []
    contract_map = {c["account_id"]: c for c in contracts}
    usage_by_account: dict[str, int] = {}
    for event in tqdm(usage_events, desc="invoice usage rollup", unit="event", leave=False):
        usage_by_account[event["account_id"]] = usage_by_account.get(event["account_id"], 0) + int(event["quantity"])

    for acc in tqdm(accounts, desc="invoices", unit="account", leave=False):
        if acc["status"] == "churned" or acc["account_id"] not in contract_map:
            continue

        idx = int(acc["account_id"].split("-")[1]) - 1
        scenario = scenario_for_index(idx)
        contract = contract_map[acc["account_id"]]
        actual_usage = usage_by_account.get(acc["account_id"], 0)
        included = int(contract["included_usage_units"])
        overage = float(contract["overage_rate"])
        expected_overage = round(max(0, (actual_usage - included) * overage), 2)

        if idx in UNDERBILLED_ACCOUNT_INDICES:
            usage_amount = 0.0
        elif scenario == "subthreshold_invoice_variance":
            usage_amount = round(max(0, expected_overage - 85), 2)
        elif idx % 67 == 0:
            usage_amount = round(expected_overage + random.uniform(25, 125), 2)
        else:
            usage_amount = expected_overage

        base_amount = float(acc["mrr"])
        rows.append({
            "invoice_id": f"INV-{acc['account_id'].split('-')[1]}-{NOW.strftime('%Y%m')}",
            "account_id": acc["account_id"],
            "billing_period_start": (NOW - timedelta(days=BILLING_DAYS)).date().isoformat(),
            "billing_period_end": NOW.date().isoformat(),
            "base_amount": round(base_amount, 2),
            "usage_amount": round(usage_amount, 2),
            "total_amount": round(base_amount + usage_amount, 2),
            "status": random.choices(["paid", "pending", "past_due", "failed"], [0.72, 0.18, 0.08, 0.02])[0],
            "issued_at": (NOW - timedelta(days=random.randint(1, 7))).isoformat(timespec="seconds"),
        })
    return rows


def needs_expansion_opportunity(idx: int) -> bool:
    scenario = scenario_for_index(idx)
    if idx in EXPANSION_GAP_INDICES:
        return False
    if idx in UNDERBILLED_ACCOUNT_INDICES:
        return True
    if scenario in {"paid_overage", "high_usage_with_expansion", "seasonal_spike"}:
        return True
    return random.random() > 0.82


def generate_opportunities(accounts):
    rows = []
    for acc in tqdm(accounts, desc="opportunities", unit="account", leave=False):
        if acc["status"] == "churned":
            continue

        idx = int(acc["account_id"].split("-")[1]) - 1
        scenario = scenario_for_index(idx)
        suffix = acc["account_id"].split("-")[1]
        renewal_stage = "negotiation" if scenario == "renewal_soon" else random.choice(["qualification", "proposal", "negotiation"])

        rows.append({
            "opportunity_id": f"OPP-REN-{suffix}",
            "account_id": acc["account_id"],
            "opportunity_name": f"{acc['account_name']} - Annual Renewal",
            "stage": renewal_stage,
            "amount": acc["arr"],
            "close_date": (NOW + timedelta(days=random.randint(15, 180))).date().isoformat(),
            "type": "renewal",
            "owner": acc["owner"],
            "created_at": (NOW - timedelta(days=random.randint(10, 90))).isoformat(timespec="seconds"),
        })

        if needs_expansion_opportunity(idx):
            rows.append({
                "opportunity_id": f"OPP-EXP-{suffix}",
                "account_id": acc["account_id"],
                "opportunity_name": f"{acc['account_name']} - Usage Expansion",
                "stage": random.choice(["prospecting", "qualification", "proposal", "closed_lost"]),
                "amount": round(float(acc["arr"]) * random.uniform(0.18, 0.85), 2),
                "close_date": (NOW + timedelta(days=random.randint(20, 150))).date().isoformat(),
                "type": "expansion",
                "owner": acc["owner"],
                "created_at": (NOW - timedelta(days=random.randint(5, 45))).isoformat(timespec="seconds"),
            })
    return rows


def generate_customer_health(accounts):
    rows = []
    for acc in tqdm(accounts, desc="customer health", unit="account", leave=False):
        if acc["status"] == "churned":
            continue

        idx = int(acc["account_id"].split("-")[1]) - 1
        scenario = scenario_for_index(idx)
        if idx in UNDERBILLED_ACCOUNT_INDICES or idx in EXPANSION_GAP_INDICES:
            health = random.randint(78, 96)
            churn_risk = "low"
            adoption = "high"
            nps = random.randint(48, 90)
            last_login = NOW - timedelta(hours=random.randint(1, 36))
        elif scenario == "churn_risk":
            health = random.randint(20, 48)
            churn_risk = "high"
            adoption = "low"
            nps = random.randint(-55, 5)
            last_login = NOW - timedelta(days=random.randint(14, 45))
        elif scenario == "underutilized":
            health = random.randint(35, 64)
            churn_risk = random.choice(["medium", "high"])
            adoption = "low"
            nps = random.randint(-30, 25)
            last_login = NOW - timedelta(days=random.randint(6, 24))
        elif scenario == "ticket_spike":
            health = random.randint(42, 70)
            churn_risk = random.choice(["medium", "high"])
            adoption = random.choice(["medium", "high"])
            nps = random.randint(-20, 45)
            last_login = NOW - timedelta(hours=random.randint(8, 96))
        else:
            health = random.randint(55, 94)
            churn_risk = random.choices(["low", "medium", "high"], [0.68, 0.25, 0.07])[0]
            adoption = random.choices(["low", "medium", "high"], [0.18, 0.42, 0.4])[0]
            nps = random.randint(-10, 85)
            last_login = NOW - timedelta(hours=random.randint(1, 168))

        updated = NOW - timedelta(days=random.randint(5, 14)) if scenario == "stale_health" else NOW - timedelta(hours=random.randint(1, 18))
        rows.append({
            "health_id": f"HLT-{acc['account_id'].split('-')[1]}",
            "account_id": acc["account_id"],
            "health_score": health,
            "churn_risk": churn_risk,
            "product_adoption": adoption,
            "last_login": last_login.isoformat(timespec="seconds"),
            "nps_score": nps,
            "updated_at": updated.isoformat(timespec="seconds"),
        })
    return rows


def generate_marketing_spend():
    rows = []
    campaigns = [
        "Enterprise Webinar Series", "Cloud Analytics Content Hub", "LinkedIn ABM Campaign",
        "Google Ads - Brand", "Google Ads - Product", "Annual User Conference",
        "Developer Community Events", "Email Nurture - Enterprise", "Analyst Report Sponsorship",
        "Partner Co-Marketing", "Usage Expansion Plays", "Customer Proof Campaign",
        "Competitive Takeout", "Finance Leader Roundtable", "RevOps Field Dinner",
        "Product-Led Growth Retargeting",
    ]

    for day_offset in tqdm(range(MARKETING_DAYS), desc="marketing spend", unit="day", leave=False):
        spend_date = (NOW - timedelta(days=day_offset)).date()
        for campaign in random.sample(campaigns, random.randint(6, 12)):
            spend = round(random.uniform(300, 9500), 2)
            rows.append({
                "spend_id": str(uuid.uuid4())[:12],
                "campaign_name": campaign,
                "channel": random.choice(CHANNELS),
                "spend_amount": spend,
                "attributed_revenue": round(spend * random.uniform(0.35, 3.4), 2),
                "leads_generated": random.randint(1, 75),
                "spend_date": spend_date.isoformat(),
                "source_system": "marketing_platform",
            })

    duplicate_date = (NOW - timedelta(days=2)).date().isoformat()
    for idx, spend in enumerate(DUPLICATE_SPEND_TARGETS, start=1):
        original = {
            "spend_id": f"SPEND-DUP-{idx}-A",
            "campaign_name": f"Duplicated Spend Control {idx}",
            "channel": "linkedin" if idx % 2 else "google_ads",
            "spend_amount": spend,
            "attributed_revenue": round(spend * 1.4, 2),
            "leads_generated": 10 + idx,
            "spend_date": duplicate_date,
            "source_system": "marketing_platform",
        }
        duplicate = dict(original)
        duplicate["spend_id"] = f"SPEND-DUP-{idx}-B"
        rows.extend([original, duplicate])
    return rows


def generate_support_tickets(accounts):
    rows = []
    subjects = {
        "billing": ["Incorrect invoice amount", "Missing overage charges", "Payment processing issue", "Billing cycle question"],
        "technical": ["API latency spike", "Data sync failure", "Authentication error", "Rate limiting issue"],
        "feature_request": ["Custom dashboard request", "API v2 access", "Bulk export capability", "SSO integration"],
        "bug": ["Data duplication in reports", "Dashboard not loading", "Incorrect usage metrics", "Export file corrupted"],
        "onboarding": ["Team training request", "Integration setup help", "Migration assistance", "Documentation question"],
    }

    for acc in tqdm(accounts, desc="support tickets", unit="account", leave=False):
        if acc["status"] == "churned":
            continue

        idx = int(acc["account_id"].split("-")[1]) - 1
        scenario = scenario_for_index(idx)
        if scenario == "ticket_spike":
            ticket_count = random.randint(8, 14)
        elif scenario == "churn_risk":
            ticket_count = random.randint(5, 10)
        elif idx in UNDERBILLED_ACCOUNT_INDICES:
            ticket_count = random.randint(2, 5)
        elif idx in EXPANSION_GAP_INDICES:
            ticket_count = random.randint(1, 4)
        else:
            ticket_count = random.randint(0, 4)

        for _ in range(ticket_count):
            category = random.choice(TICKET_CATEGORIES)
            if scenario == "ticket_spike":
                category = random.choice(["technical", "bug", "billing"])
            if scenario == "churn_risk":
                category = random.choice(["technical", "bug", "onboarding"])

            created = NOW - timedelta(days=random.randint(0, 75))
            resolved = created + timedelta(hours=random.randint(2, 168)) if random.random() > 0.34 else None
            priority = random.choices(["low", "medium", "high", "critical"], [0.28, 0.42, 0.22, 0.08])[0]
            if scenario in {"ticket_spike", "churn_risk"}:
                priority = random.choices(["medium", "high", "critical"], [0.25, 0.5, 0.25])[0]

            rows.append({
                "ticket_id": f"TKT-{str(uuid.uuid4())[:8]}",
                "account_id": acc["account_id"],
                "subject": random.choice(subjects[category]),
                "priority": priority,
                "status": "resolved" if resolved else random.choice(["open", "in_progress"]),
                "created_at": created.isoformat(timespec="seconds"),
                "resolved_at": resolved.isoformat(timespec="seconds") if resolved else "",
                "category": category,
            })
    return rows


def generate_connector_status():
    return [
        {
            "connector_id": "conn-product-telemetry",
            "connector_name": "product_telemetry",
            "source_system": "Usage Tracking",
            "destination_table": "product_usage_events",
            "status": "delayed",
            "last_sync_completed": (NOW - timedelta(hours=19)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 15,
            "rows_synced_last": 8420,
            "schema_changes_detected": False,
            "error_message": "Sync delayed: upstream rate limiting detected",
            "owner": "Alex Thompson",
        },
        {
            "connector_id": "conn-stripe-billing",
            "connector_name": "stripe_billing",
            "source_system": "Billing",
            "destination_table": "invoices",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=12)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 15,
            "rows_synced_last": 4210,
            "schema_changes_detected": False,
            "error_message": "",
            "owner": "Alex Thompson",
        },
        {
            "connector_id": "conn-salesforce-crm",
            "connector_name": "salesforce_crm",
            "source_system": "CRM",
            "destination_table": "opportunities",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=45)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 60,
            "rows_synced_last": 1850,
            "schema_changes_detected": True,
            "error_message": "Warning: 2 new fields detected in source schema",
            "owner": "Jordan Lee",
        },
        {
            "connector_id": "conn-cs-platform",
            "connector_name": "cs_platform",
            "source_system": "Customer Success",
            "destination_table": "customer_health",
            "status": "broken",
            "last_sync_completed": (NOW - timedelta(days=3, hours=7)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 360,
            "rows_synced_last": 0,
            "schema_changes_detected": False,
            "error_message": "Authentication token expired. Re-authentication required.",
            "owner": "Jordan Lee",
        },
        {
            "connector_id": "conn-marketing-platform",
            "connector_name": "marketing_platform",
            "source_system": "Marketing",
            "destination_table": "marketing_spend",
            "status": "broken",
            "last_sync_completed": (NOW - timedelta(days=2, hours=14)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 360,
            "rows_synced_last": 0,
            "schema_changes_detected": False,
            "error_message": "API rate limit exceeded. Connector paused.",
            "owner": "Sam Patel",
        },
        {
            "connector_id": "conn-zendesk",
            "connector_name": "zendesk_support",
            "source_system": "Support",
            "destination_table": "support_tickets",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=30)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 60,
            "rows_synced_last": 2340,
            "schema_changes_detected": False,
            "error_message": "",
            "owner": "Sam Patel",
        },
        {
            "connector_id": "conn-contract-mgmt",
            "connector_name": "contract_management",
            "source_system": "Contract Management",
            "destination_table": "contracts",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(hours=2)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 360,
            "rows_synced_last": 728,
            "schema_changes_detected": False,
            "error_message": "",
            "owner": "Alex Thompson",
        },
        {
            "connector_id": "conn-account-master",
            "connector_name": "account_master",
            "source_system": "CRM",
            "destination_table": "accounts",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=20)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 60,
            "rows_synced_last": 750,
            "schema_changes_detected": False,
            "error_message": "",
            "owner": "Jordan Lee",
        },
        {
            "connector_id": "conn-payment-gateway",
            "connector_name": "payment_gateway",
            "source_system": "Payments",
            "destination_table": "invoices",
            "status": "delayed",
            "last_sync_completed": (NOW - timedelta(hours=4)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 30,
            "rows_synced_last": 312,
            "schema_changes_detected": False,
            "error_message": "Webhook backlog is draining slower than expected",
            "owner": "Alex Thompson",
        },
        {
            "connector_id": "conn-web-analytics",
            "connector_name": "web_analytics",
            "source_system": "Website",
            "destination_table": "marketing_spend",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=55)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 60,
            "rows_synced_last": 9800,
            "schema_changes_detected": True,
            "error_message": "Campaign attribution field renamed in source",
            "owner": "Sam Patel",
        },
        {
            "connector_id": "conn-product-catalog",
            "connector_name": "product_catalog",
            "source_system": "Product Catalog",
            "destination_table": "contracts",
            "status": "connected",
            "last_sync_completed": (NOW - timedelta(minutes=18)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 120,
            "rows_synced_last": 95,
            "schema_changes_detected": False,
            "error_message": "",
            "owner": "Data Platform",
        },
        {
            "connector_id": "conn-data-quality",
            "connector_name": "data_quality_rules",
            "source_system": "Warehouse",
            "destination_table": "metric_dependency_map",
            "status": "broken",
            "last_sync_completed": (NOW - timedelta(days=1, hours=9)).isoformat(timespec="seconds"),
            "sync_frequency_minutes": 60,
            "rows_synced_last": 0,
            "schema_changes_detected": False,
            "error_message": "Rule runner failed after BigQuery permission change",
            "owner": "Data Platform",
        },
    ]


def generate_metric_dependencies():
    return [
        {"metric_id": "MET-001", "metric_name": "Monthly Recurring Revenue (MRR)", "source_tables": "accounts,invoices,contracts", "source_connectors": "stripe_billing,salesforce_crm,contract_management", "owner": "Finance / RevOps", "dashboard_name": "Executive Revenue Dashboard", "business_criticality": "critical"},
        {"metric_id": "MET-002", "metric_name": "Net Revenue Retention (NRR)", "source_tables": "accounts,invoices,contracts,product_usage_events", "source_connectors": "stripe_billing,salesforce_crm,product_telemetry,contract_management", "owner": "Finance / RevOps", "dashboard_name": "Executive Revenue Dashboard", "business_criticality": "critical"},
        {"metric_id": "MET-003", "metric_name": "Underbilling Exposure", "source_tables": "product_usage_events,invoices,contracts", "source_connectors": "product_telemetry,stripe_billing,contract_management,payment_gateway", "owner": "Finance / Billing Ops", "dashboard_name": "Billing Accuracy Dashboard", "business_criticality": "critical"},
        {"metric_id": "MET-004", "metric_name": "Expansion Pipeline", "source_tables": "product_usage_events,opportunities,accounts", "source_connectors": "product_telemetry,salesforce_crm,account_master", "owner": "Sales / RevOps", "dashboard_name": "Sales Pipeline Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-005", "metric_name": "Customer Health Score", "source_tables": "customer_health,support_tickets,product_usage_events", "source_connectors": "cs_platform,zendesk_support,product_telemetry", "owner": "Customer Success", "dashboard_name": "CS Health Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-006", "metric_name": "Customer Acquisition Cost (CAC)", "source_tables": "marketing_spend,opportunities", "source_connectors": "marketing_platform,salesforce_crm,web_analytics", "owner": "Marketing / Finance", "dashboard_name": "Marketing ROI Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-007", "metric_name": "Churn Risk Exposure", "source_tables": "customer_health,accounts,support_tickets", "source_connectors": "cs_platform,account_master,zendesk_support", "owner": "Customer Success", "dashboard_name": "CS Health Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-008", "metric_name": "Usage Growth Rate", "source_tables": "product_usage_events,accounts", "source_connectors": "product_telemetry,account_master", "owner": "Product", "dashboard_name": "Product Analytics Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-009", "metric_name": "Revenue at Risk", "source_tables": "accounts,invoices,customer_health,product_usage_events,contracts", "source_connectors": "stripe_billing,cs_platform,product_telemetry,salesforce_crm,contract_management", "owner": "Finance / Leadership", "dashboard_name": "Executive Revenue Dashboard", "business_criticality": "critical"},
        {"metric_id": "MET-010", "metric_name": "Cost Leakage", "source_tables": "marketing_spend", "source_connectors": "marketing_platform,web_analytics", "owner": "Marketing / Finance", "dashboard_name": "Marketing ROI Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-011", "metric_name": "Overage Capture Rate", "source_tables": "product_usage_events,invoices,contracts", "source_connectors": "product_telemetry,stripe_billing,contract_management", "owner": "Billing Ops", "dashboard_name": "Billing Accuracy Dashboard", "business_criticality": "critical"},
        {"metric_id": "MET-012", "metric_name": "Expansion Readiness", "source_tables": "product_usage_events,customer_health,opportunities", "source_connectors": "product_telemetry,cs_platform,salesforce_crm", "owner": "Sales / CS", "dashboard_name": "Sales Pipeline Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-013", "metric_name": "Connector SLA Compliance", "source_tables": "fivetran_connector_status", "source_connectors": "data_quality_rules", "owner": "Data Platform", "dashboard_name": "Data Trust Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-014", "metric_name": "Payment Collection Risk", "source_tables": "invoices,accounts", "source_connectors": "stripe_billing,payment_gateway,account_master", "owner": "Finance", "dashboard_name": "Executive Revenue Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-015", "metric_name": "Renewal Forecast", "source_tables": "contracts,opportunities,customer_health", "source_connectors": "contract_management,salesforce_crm,cs_platform", "owner": "RevOps", "dashboard_name": "Renewal Forecast Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-016", "metric_name": "Product Adoption", "source_tables": "customer_health,product_usage_events", "source_connectors": "cs_platform,product_telemetry", "owner": "Product / CS", "dashboard_name": "Product Analytics Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-017", "metric_name": "Support Escalation Risk", "source_tables": "support_tickets,customer_health", "source_connectors": "zendesk_support,cs_platform", "owner": "Support / CS", "dashboard_name": "CS Health Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-018", "metric_name": "Campaign ROI", "source_tables": "marketing_spend,opportunities", "source_connectors": "marketing_platform,web_analytics,salesforce_crm", "owner": "Marketing", "dashboard_name": "Marketing ROI Dashboard", "business_criticality": "medium"},
        {"metric_id": "MET-019", "metric_name": "Contract Entitlement Accuracy", "source_tables": "contracts,accounts", "source_connectors": "contract_management,product_catalog,account_master", "owner": "Revenue Systems", "dashboard_name": "Billing Accuracy Dashboard", "business_criticality": "high"},
        {"metric_id": "MET-020", "metric_name": "Data Freshness", "source_tables": "fivetran_connector_status,metric_dependency_map", "source_connectors": "data_quality_rules,product_telemetry,marketing_platform,cs_platform", "owner": "Data Platform", "dashboard_name": "Data Trust Dashboard", "business_criticality": "critical"},
    ]


def write_csv(filename, rows):
    if not rows:
        return
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in tqdm(rows, desc=f"write {filename}", unit="row", leave=False):
            writer.writerow(row)
    tqdm.write(f"  wrote {filename}: {len(rows)} rows")


def main():
    print("Generating StreamWorks Cloud synthetic data...\n")
    with tqdm(total=10, desc="seed generation", unit="stage") as progress:
        progress.set_postfix_str("accounts")
        accounts = generate_accounts()
        progress.update()

        progress.set_postfix_str("contracts")
        contracts = generate_contracts(accounts)
        progress.update()

        progress.set_postfix_str("usage events")
        usage_events = generate_usage_events(accounts, contracts)
        progress.update()

        progress.set_postfix_str("invoices")
        invoices = generate_invoices(accounts, contracts, usage_events)
        progress.update()

        progress.set_postfix_str("opportunities")
        opportunities = generate_opportunities(accounts)
        progress.update()

        progress.set_postfix_str("customer health")
        health = generate_customer_health(accounts)
        progress.update()

        progress.set_postfix_str("marketing spend")
        marketing = generate_marketing_spend()
        progress.update()

        progress.set_postfix_str("support tickets")
        tickets = generate_support_tickets(accounts)
        progress.update()

        progress.set_postfix_str("connector status")
        connectors = generate_connector_status()
        progress.update()

        progress.set_postfix_str("metric dependencies")
        metrics = generate_metric_dependencies()
        progress.update()

    for filename, rows in tqdm([
        ("accounts.csv", accounts),
        ("contracts.csv", contracts),
        ("product_usage_events.csv", usage_events),
        ("invoices.csv", invoices),
        ("opportunities.csv", opportunities),
        ("customer_health.csv", health),
        ("marketing_spend.csv", marketing),
        ("support_tickets.csv", tickets),
        ("fivetran_connector_status.csv", connectors),
        ("metric_dependency_map.csv", metrics),
    ], desc="csv files", unit="file"):
        write_csv(filename, rows)

    scenario_counts = Counter(scenario_for_index(idx) for idx in range(NUM_ACCOUNTS))
    print(f"\nDone. All files written to {OUTPUT_DIR}/")
    print(f"Accounts generated: {NUM_ACCOUNTS}")
    print(f"Scenario coverage: {dict(sorted(scenario_counts.items()))}")
    print(f"Underbilling target: ${sum(UNDERBILLING_TARGETS):,.0f}")
    print(f"Expansion target: ${sum(EXPANSION_TARGETS):,.0f}")
    print(f"Duplicate spend leakage target: ${sum(DUPLICATE_SPEND_TARGETS):,.0f}")
    print("Revenue dashboard trust score target: 62/100")


if __name__ == "__main__":
    main()
