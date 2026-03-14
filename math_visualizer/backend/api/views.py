import json
import math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# A dictionary of safe mathematical functions and constants
SAFE_MATH_ENV = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sqrt': math.sqrt,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
    'abs': abs,
}

@csrf_exempt
def calculate_points(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equation = data.get('equation', 'x')
            
            # Simple sanitization
            equation = equation.replace('^', '**')
            
            x_min = float(data.get('x_min', -10))
            x_max = float(data.get('x_max', 10))
            step = float(data.get('step', 0.5))

            if x_min >= x_max:
                return JsonResponse({'error': 'x_min must be less than x_max'}, status=400)
            if step <= 0:
                return JsonResponse({'error': 'step must be greater than 0'}, status=400)

            # Limit number of points to avoid massive processing
            if (x_max - x_min) / step > 1000:
                return JsonResponse({'error': 'Too many points. Increase step or reduce range.'}, status=400)

            points = []
            x = x_min
            while x <= x_max:
                env = SAFE_MATH_ENV.copy()
                env['x'] = x
                try:
                    # Evaluate the equation safely
                    y = eval(equation, {"__builtins__": {}}, env)
                    # Only add valid real numbers
                    if isinstance(y, (int, float)) and not math.isnan(y) and not math.isinf(y):
                        points.append({'x': round(x, 4), 'y': round(y, 4)})
                except ZeroDivisionError:
                    # Handle division by zero natively
                    pass
                except Exception as e:
                    pass # other evaluation errors at this point
                
                x += step

            if not points:
                return JsonResponse({'error': 'Invalid equation or no valid points evaluated.'}, status=400)

            return JsonResponse({'points': points})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
