"""
Date utilities for ShotGrid MCP server.
Provides ISO8601 formatting and validation helpers.
"""

from typing import Union

import pendulum


def to_iso8601(dt: Union[str, pendulum.DateTime]) -> str:
    """
    Convert date or datetime to ISO8601 string (with +08:00 timezone) using pendulum.
    Accepts 'YYYY-MM-DD', datetime, or pendulum.DateTime object.
    """
    if isinstance(dt, str):
        try:
            dt_obj = pendulum.parse(dt, tz="Asia/Shanghai")
        except Exception as err:
            raise ValueError(f"Invalid date string: {dt}") from err
    elif isinstance(dt, pendulum.DateTime):
        dt_obj = dt.in_timezone("Asia/Shanghai")
    else:
        raise TypeError("dt must be str or pendulum.DateTime")
    return dt_obj.to_iso8601_string()
