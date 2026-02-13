# Claude Code Task: Fix Product-to-Dataset Path Mapping

## Problem

Census API URLs require dataset paths like `acs/acs5`, but our tools use 
shorthand product codes like `acs5`. Two places are broken:

1. `get_variables()` (line ~250) receives `acs5`, needs `acs/acs5`
2. `get_census_data()` (line ~168) has `acs/acs5` hardcoded — ignores product param

## Fix

Add a product-to-dataset mapping in `src/census_mcp/api/census_client.py`:

```python
PRODUCT_TO_DATASET = {
    "acs5": "acs/acs5",
    "acs1": "acs/acs1", 
    "acs5/profile": "acs/acs5/profile",
    "acs5/subject": "acs/acs5/subject",
    "acs1/profile": "acs/acs1/profile",
    "acs1/subject": "acs/acs1/subject",
    "sf1": "dec/sf1",
    "dhc": "dec/dhc",
    "pl": "dec/pl",
    "pep": "pep/population",
}

def resolve_dataset(product: str) -> str:
    """Resolve shorthand product code to Census API dataset path."""
    return PRODUCT_TO_DATASET.get(product, product)  # passthrough if already full path
```

Then use `resolve_dataset()` in both:
- `get_census_data()`: replace hardcoded `acs/acs5` with `resolve_dataset(product)`
  (the product/dataset parameter needs to be threaded through to this function)
- `get_variables()`: wrap dataset param with `resolve_dataset(dataset)`

Also check `server.py` to make sure the product parameter is being passed
through to `get_census_data()` — line 168 suggests it may be ignored entirely.

## Scope

- Only modify `census_client.py` and `server.py`
- Do NOT change any eval/ files
- Do NOT run the harness
- Test by running: `/opt/anaconda3/envs/census-mcp/bin/python -c "from census_mcp.api.census_client import resolve_dataset; print(resolve_dataset('acs5')); print(resolve_dataset('acs1')); print(resolve_dataset('acs/acs5'))"`
