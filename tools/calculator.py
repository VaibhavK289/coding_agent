def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract two numbers."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers. Raises ValueError if division by zero is attempted."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def main():
    print("Simple Calculator")
    print("Supported operations: +, -, *, /")
    
    while True:
        try:
            operation = input("Enter operation (+, -, *, /) or 'exit' to quit: ").strip()
            if operation.lower() == 'exit':
                print("Exiting calculator.")
                break
            
            if operation not in ['+', '-', '*', '/']:
                print("Invalid operation. Please choose +, -, *, or /.")
                continue
                
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
            
            if operation == '+':
                result = add(num1, num2)
            elif operation == '-':
                result = subtract(num1, num2)
            elif operation == '*':
                result = multiply(num1, num2)
            elif operation == '/':
                result = divide(num1, num2)
            
            print(f"Result: {result}")
            
        except ValueError:
            print("Error: Invalid input. Please enter numbers only.")
        except ZeroDivisionError:
            print("Error: Cannot divide by zero.")
        except KeyboardInterrupt:
            print("\nCalculator interrupted. Exiting.")
            break

if __name__ == "__main__":
    main()