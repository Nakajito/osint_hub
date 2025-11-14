import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "osint_hub.settings")
django.setup()

import trio
from PhoneSearch.views import search_phone_async

# Ejecutar búsqueda
print("Iniciando búsqueda...")
results = trio.run(search_phone_async, "5535664668", "521")

print(f"\nTotal results: {len(results)}")
print(f"Results type: {type(results)}")
print(f"Results JSON-serializable: {all(isinstance(r, dict) for r in results)}")

for i, r in enumerate(results):
    print(f"\nResult {i}: {r}")

print("\n✓ Búsqueda completada exitosamente")
