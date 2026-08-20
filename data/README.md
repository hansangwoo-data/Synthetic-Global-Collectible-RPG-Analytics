# Synthetic Data Boundary

All files in `data/synthetic/` are generated for a fictional global
character-collection mobile RPG. They are not transformed, sampled, calibrated,
or modeled from a specific company's production data.

The fixed seed in `src/generate_synthetic_data.py` reproduces:

- regional daily KPIs for KR, JP, and Global West;
- mature monthly survival-style retention cohorts through November 2025;
- a fictional event and incident calendar;
- a product dimension with standard premium-currency top-ups but without direct
  limited-character sales;
- daily product sales;
- daily PvE boss funnels by region and difficulty.

Gacha pulls, user-level transactions, individual combat logs, real product
names, real incidents, and proprietary schemas are intentionally excluded.

Run:

```bash
python src/generate_synthetic_data.py
```

Derived tables written by the analysis pipeline are stored in the Git-ignored
`outputs/` directory.
