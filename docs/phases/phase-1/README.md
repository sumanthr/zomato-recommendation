# Phase 1 Resources

- Download pipeline: `src/phases/phase_1/download_dataset.py`
- Curation pipeline: `src/phases/phase_1/curate_dataset.py`
- End-to-end runner: `src/phases/phase_1/pipeline.py`
- Normalization utilities: `src/phases/phase_1/normalization.py`
- Data quality utilities: `src/phases/phase_1/quality.py`

## Hugging Face schema mapping (ManikaSaini/zomato-restaurant-recommendation)

Curated columns include: `name`, `location` → locality, `listed_in(city)` → `location_city`, `cuisines`, `rate` → rating, `approx_cost(for two people)` → `avg_cost_for_two`. Optional local raw path: `ZOMATO_LOCAL_RAW_PATH` if Hub download is blocked.
