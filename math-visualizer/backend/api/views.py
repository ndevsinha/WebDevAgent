import json
import numpy as np
import sympy as sp
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def evaluate_expression(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            expression = body.get('expression', 'x**2')
            x_min = float(body.get('x_min', -10))
            x_max = float(body.get('x_max', 10))
            num_points = int(body.get('num_points', 500))

            x = sp.Symbol('x')
            
            # Parse the expression
            # Use sympify and handle common math functions implicitly
            parsed_expr = sp.sympify(expression)

            # Create lambda function
            f = sp.lambdify(x, parsed_expr, modules=['numpy', 'math'])

            x_vals = np.linspace(x_min, x_max, num_points)
            
            # Use exception catching on evaluation
            # It might fail if the function doesn't support array inputs properly
            try:
                y_vals = f(x_vals)
            except Exception:
                # Fallback to list comprehension for non-vectorized functions
                y_vals = [f(xv) for xv in x_vals]

            data = []
            
            # Sometimes f returns a single scalar if expression has no x (e.g. '5')
            if np.isscalar(y_vals):
                y_vals = np.full_like(x_vals, y_vals)
                
            for xv, yv in zip(x_vals, y_vals):
                try:
                    # check if yv is complex
                    if isinstance(yv, complex):
                        if abs(yv.imag) > 1e-10:
                            continue # skip complex values
                        yv = yv.real
                    if not np.isnan(yv) and not np.isinf(yv):
                        data.append({'x': float(xv), 'y': float(yv)})
                except:
                    pass

            return JsonResponse({'status': 'success', 'data': data})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
