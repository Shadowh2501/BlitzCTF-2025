import requests

URL = "http://127.0.0.1:5000"  # Change to your server's address if needed!
session = requests.Session()
session.get(URL)

WIDTH, HEIGHT = 25, 25
END = (WIDTH, HEIGHT)

DIRS = [
    ("up",    0,  1, "U", "down"),
    ("down",  0, -1, "D", "up"),
    ("right", 1,  0, "R", "left"),
    ("left", -1,  0, "L", "right"),
]

def move(direction):
    r = session.post(f"{URL}/move", json={"move": direction})
    return r.json()

def solve():
    # Stack: (x, y, path_so_far, unexplored_directions)
    stack = []
    visited = set()
    stack.append((0, 0, "", list(DIRS)))
    visited.add((0,0))
    while stack:
        x, y, path, directions = stack[-1]
        if (x, y) == END:
            return path
        if not directions:
            # All directions tried, need to backtrack
            if len(stack) > 1:
                prev_x, prev_y, prev_path, _ = stack[-2]
                # Move back to previous position
                for dir, dx, dy, dchar, backdir in DIRS:
                    if (x + dx, y + dy) == (prev_x, prev_y):
                        move(dir)
                        break
            stack.pop()
            continue
        dir, dx, dy, dchar, backdir = directions.pop()
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= WIDTH and 0 <= ny <= HEIGHT):
            continue
        if (nx, ny) in visited:
            continue
        res = move(dir)
        if res.get("success"):
            visited.add((nx, ny))
            stack.append((nx, ny, path + dchar, list(DIRS)))
    return None

solution_path = solve()
print("Solution path:", solution_path)

if solution_path:
    resp = session.post(f"{URL}/submit", json={"code": solution_path})
    print(resp.json())
else:
    print("No path found.") 