"""
Custom Template Tags and Filters for Members App

Place this file in: members/templatetags/members_tags.py

Usage in templates:
{% load members_tags %}
"""

from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Get item from dictionary by key.

    Usage: {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name="get_index")
def get_index(list_obj, index):
    """
    Get item from list by index.

    Usage: {{ my_list|get_index:0 }}
    """
    try:
        return list_obj[int(index)]
    except (IndexError, TypeError, ValueError):
        return None


@register.filter(name="divide_by_million")
def divide_by_million(value):
    """
    Divide value by one million.

    Usage: {{ population|divide_by_million }}
    """
    try:
        return float(value) / 1_000_000
    except (TypeError, ValueError):
        return 0


@register.filter(name="mul")
def multiply(value, arg):
    """
    Multiply value by argument.

    Usage: {{ value|mul:2 }}
    """
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter(name="add")
def add_values(value, arg):
    """
    Add argument to value.

    Usage: {{ value|add:5 }}
    """
    try:
        return float(value) + float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter(name="map")
def map_attribute(queryset, attribute):
    """
    Map attribute from queryset objects.

    Usage: {{ countries|map:'country_name' }}
    """
    try:
        return [getattr(obj, attribute) for obj in queryset]
    except (AttributeError, TypeError):
        return []


@register.filter
def format_number(value):
    """
    Format number with commas.

    Usage: {{ 1000000|format_number }}  => "1,000,000"
    """
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value


@register.filter
def format_currency(value):
    """
    Format value as currency.

    Usage: {{ 1000000|format_currency }}  => "$1,000,000"
    """
    try:
        return "${:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return value


@register.filter
def percentage(value):
    """
    Format value as percentage.

    Usage: {{ 0.15|percentage }}  => "15%"
    """
    try:
        return "{:.1f}%".format(float(value) * 100)
    except (ValueError, TypeError):
        return value


@register.simple_tag
def active_countries_list():
    """
    Get list of active country slugs.

    Usage: {% active_countries_list as active_slugs %}
    """
    from members.models import MemberStateIPA

    return list(MemberStateIPA.objects.filter(is_active=True).values_list("slug", flat=True))


@register.inclusion_tag("members/components/country_flag.html")
def country_flag(country):
    """
    Render country flag component.

    Usage: {% country_flag member_state %}
    """
    return {"country": country}


@register.inclusion_tag("members/components/stat_card.html")
def stat_card(title, value, subtitle="", icon=""):
    """
    Render statistic card component.

    Usage: {% stat_card "GDP" "$100B" subtitle="2024" icon="📊" %}
    """
    return {"title": title, "value": value, "subtitle": subtitle, "icon": icon}


@register.filter
def format_investment(value):
    """
    Format investment amount in millions with M suffix.
    Example: 50000000 -> $50M
             5000000 -> $5M
             500000 -> $0.5M
    """
    if not value:
        return "N/A"

    try:
        amount = float(value)
        millions = amount / 1000000

        if millions >= 1:
            # Format as whole number if >= 1M
            if millions == int(millions):
                return f"${int(millions)}M"
            else:
                return f"${millions:.1f}M"
        else:
            # Format with decimal for < 1M
            return f"${millions:.1f}M"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def format_investment_range(opportunity):
    """
    Format investment range with min and max values.
    """
    try:
        min_val = format_investment(opportunity.investment_required_min)
        if opportunity.investment_required_max:
            max_val = format_investment(opportunity.investment_required_max)
            return f"{min_val} - {max_val}"
        return min_val
    except AttributeError:
        return "N/A"
