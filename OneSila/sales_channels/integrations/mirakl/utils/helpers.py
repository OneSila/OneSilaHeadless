from __future__ import annotations


def get_local_instance_label(*, local_instance=None) -> str:
    if local_instance is None:
        return ""

    for attr_name in ("name", "internal_name", "value"):
        label = getattr(local_instance, attr_name, None)
        if label not in (None, "", "No Name Set", "No Value Set"):
            return str(label)

    local_instance_id = getattr(local_instance, "id", None)
    if local_instance_id is None:
        return ""
    return str(local_instance_id)


def build_remote_property_mapping_label(*, remote_property=None) -> str:
    remote_property_code = getattr(remote_property, "code", "") or ""
    local_property_label = get_local_instance_label(
        local_instance=getattr(remote_property, "local_instance", None),
    )
    if not local_property_label:
        return f"Mirakl field '{remote_property_code}'"
    return f"Mirakl field '{remote_property_code}' (local '{local_property_label}')"
