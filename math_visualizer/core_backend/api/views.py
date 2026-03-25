import json
import numpy as np
import sympy as sp
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def calculate_points(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equation_str = data.get('equation', 'x')
            x_min = float(data.get('x_min', -10))
            x_max = float(data.get('x_max', 10))
            
            x = sp.Symbol('x')
            
            # Simple replacements to help users who use ^ instead of **
            equation_str = equation_str.replace('^', '**')
            expr = sp.sympify(equation_str)
            
            x_vals = np.linspace(x_min, x_max, 500)
            
            # Use lambdify to convert sympy expression to a numpy-compatible function
            f = sp.lambdify(x, expr, 'numpy')
            y_vals = f(x_vals)
            
            # If the expression doesn't contain x (e.g., '5'), lambdify might return a scalar. Let's handle it.
            if np.isscalar(y_vals):
                y_vals = np.full_like(x_vals, y_vals)
                
            points = [{'x': float(xv), 'y': float(yv)} for xv, yv in zip(x_vals, y_vals)]
            points = [p for p in points if not np.isnan(p['y']) and not np.isinf(p['y'])]
            
            return JsonResponse({'points': points, 'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e), 'status': 'error'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
