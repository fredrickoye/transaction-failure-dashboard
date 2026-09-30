"""
Transaction Failure Root-Cause Analysis
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "transaction_failures.csv"
OUT = Path(__file__).parent.parent / "outputs"
OUT.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["font.size"] = 10

df = pd.read_csv(DATA, parse_dates=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["date"] = df["timestamp"].dt.date
df["is_failed"] = (df["status"] == "failed").astype(int)

print("=" * 60)
print("TRANSACTION FAILURE ROOT-CAUSE ANALYSIS")
print("=" * 60)
print(f"\nTotal transactions : {len(df):,}")
print(f"Failed transactions: {df['is_failed'].sum():,} ({df['is_failed'].mean()*100:.1f}%)")
print(f"Date range         : {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")

# 1. Failure rate by provider
print("\n--- Failure Rate by Provider ---")
by_provider = df.groupby("payment_provider").agg(
    total=("transaction_id", "count"),
    failed=("is_failed", "sum"),
    failure_rate=("is_failed", "mean"),
    avg_amount=("amount", "mean")
).round(3)
by_provider["failure_rate_pct"] = (by_provider["failure_rate"] * 100).round(1)
print(by_provider.sort_values("failure_rate", ascending=False))

# 2. Failure rate by channel
print("\n--- Failure Rate by Channel ---")
by_channel = df.groupby("channel").agg(
    total=("transaction_id", "count"),
    failed=("is_failed", "sum"),
    failure_rate=("is_failed", "mean")
).round(3)
print(by_channel.sort_values("failure_rate", ascending=False))

# 3. Top failure reasons
print("\n--- Top Failure Reasons ---")
reasons = df[df["status"] == "failed"]["failure_reason"].value_counts()
print(reasons)

# 4. Hourly pattern
print("\n--- Failure Rate by Hour of Day ---")
hourly = df.groupby("hour")["is_failed"].mean().round(3)
print(hourly)

# ---- Visualisations ----

# Chart 1: Failure rate by provider
fig, ax = plt.subplots()
order = by_provider.sort_values("failure_rate", ascending=False).index
sns.barplot(data=df, x="payment_provider", y="is_failed", order=order, ax=ax, errorbar=None)
ax.set_ylabel("Failure Rate")
ax.set_xlabel("Payment Provider")
ax.set_title("Transaction Failure Rate by Payment Provider")
ax.set_ylim(0, 0.4)
for i, p in enumerate(order):
    rate = by_provider.loc[p, "failure_rate"]
    ax.text(i, rate + 0.01, f"{rate*100:.1f}%", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(OUT / "failure_rate_by_provider.png", dpi=150)
plt.close()

# Chart 2: Failure rate by channel
fig, ax = plt.subplots()
order_c = by_channel.sort_values("failure_rate", ascending=False).index
sns.barplot(data=df, x="channel", y="is_failed", order=order_c, ax=ax, errorbar=None)
ax.set_ylabel("Failure Rate")
ax.set_xlabel("Channel")
ax.set_title("Transaction Failure Rate by Channel")
ax.set_ylim(0, 0.45)
plt.tight_layout()
plt.savefig(OUT / "failure_rate_by_channel.png", dpi=150)
plt.close()

# Chart 3: Failure reasons pie
fig, ax = plt.subplots(figsize=(8, 6))
reasons.plot.pie(autopct="%1.1f%%", ax=ax, startangle=90)
ax.set_ylabel("")
ax.set_title("Distribution of Failure Reasons")
plt.tight_layout()
plt.savefig(OUT / "failure_reasons.png", dpi=150)
plt.close()

# Chart 4: Hourly failure rate
fig, ax = plt.subplots()
hourly.plot(kind="line", marker="o", ax=ax, color="#c44e52")
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Failure Rate")
ax.set_title("Failure Rate by Hour of Day")
ax.set_xticks(range(0, 24, 2))
ax.set_ylim(0, 0.4)
plt.tight_layout()
plt.savefig(OUT / "failure_rate_by_hour.png", dpi=150)
plt.close()

# Chart 5: Amount vs failure (boxplot)
fig, ax = plt.subplots()
sns.boxplot(data=df, x="status", y="amount", ax=ax, showfliers=False)
ax.set_title("Transaction Amount Distribution by Status")
ax.set_ylabel("Amount (NGN)")
plt.tight_layout()
plt.savefig(OUT / "amount_by_status.png", dpi=150)
plt.close()

# Summary insights file
insights = f"""
TRANSACTION FAILURE ROOT-CAUSE ANALYSIS – KEY FINDINGS
=======================================================

Dataset: {len(df):,} synthetic transactions over ~90 days
Overall failure rate: {df['is_failed'].mean()*100:.1f}%

1. PROVIDER PERFORMANCE
{by_provider[['total','failed','failure_rate_pct']].to_string()}

   → Provider B shows the highest failure rate.
   → Recommendation: Investigate Provider B timeout/webhook issues; consider routing high-value traffic preferentially to lower-failure providers during peak risk windows.

2. CHANNEL PERFORMANCE
{by_channel[['total','failed','failure_rate']].to_string()}

   → USSD carries a noticeably higher failure rate than Web/Mobile.
   → Recommendation: Review USSD session handling and timeout settings.

3. TOP FAILURE REASONS
{reasons.head(5).to_string()}

4. TIME-OF-DAY PATTERN
   Highest failure rates occur in the early morning hours (00:00–05:00).
   → Possible causes: lower monitoring coverage, provider maintenance windows, or network instability.

5. AMOUNT RELATIONSHIP
   Failed transactions skew slightly higher in amount than successful ones.
   → High-value transactions may warrant additional confirmation steps or alternative routing.

BUSINESS IMPLICATION
--------------------
These patterns can be turned into concrete ops actions:
- Provider-level SLAs and automated failover rules
- Channel-specific monitoring alerts
- Time-based staffing or monitoring coverage adjustments
- Pre-emptive customer messaging when a provider is degraded

All data is synthetic and modelled on common Nigerian fintech payment flows.
No real customer or company data was used.
"""
with open(OUT / "insights_summary.txt", "w") as f:
    f.write(insights)

print("\nCharts and insights saved to outputs/")
print(insights)
