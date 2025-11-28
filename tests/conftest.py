"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing."""
    code = '''
class Order:
    def __init__(self, customer, items):
        self.customer = customer
        self.items = items

    def calculate_total(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.price * item.quantity
        tax = subtotal * 0.1
        discount = 0
        if self.customer.is_premium:
            discount = subtotal * 0.05
        return subtotal + tax - discount

    def print_order(self):
        print(f"Customer: {self.customer.name}")
        for item in self.items:
            print(f"  {item.name}: {item.price}")
'''
    file_path = tmp_path / "order.py"
    file_path.write_text(code)
    return file_path
