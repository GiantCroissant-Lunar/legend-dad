class_name LoadPolicy
extends RefCounted

enum Policy { EAGER, LAZY }

static func from_string(name: String) -> int:
    match name:
        "eager": return Policy.EAGER
        "lazy": return Policy.LAZY
        _:
            push_error("Unknown LoadPolicy: %s" % name)
            return -1
