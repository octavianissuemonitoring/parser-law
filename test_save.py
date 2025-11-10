import pandas as pd
import os

# Test salvare CSV
os.makedirs('/app/rezultate', exist_ok=True)
df = pd.DataFrame({'test': [1, 2, 3]})
csv_path = '/app/rezultate/test.csv'
df.to_csv(csv_path, index=False)
print(f"SUCCESS: Salvat în {csv_path}")
print(f"Fișiere: {os.listdir('/app/rezultate')}")
