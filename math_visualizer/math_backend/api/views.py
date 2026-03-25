import sympy as sp
import math
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class EvaluateEquationView(APIView):
    def post(self, request):
        equation = request.data.get('equation', '')
        x_min = float(request.data.get('x_min', -10))
        x_max = float(request.data.get('x_max', 10))
        num_points = int(request.data.get('num_points', 400)) # Increased for smoother lines

        if not equation:
            return Response({'error': 'Equation is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # We define 'x' as our symbol
            x = sp.Symbol('x')
            
            # Replace common syntax issues like '^' instead of '**' for exponents
            clean_equation = equation.replace('^', '**')
            
            # Sympify converts the string to a sympy expression
            expr = sp.sympify(clean_equation)
            
            # Create a lambda function for fast numerical evaluation using standard math
            f = sp.lambdify(x, expr, modules=['math'])
            
            # Generate coordinate points
            step = (x_max - x_min) / num_points
            points = []
            for i in range(num_points + 1):
                vx = x_min + i * step
                try:
                    vy = f(vx)
                    
                    # Ignore complex numbers
                    if isinstance(vy, complex) and vy.imag != 0:
                        continue
                        
                    # Filter out Infinity and NaN
                    if not math.isnan(vy) and not math.isinf(vy):
                        points.append({'x': float(vx), 'y': float(vy)})
                except (ValueError, ZeroDivisionError, TypeError):
                    # Handle domain errors gracefully (e.g. log(-1) or 1/0)
                    pass
            
            return Response({'points': points, 'equation': str(expr)})
            
        except Exception as e:
            return Response({'error': f"Failed to parse or evaluate equation: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
