from strawberry.relay import to_base64


def get_group(instance):
    return f"{instance.__class__.__name__}"


def get_msg_type(instance):
    group = get_group(instance)
    return f"{group}_{instance.id}"


def get_msg(instance):
    return {'type': get_msg_type(instance)}


def create_global_id(instance):
    return to_base64(f"{instance.__class__.__name__}Type", instance.id)
