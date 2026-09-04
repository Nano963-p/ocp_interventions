"""Small, framework-independent helpers for controlled form validation."""
from datetime import datetime
import math


def text_value(form, name, label, *, required=False, max_length=255):
    value = form.get(name, '').strip()
    errors = []
    if required and not value:
        errors.append(f"{label} est obligatoire.")
    if len(value) > max_length:
        errors.append(f"{label} ne peut pas dépasser {max_length} caractères.")
    return value, errors


def choice_value(form, name, label, allowed, *, default=None):
    value = form.get(name, default)
    if value not in allowed:
        return None, [f"{label} invalide."]
    return value, []


def int_value(form, name, label, *, minimum=None, maximum=None, default=None):
    raw = form.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, [f"{label} doit être un nombre entier."]
    errors = []
    if minimum is not None and value < minimum:
        errors.append(f"{label} doit être supérieur ou égal à {minimum}.")
    if maximum is not None and value > maximum:
        errors.append(f"{label} doit être inférieur ou égal à {maximum}.")
    return value, errors


def float_value(form, name, label, *, minimum=None, maximum=None, default=None):
    raw = form.get(name, default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, [f"{label} doit être un nombre."]
    if not math.isfinite(value):
        return None, [f"{label} doit être un nombre fini."]
    errors = []
    if minimum is not None and value < minimum:
        errors.append(f"{label} doit être supérieur ou égal à {minimum}.")
    if maximum is not None and value > maximum:
        errors.append(f"{label} doit être inférieur ou égal à {maximum}.")
    return value, errors


def date_value(form, name, label, *, required=False):
    raw = form.get(name, '').strip()
    if not raw:
        return (None, [f"{label} est obligatoire."]) if required else (None, [])
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date(), []
    except ValueError:
        return None, [f"{label} doit être une date valide au format AAAA-MM-JJ."]


def flash_errors(flash, errors):
    for error in errors:
        flash(error, 'danger')
