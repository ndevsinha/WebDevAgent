from rest_framework.decorators import api_view
from rest_framework.response import Response
import sympy as sp
import numpy as np

@api_view(['POST'])
def calculate_plot(request):
    equation_str = request.data.get('equation', 'x')
    x_min = float(request.data.get('x_min', -10))
    x_max = float(request.data.get('x_max', 10))
    steps = int(request.data.get('steps', 100))

    try:
        # Define the variable
        x = sp.Symbol('x')
        
        # Parse the expression
        # To make it user-friendly, we can allow math functions like sin, cos without prefixes
        # Sympy parse_expr handles basic functions, but we need to ensure it uses sympy's functions
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
        transformations = (standard_transformations + (implicit_multiplication_application,))
        
        # Replace common JS/human notations to python
        equation_str = equation_str.replace('^', '**')

        expr = parse_expr(equation_str, transformations=transformations)

        # Generate x values
        x_vals = np.linspace(x_min, x_max, steps)
        
        # Create a fast numerical function using lambdify
        # Handle cases where equation is a constant
        f = sp.lambdify(x, expr, modules=['numpy'])
        
        # Evaluate y values
        y_vals = f(x_vals)
        
        # If the result is a scalar (constant function), make it an array
        if np.isscalar(y_vals):
            y_vals = np.full_like(x_vals, y_vals)
            
        # Handle NaN and Infinity by replacing them with None for JSON serialization
        points = []
        for i in range(len(x_vals)):
            y = float(y_vals[i])
            if np.isnan(y) or np.isinf(y) or abs(y) > 1000:
                continue
            points.append({'x': float(x_vals[i]), 'y': y})

        return Response({'points': points, 'equation': equation_str})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
