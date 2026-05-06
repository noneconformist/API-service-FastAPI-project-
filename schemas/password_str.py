import re
from typing import Annotated

from pydantic import AfterValidator


def strong_password(password: str) -> str:
    errors = []

    if len(password) < 8:
        errors.append('The password is too short (minimum 8 characters)')
    if len(password) > 24:
        errors.append('The password is too long (maximum 24 characters)')

    if not re.search(r'\d', password):
        errors.append('at least one digit')
    if not re.search(r'[a-z]', password):
        errors.append('at least one lowercase')
    if not re.search(r'[A-Z]', password):
        errors.append('at least one uppercase')
    if re.search(r'[@\"\'<>]', password):
        errors.append('cannot contain: @ " \' < >')
    if not re.search(r'[^0-9a-zA-Z]', password):
        errors.append('at least one special character (excluding @ " \' < >)')

    if errors:
        raise ValueError('Password validation errors:\n- ' + '\n- '.join(errors))

    return password


PasswordStr = Annotated[
    str,
    AfterValidator(strong_password),
]
