
import logging
from importlib import import_module


def import_cls(class_spec):
    try:
        return import_module(class_spec)
    except ImportError:
        mod_name, _, cls_name = class_spec.rpartition('.')
        return getattr(import_module(mod_name), cls_name)
