"""Utility functions

Helpers and other assorted functions.
"""

import inspect

__all__ = [
    'inspect_info',
]


def inspect_info(current_frame, stack_info):
    frame_info, stack_first = inspect.getframeinfo(current_frame), stack_info[1]
    return frame_info[0], frame_info[1], frame_info[2], stack_first[1], stack_first[2], stack_first[3]
