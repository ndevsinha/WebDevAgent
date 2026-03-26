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
            equation = data.get('equation', 'x')
            # default bounds
            x_min = float(data.get('x_min', -10))
            x_max = float(data.get('x_max', 10))
            step = float(data.get('step', 0.1))

            if step <= 0:
                return JsonResponse({'status': 'error', 'message': 'Step must be positive'})
            if x_min >= x_max:
                return JsonResponse({'status': 'error', 'message': 'x_min must be less than x_max'})

            x = sp.symbols('x')
            expr = sp.sympify(equation)
            
            # Use lambdify to convert the sympy expression to a function that evaluates with numpy
            f = sp.lambdify(x, expr, modules=['numpy', 'math'])
            
            x_vals = np.arange(x_min, x_max + step, step)
            
            # To handle constant functions where lambdify might return a scalar
            y_vals = f(x_vals)
            if np.isscalar(y_vals):
                y_vals = np.full_like(x_vals, y_vals)
            
            points = []
            for xv, yv in zip(x_vals, y_vals):
                if np.isreal(yv) and np.isfinite(yv):
                    points.append({'x': float(xv), 'y': float(yv)})
            
            return JsonResponse({'status': 'success', 'points': points})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Only POST is allowed'})
