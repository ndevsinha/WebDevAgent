import math
from rest_framework.views import APIView
from rest_framework.response import Response

class CurveListView(APIView):
    def get(self, request):
        curves = [
            {"id": "helix", "name": "3D Helix"},
            {"id": "torus_knot", "name": "Torus Knot (Trefoil)"},
            {"id": "lorenz", "name": "Lorenz Attractor"},
            {"id": "viviani", "name": "Viviani's Curve"},
            {"id": "fractal_tree", "name": "3D Fractal Tree"},
            {"id": "sierpinski", "name": "Sierpinski Tetrahedron"}
        ]
        return Response(curves)

class CurveDataView(APIView):
    def get(self, request, curve_id):
        data = []
        if curve_id == "helix":
            for i in range(1000):
                t = i * 0.1
                data.append({"x": math.cos(t) * 10, "y": math.sin(t) * 10, "z": (t - 50) * 0.5})
                
        elif curve_id == "torus_knot":
            p, q = 2, 3
            for i in range(1000):
                t = i * 0.05
                r = math.cos(q * t) + 2
                data.append({"x": r * math.cos(p * t) * 5, "y": r * math.sin(p * t) * 5, "z": -math.sin(q * t) * 5})
                
        elif curve_id == "lorenz":
            x, y, z = 0.1, 0.0, 0.0
            sigma, rho, beta = 10.0, 28.0, 8.0/3.0
            dt = 0.01
            for _ in range(3000):
                dx = sigma * (y - x) * dt
                dy = (x * (rho - z) - y) * dt
                dz = (x * y - beta * z) * dt
                x += dx; y += dy; z += dz
                data.append({"x": x, "y": y, "z": z - 25})
                
        elif curve_id == "viviani":
            r = 10
            for i in range(1000):
                t = i * 0.1
                data.append({"x": r * (1 + math.cos(t)) - r, "y": r * math.sin(t), "z": 2 * r * math.sin(t / 2)})
                
        elif curve_id == "fractal_tree":
            # 3D Recursive Branching Tree
            def grow(x, y, z, length, theta, phi, depth):
                if depth == 0: return
                
                # Spherical to Cartesian projection for the new branch endpoint
                nx = x + length * math.sin(phi) * math.cos(theta)
                ny = y - length * math.cos(phi) # y goes up in visualizer when negative
                nz = z + length * math.sin(phi) * math.sin(theta)
                
                # Draw the branch
                data.append({"x": x, "y": y, "z": z})
                data.append({"x": nx, "y": ny, "z": nz})
                data.append(None) # D3 Line break
                
                # Recursively grow 3 new branches from the new endpoint
                grow(nx, ny, nz, length * 0.7, theta + 0.8, phi + 0.4, depth - 1)
                grow(nx, ny, nz, length * 0.7, theta - 0.8, phi + 0.4, depth - 1)
                grow(nx, ny, nz, length * 0.7, theta + 1.5, phi - 0.2, depth - 1)

            # Start the tree root at y=15, growing upwards
            grow(0, 15, 0, 10, 0, 0, 6) # depth 6 = thousands of branches
            
        elif curve_id == "sierpinski":
            # 3D Sierpinski Tetrahedron
            def sierpinski(p1, p2, p3, p4, depth):
                if depth == 0:
                    # Draw the 6 edges of the current tetrahedron
                    edges = [(p1, p2), (p2, p3), (p3, p1), (p1, p4), (p2, p4), (p3, p4)]
                    for pA, pB in edges:
                        data.append({"x": pA[0], "y": pA[1], "z": pA[2]})
                        data.append({"x": pB[0], "y": pB[1], "z": pB[2]})
                        data.append(None) # D3 Line break
                else:
                    # Calculate midpoints of all 6 edges
                    def mid(a, b): return [(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2]
                    m12, m13, m14 = mid(p1,p2), mid(p1,p3), mid(p1,p4)
                    m23, m24, m34 = mid(p2,p3), mid(p2,p4), mid(p3,p4)
                    
                    # Recursively build 4 smaller tetrahedrons at the corners
                    sierpinski(p1, m12, m13, m14, depth - 1)
                    sierpinski(m12, p2, m23, m24, depth - 1)
                    sierpinski(m13, m23, p3, m34, depth - 1)
                    sierpinski(m14, m24, m34, p4, depth - 1)
            
            # Start with a regular tetrahedron centered around the origin
            s = 15
            p1 = [ s,  s,  s]
            p2 = [-s, -s,  s]
            p3 = [-s,  s, -s]
            p4 = [ s, -s, -s]
            sierpinski(p1, p2, p3, p4, 4) # depth 4 = 256 tetrahedrons

        else:
            return Response({"error": "Curve not found"}, status=404)
        
        return Response({"id": curve_id, "points": data})
