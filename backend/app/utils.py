"""
Utility functions and helpers for the Tavi application.
"""
from typing import TypeVar, Optional
from enum import Enum


T = TypeVar('T', bound=Enum)


def safe_enum(enum_class: type[T], value: Optional[str], default: T) -> T:
    """
    Safely convert string to enum, handling case-insensitivity.
    
    Args:
        enum_class: The enum class to convert to
        value: String value to convert
        default: Default enum value if conversion fails
        
    Returns:
        Enum value or default
        
    Examples:
        >>> safe_enum(Priority, "high", Priority.MEDIUM)
        Priority.HIGH
        >>> safe_enum(Priority, "HIGH", Priority.MEDIUM)  # Case insensitive
        Priority.HIGH
        >>> safe_enum(Priority, "invalid", Priority.MEDIUM)
        Priority.MEDIUM
    """
    if not value:
        return default
    
    try:
        # Try exact match first
        return enum_class(value)
    except (ValueError, KeyError):
        # Try case-insensitive match
        try:
            value_lower = str(value).lower()
            for enum_item in enum_class:
                if enum_item.value.lower() == value_lower:
                    return enum_item
        except:
            pass
        return default
