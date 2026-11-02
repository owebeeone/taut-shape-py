"""Foundation-only aliases to the application's single canonical ``taut`` owner."""
from taut.contracts import (RUNTIME_OWNER, GENERATOR_BUILD, DESCRIPTOR_CONTRACT,
                            CODEC_CONTRACT, require_contract, ConfigurationError)
from taut.descriptors import (SchemaDescriptor, MessageDescriptor, FieldDescriptor,
                              EnumDescriptor, OneOfDescriptor, TypeDescriptor,
                              ConstraintDescriptor, SchemaBinding)
from taut.wire import cbor, codec, jsoncodec


def __getattr__(name):
    if name in ("PathSegment", "ValidationIssue", "DeferredCheck", "ValidationReport",
                "validate_record", "is_record_valid"):
        from taut import validation
        return getattr(validation, name)
    raise AttributeError(name)
