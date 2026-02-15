from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    return dictionary.get(key, 0)

@register.filter
def is_my_program(program, user):
    """Check if user is in program team members"""
    if user.is_authenticated:
        return user in program.team_members.all()
    return False