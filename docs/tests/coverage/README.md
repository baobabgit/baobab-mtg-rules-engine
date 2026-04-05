# Rapports de couverture

Ce répertoire accueille les **sorties générées** par `coverage` / `pytest-cov` :

- `html/` : rapport HTML (navigation par fichier)
- `coverage.xml` : export XML (CI, outils tiers)
- `.coverage` : fichier de données binaire utilisé par `coverage`

Ces fichiers sont **ignorés par Git** (voir `.gitignore`). Pour les régénérer :

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

La configuration (chemins, seuil minimal, branches, etc.) vit dans `pyproject.toml`, sections `[tool.coverage.*]` et options `addopts` de pytest.
