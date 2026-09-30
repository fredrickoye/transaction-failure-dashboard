"""
Generate realistic synthetic payment transaction data
modelled on common Nigerian fintech / payments issues.
No real company data used.
"""
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import os

fake = Faker()
np.random.seed(42)
Faker.seed(42)

n = 8000  # rows

providers = ['Provider A', 'Provider B', 'Provider C']
channels = ['Web', 'Mobile App', 'USSD', 'POS']
statuses = ['success', 'failed']
failure_reasons = [
    'Insufficient funds', 'Timeout', 'Provider error',
    'Webhook failure', 'Invalid account', 'Network error',
    'Card declined', 'OTP failure'
]

# Base timestamps over last 90 days
start = datetime.now() - timedelta(days=90)
timestamps = [start + timedelta(seconds=np.random.randint(0, 90*24*3600)) for _ in range(n)]

data = {
    'transaction_id': [fake.uuid4() for _ in range(n)],
    'timestamp': timestamps,
    'amount': np.round(np.random.exponential(scale=4500, size=n) + 100, 2),
    'currency': 'NGN',
    'payment_provider': np.random.choice(providers, n, p=[0.48, 0.32, 0.20]),
    'channel': np.random.choice(channels, n, p=[0.40, 0.35, 0.15, 0.10]),
    'status': np.random.choice(statuses, n, p=[0.82, 0.18]),
}

df = pd.DataFrame(data)

# Failure reason only for failed rows
df['failure_reason'] = None
failed_mask = df['status'] == 'failed'
df.loc[failed_mask, 'failure_reason'] = np.random.choice(
    failure_reasons, size=failed_mask.sum()
)

# Make some realistic patterns:
# - Higher failures on USSD and late night
# - Provider B slightly higher failure rate
# - Larger amounts fail a bit more often

df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.day_name()

# Boost failure probability for certain conditions (re-sample a portion)
boost_mask = (
    (df['channel'] == 'USSD') |
    (df['hour'].between(0, 5)) |
    (df['payment_provider'] == 'Provider B') |
    (df['amount'] > 20000)
)
# Flip some successes to failures under boost conditions
flip_idx = df[boost_mask & (df['status'] == 'success')].sample(frac=0.12, random_state=42).index
df.loc[flip_idx, 'status'] = 'failed'
df.loc[flip_idx, 'failure_reason'] = np.random.choice(failure_reasons, size=len(flip_idx))

df = df.drop(columns=['hour', 'day_of_week'])
df = df.sort_values('timestamp').reset_index(drop=True)

out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'transaction_failures.csv')
df.to_csv(out_path, index=False)
print(f"Generated {len(df)} rows → {out_path}")
print(df['status'].value_counts(normalize=True).round(3))
print(df.head(3))
