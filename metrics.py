import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Data dictionaries
data = {
    'PreRun3': {
        'game1': {'Memory_Usage': 26.48, 'Network_Input': 4.21, 'Network_Output': 1.92, 'CPU_Usage': 0.19},
        'game2': {'Memory_Usage': 24.52, 'Network_Input': 4.24, 'Network_Output': 1.89, 'CPU_Usage': 0.17},
        'game3': {'Memory_Usage': 26.5, 'Network_Input': 4.28, 'Network_Output': 1.92, 'CPU_Usage': 0.20},
        'zookeeper-server': {'Memory_Usage': 141.5, 'Network_Input': 6.73, 'Network_Output': 4.23, 'CPU_Usage': 1.23}
    },
    'PostRun3': {
        'game1': {'Memory_Usage': 28.0, 'Network_Input': 141, 'Network_Output': 78.5, 'CPU_Usage': 0.48},
        'game2': {'Memory_Usage': 27.77, 'Network_Input': 155, 'Network_Output': 87.3, 'CPU_Usage': 0.16},
        'game3': {'Memory_Usage': 30.0, 'Network_Input': 139, 'Network_Output': 77.5, 'CPU_Usage': 0.12},
        'zookeeper-server': {'Memory_Usage': 153.1, 'Network_Input': 199, 'Network_Output': 227, 'CPU_Usage': 0.55}
    },
    'PreRun5': {
        'game1': {'Memory_Usage': 24.51, 'Network_Input': 17.3, 'Network_Output': 12.7, 'CPU_Usage': 0.61},
        'game2': {'Memory_Usage': 26.5, 'Network_Input': 17.6, 'Network_Output': 12.7, 'CPU_Usage': 0.18},
        'game3': {'Memory_Usage': 24.51, 'Network_Input': 17.5, 'Network_Output': 12.7, 'CPU_Usage': 0.24},
        'game4': {'Memory_Usage': 24.51, 'Network_Input': 17.9, 'Network_Output': 12.8, 'CPU_Usage': 0.23},
        'game5': {'Memory_Usage': 24.5, 'Network_Input': 17.4, 'Network_Output': 12.5, 'CPU_Usage': 0.18},
        'zookeeper-server': {'Memory_Usage': 180.5, 'Network_Input': 879, 'Network_Output': 1.31, 'CPU_Usage': 0.88}
    },
    'PostRun5': {
        'game1': {'Memory_Usage': 28.07, 'Network_Input': 248, 'Network_Output': 638, 'CPU_Usage': 0.20},
        'game2': {'Memory_Usage': 30.15, 'Network_Input': 256, 'Network_Output': 119, 'CPU_Usage': 0.25},
        'game3': {'Memory_Usage': 28.28, 'Network_Input': 271, 'Network_Output': 128, 'CPU_Usage': 0.13},
        'game4': {'Memory_Usage': 28.07, 'Network_Input': 248, 'Network_Output': 638, 'CPU_Usage': 0.20},
        'game5': {'Memory_Usage': 27.55, 'Network_Input': 234, 'Network_Output': 109, 'CPU_Usage': 0.19},
        'zookeeper-server': {'Memory_Usage': 188.3, 'Network_Input': 1.35, 'Network_Output': 2.04, 'CPU_Usage': 0.39}
    }
}

# Convert to DataFrame for easier manipulation
dfs = {}
for key, val in data.items():
    dfs[key] = pd.DataFrame.from_dict(val, orient='index')

# Compute differences
differences = {}
for key in ['3', '5']:
    pre_key = f'PreRun{key}'
    post_key = f'PostRun{key}'
    differences[key] = dfs[post_key] - dfs[pre_key]

# Average differences for 3 and 5 users
avg_diffs = pd.concat([differences['3'], differences['5']]).groupby(level=0).mean()

# Extrapolation for 10, 20, 50, 100 users
user_counts = np.array([3, 5, 10, 20, 50, 100])
extrapolations = {}
for column in avg_diffs.columns:
    lr = LinearRegression()
    lr.fit(user_counts[:2].reshape(-1, 1), avg_diffs[column][:2])
    extrapolations[column] = lr.predict(user_counts.reshape(-1, 1))

# Plotting
plt.figure(figsize=(15, 10))
for i, (key, values) in enumerate(extrapolations.items(), 1):
    plt.subplot(2, 2, i)
    plt.plot(user_counts, values, marker='o')
    plt.title(f'{key} vs Number of Users')
    plt.xlabel('Number of Users')
    plt.ylabel(key)
    plt.grid(True)

plt.tight_layout()
plt.show()
