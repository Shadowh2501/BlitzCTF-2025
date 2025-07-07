import os
import random
import time
from flask import Flask, session, render_template, request, jsonify
from collections import deque


app = Flask(
    __name__,
    static_folder='static',
    static_url_path='/static'
)

app.config['DEBUG'] = True
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()
app.secret_key = os.urandom(24)

WIDTH, HEIGHT = 25, 25

def build_maze(width, height):
    w, h = width, height
    visited = [[False] * (h + 1) for _ in range(w + 1)]
    adj = {(x, y): set() for x in range(w + 1) for y in range(h + 1)}

    def neighbors(cx, cy):
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx <= w and 0 <= ny <= h:
                yield nx, ny

    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        cx, cy = stack[-1]
        unv = [p for p in neighbors(cx, cy) if not visited[p[0]][p[1]]]
        if unv:
            nx, ny = random.choice(unv)
            visited[nx][ny] = True
            adj[(cx, cy)].add((nx, ny))
            adj[(nx, ny)].add((cx, cy))
            stack.append((nx, ny))
        else:
            stack.pop()
    return adj

def find_solution(adj, width, height):
    start, end = (0, 0), (width, height)
    q = deque([start])
    parent = {start: None}
    while q:
        cur = q.popleft()
        if cur == end:
            break
        for nxt in adj[cur]:
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)
    path = []
    node = end
    while parent[node] is not None:
        px, py = parent[node]
        x, y   = node
        if x > px: path.append('R')
        elif x < px: path.append('L')
        elif y > py: path.append('U')
        else:        path.append('D')
        node = parent[node]
    return ''.join(reversed(path))

MAZE = build_maze(WIDTH, HEIGHT)
SOLUTION_PATH = find_solution(MAZE, WIDTH, HEIGHT)

@app.route('/')
def index():
    session.clear()
    session['x'], session['y'] = 0, 0
    session['last_move'] = 0.0
    session['path'] = ''
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    # --- Rate limit removed for faster testing ---
    data = request.get_json() or {}
    dir = data.get('move')
    dx = dy = 0
    if dir == 'up':
        dy = 1; session['path'] += 'U'
    elif dir == 'down':
        dy = -1; session['path'] += 'D'
    elif dir == 'right':
        dx = 1; session['path'] += 'R'
    elif dir == 'left':
        dx = -1; session['path'] += 'L'
    else:
        return jsonify(success=False, message='Invalid move'), 400

    x, y = session['x'], session['y']
    nx, ny = x + dx, y + dy
    if (nx, ny) in MAZE.get((x, y), []):
        session['x'], session['y'] = nx, ny
        if (nx, ny) == (WIDTH, HEIGHT):
            return jsonify(success=True, win=True)
        return jsonify(success=True, x=nx, y=ny)
    return jsonify(success=False, message='bonk, please be careful :)')

@app.route('/submit', methods=['POST'])
def submit():
    guess = (request.get_json() or {}).get('code', '')
    if guess == SOLUTION_PATH:
        return jsonify(success=True, flag=os.getenv('FLAG', 'CTF{dummy_flag}'))
    return jsonify(success=False, message='Incorrect secret code.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)