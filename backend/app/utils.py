"""
Utility functions and helpers for the Tavi application.
"""
from typing import TypeVar, Optional
from enum import Enum


T = TypeVar('T', bound=Enum)


def safe_enum(enum_class: type[T], value: Optional[str], default: T) -> T:
    """
    Safely convert string to enum, handling case-insensitivity.
    """
    if not value:
        return default
    
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        try:
            value_lower = str(value).lower()
            for enum_item in enum_class:
                if enum_item.value.lower() == value_lower:
                    return enum_item
        except:
            pass
        return default
