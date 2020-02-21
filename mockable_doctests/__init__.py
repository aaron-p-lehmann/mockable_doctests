# pylint: skip-file
# flake8: noqa
"""
Import submodules __all__ members so that they can be accessed directly through main package import.

This allows downstream code to access all members through package import without needing subpackages and
becoming dependent on internal package structure
"""
from mockable_doctests import mockable


from mockable_doctests.mockable import *


__all__ = (
    list(getattr(mockable, "__all__", []))
)


__version__ = '1.0.0'
