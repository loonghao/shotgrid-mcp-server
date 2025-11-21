"""ShotGrid filter utilities - Compatibility Layer.

This module re-exports filter utilities from the shotgrid-query library for backward compatibility.

Note: Core filter functionality has been migrated to the shotgrid-query library.
      Import FilterBuilder, TimeUnit, process_filters, etc. from shotgrid_query instead.

      This module is kept for backward compatibility only.
"""

# Import from shotgrid-query for backward compatibility
from shotgrid_query import (
    FilterBuilder,
    TimeUnit,
    build_date_filter,
    combine_filters,
    create_date_filter,
    process_filters,
    validate_filters,
)

# Re-export for backward compatibility
__all__ = [
    "FilterBuilder",
    "TimeUnit",
    "build_date_filter",
    "combine_filters",
    "create_date_filter",
    "process_filters",
    "validate_filters",
]
