def attach_metadata(item, product_id):
    """
    Add machine metadata:
    - product_id
    - timestamp_utc (deterministic mock: constant '1970-01-01T00:00:00Z')
    - generator_version = '1.0'
    """
    item["product_id"] = product_id
    item["timestamp_utc"] = "1970-01-01T00:00:00Z"
    item["generator_version"] = "1.0"
    return item
