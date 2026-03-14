import json
import math
import sympy as sp
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def evaluate_equation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equation_str = data.get('equation', 'x')
            x_min = float(data.get('x_min', -10))
            x_max = float(data.get('x_max', 10))
            num_points = int(data.get('num_points', 200))

            x = sp.Symbol('x')
            # Parse the string into a sympy expression
            expr = sp.sympify(equation_str)
            
            # Create a lambda function for fast evaluation
            f = sp.lambdify(x, expr, 'math')
            
            # Generate points
            step = (x_max - x_min) / max(1, (num_points - 1))
            x_vals = [x_min + i * step for i in range(num_points)]
            
            points = []
            for x_val in x_vals:
                try:
                    y_val = f(x_val)
                    if isinstance(y_val, complex) or math.isnan(y_val) or math.isinf(y_val):
                        continue
                    points.append({"x": float(x_val), "y": float(y_val)})
                except Exception:
                    # Ignore points where the function is undefined (e.g., division by zero)
                    pass

            return JsonResponse({"status": "success", "points": points})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    return JsonResponse({"status": "error", "message": "Only POST requests are allowed"}, status=405)
