# Python Test Generator

A powerful automated test generator that analyzes Python code and creates comprehensive test suites. It supports regular functions, class methods, async functions, and generates tests for edge cases and code coverage.

## ✨ Features

- 🔍 Analyzes entire Python projects
- 🧪 Generates pytest-compatible test cases
- 📊 Includes code coverage analysis
- 🔄 Supports async functions and coroutines
- 🏗️ Handles class methods and inheritance
- ⚡ Generates edge cases automatically
- 🎯 Creates targeted tests for uncovered code

## 🚀 Quick Start

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Run the generator:
```bash
python test_generator.py /path/to/your/project --output generated_tests.py
```

## 📋 Requirements

```
astroid>=2.14.2
black>=23.3.0
coverage>=7.2.3
pytest>=7.3.1
asyncio>=3.4.3
```

## 💡 Example

Here's a simple example of how the generator works. Given this Python code:

```python
class ShoppingCart:
    def add_item(self, item_name: str, quantity: int, price: float) -> float:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price < 0:
            raise ValueError("Price cannot be negative")
        return quantity * price
```

The generator will create tests like:

```python
import pytest

def test_add_item_with_valid_parameters():
    cart = ShoppingCart()
    result = cart.add_item("test_item", 2, 10.0)
    assert result == 20.0

def test_add_item_with_zero_quantity():
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.add_item("test_item", 0, 10.0)

def test_add_item_with_negative_price():
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.add_item("test_item", 1, -10.0)
```

## 🔧 Usage

### Basic Usage
```bash
python test_generator.py /path/to/your/code --output tests/generated_tests.py
```

### Running Generated Tests
```bash
pytest generated_tests.py -v
```

For async tests, install pytest-asyncio:
```bash
pip install pytest-asyncio
```

## 🎯 What It Tests

1. **Parameter Validation**
   - Valid inputs
   - Edge cases
   - Type checking

2. **Error Handling**
   - Expected exceptions
   - Error messages
   - Invalid inputs

3. **Async Functions**
   - Proper async/await usage
   - Async context handling
   - Coroutine behavior

4. **Code Coverage**
   - Branch coverage
   - Line coverage
   - Condition coverage

## 📁 Project Structure

```
your-project/
├── test_generator.py    # Main generator code
├── requirements.txt     # Project dependencies
└── sample_app.py       # Example code (optional)
```

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚠️ Known Limitations

- Complex type inference might need manual adjustments
- Generated assertions may need refinement
- Some edge cases might require manual addition
- Coverage analysis may need fine-tuning

## 📖 Advanced Usage

### Custom Test Templates

The generator creates basic assertions. You may want to enhance them for your specific needs:

```python
# Generated test
def test_function():
    assert result is not None

# Enhanced test
def test_function():
    result = function()
    assert isinstance(result, ExpectedType)
    assert min_value <= result <= max_value
    assert result meets_other_conditions
```

### Coverage Focus

To focus on untested code paths:
```bash
python test_generator.py /path/to/code --output new_tests.py
```

## 📝 License

MIT License - feel free to use this tool in your projects!

## 🤔 Questions?

If you have questions or run into issues, please open an issue on GitHub.
