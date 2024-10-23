from typing import List, Dict, Optional
import asyncio

class ShoppingCart:
    def __init__(self):
        self.items: Dict[str, int] = {}
        self.total: float = 0.0

    def add_item(self, item_name: str, quantity: int, price: float) -> float:
        """
        Add an item to the shopping cart.
        Returns the new total after adding the item.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if price < 0:
            raise ValueError("Price cannot be negative")
            
        if item_name in self.items:
            self.items[item_name] += quantity
        else:
            self.items[item_name] = quantity
            
        self.total += quantity * price
        return self.total

    def remove_item(self, item_name: str, quantity: Optional[int] = None) -> float:
        """
        Remove an item from the cart. If quantity is None, removes all of that item.
        Returns the new total after removing the item.
        """
        if item_name not in self.items:
            raise KeyError("Item not found in cart")
            
        if quantity is not None:
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if quantity > self.items[item_name]:
                raise ValueError("Not enough items in cart")
                
            self.items[item_name] -= quantity
            if self.items[item_name] == 0:
                del self.items[item_name]
        else:
            del self.items[item_name]
            
        return self.total

    async def calculate_discount(self, is_member: bool = False) -> float:
        """
        Calculate discount based on cart total and membership status.
        """
        # Simulate some async operation (e.g., checking member status from database)
        await asyncio.sleep(0.1)
        
        discount = 0.0
        if self.total >= 100:
            discount += 0.1  # 10% discount for orders over $100
        if is_member:
            discount += 0.05  # Additional 5% for members
            
        return self.total * discount
