from models import User


# for display admin's balance
def format_balance(user: User) -> int | None:
    # Admin has "none" always
    if any(role.name == 'admin' for role in user.roles):
        return None
    return user.balance
