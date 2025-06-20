from pydantic import BaseModel
from typing import Literal

# Create a JSON schema to constrain LLM output to Boolean values.
class BooleanResponse(BaseModel):
    response: bool

# Create a JSON schema to constrain LLM output to the given categories.
# Infrequently used categories are commented out to simplify output charts.
class CategoryResponse(BaseModel):
    response : Literal[
        'Automotive',
        'Baby & Child',
        # 'Books',
        'Charity',
        'Clothing & Accessories',
        'Debt',
        # 'Electronics & Accessories',
        'Entertainment',
        # 'Garden & Outdoor',
        'Gifts',
        'Groceries',
        # 'Gym & Fitness',
        'Health & Personal Care',
        'Home & Kitchen',
        'Landscaping',
        # 'Office Supplies',
        'Other Food & Beverage',
        # 'Pet Supplies',
        'Rent',
        'Security',
        'Subscriptions',
        'Travel',
        'Utilities',
        'Other',
    ]