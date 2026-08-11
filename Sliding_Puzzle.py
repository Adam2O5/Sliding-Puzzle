import pygame
import random
import sys
import heapq

pygame.init()

WIDTH, HEIGHT = 370, 440
BOARD_SIZE = 4
TILE_SIZE = 80
MARGIN = 10
HEADER_HEIGHT = 70

# --- MOTYW CYBERPUNK ---
BG_COLOR = (18, 18, 18)
TILE_BG = (30, 30, 30)
CYAN_NEON = (0, 229, 255)
MAGENTA_NEON = (213, 0, 249)
GREEN_NEON = (57, 255, 20)
TEXT_INFO = (150, 150, 150)
# -----------------------

FPS = 60

# Globalna tabela (Cache) dla docelowych współrzędnych (Optymalizacja A*)
GOAL_POSITIONS = {num: ((num - 1) // BOARD_SIZE, (num - 1) % BOARD_SIZE) for num in range(1, BOARD_SIZE * BOARD_SIZE)}

def create_board():
    board = []
    num = 1
    for i in range(BOARD_SIZE):
        row = []
        for j in range(BOARD_SIZE):
            if i == BOARD_SIZE - 1 and j == BOARD_SIZE - 1:
                row.append(0) 
            else:
                row.append(num)
                num += 1
        board.append(row)
    return board

def shuffle_board(board, moves=400):
    while True:
        board_copy = [row[:] for row in board]
        empty_row, empty_col = find_empty(board_copy)
        
        for _ in range(moves):
            possible_moves = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_row, new_col = empty_row + dr, empty_col + dc
                if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                    possible_moves.append((new_row, new_col))
            
            if possible_moves:
                row, col = random.choice(possible_moves)
                board_copy[empty_row][empty_col] = board_copy[row][col]
                board_copy[row][col] = 0
                empty_row, empty_col = row, col
        
        if not is_solved(board_copy):
            return board_copy

def find_empty(board):
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 0:
                return i, j
    return None

def is_valid_move(row, col, empty_row, empty_col):
    return (row == empty_row and abs(col - empty_col) == 1) or (col == empty_col and abs(row - empty_row) == 1)

def is_solved(board):
    num = 1
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if i == BOARD_SIZE - 1 and j == BOARD_SIZE - 1:
                if board[i][j] != 0:
                    return False
            elif board[i][j] != num:
                return False
            num += 1
    return True

def draw_board(screen, board, font_small, font_large, solved=False, solving=False):
    screen.fill(BG_COLOR)
    
    # --- RYSOWANIE HUD (WIZJERA) ---
    hud_margin = MARGIN
    hud_top = MARGIN
    hud_bottom = HEADER_HEIGHT
    hud_right = WIDTH - MARGIN
    chamfer = 12
    
    # Kształt wielokąta ze ściętymi rogami
    hud_points = [
        (hud_margin + chamfer, hud_top),
        (hud_right, hud_top),
        (hud_right, hud_bottom - chamfer),
        (hud_right - chamfer, hud_bottom),
        (hud_margin, hud_bottom),
        (hud_margin, hud_top + chamfer)
    ]
    
    # Wypełnienie i obramowanie HUD
    pygame.draw.polygon(screen, TILE_BG, hud_points)
    pygame.draw.polygon(screen, CYAN_NEON, hud_points, 2)
    
    instructions = [
        "Click tile to move it",
        "Press space to shuffle",
        "Press 's' to use solver"
    ]
    
    for i, instruction in enumerate(instructions):
        y_pos = hud_top + 5 + i * 18
        text = font_small.render(instruction, True, CYAN_NEON)
        text_rect = text.get_rect(center=(WIDTH // 2, y_pos + text.get_height() // 2))
        screen.blit(text, text_rect)
    # -------------------------------
    
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            x = j * (TILE_SIZE + MARGIN) + MARGIN
            y = i * (TILE_SIZE + MARGIN) + MARGIN + HEADER_HEIGHT
            
            if board[i][j] != 0:
                if solved:
                    neon_color = GREEN_NEON
                elif solving:
                    neon_color = MAGENTA_NEON
                else:
                    neon_color = CYAN_NEON
                
                pygame.draw.rect(screen, TILE_BG, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, neon_color, (x, y, TILE_SIZE, TILE_SIZE), 3)
                
                text = font_large.render(str(board[i][j]), True, neon_color)
                text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                screen.blit(text, text_rect)


# --- ZOPTYMALIZOWANE FUNKCJE A* DLA KROTEK 1D ---

def manhattan_distance_1d(board_1d):
    distance = 0
    for i, num in enumerate(board_1d):
        if num != 0:
            current_row = i // BOARD_SIZE
            current_col = i % BOARD_SIZE
            target_row, target_col = GOAL_POSITIONS[num]
            distance += abs(current_row - target_row) + abs(current_col - target_col)
    return distance

def count_conflicts_list(tiles_in_goal):
    if len(tiles_in_goal) < 2:
        return 0

    conflicts = {tile: 0 for tile, _, _ in tiles_in_goal}

    for i, (tile1, pos1, goal1) in enumerate(tiles_in_goal):
        for j, (tile2, pos2, goal2) in enumerate(tiles_in_goal):
            if i != j:
                if (pos1 < pos2 and goal1 > goal2) or (pos1 > pos2 and goal1 < goal2):
                    conflicts[tile1] += 1
    
    tiles_to_remove = 0
    
    while any(count > 0 for count in conflicts.values()):
        tile_to_remove = max(conflicts, key=conflicts.get)
        conflicts[tile_to_remove] = 0
        tiles_to_remove += 1

        for t1, p1, g1 in tiles_in_goal:
            if t1 == tile_to_remove:
                continue
            for t2, p2, g2 in tiles_in_goal:
                if t2 == tile_to_remove:
                    if (p1 < p2 and g1 > g2) or (p1 > p2 and g1 < g2):
                        conflicts[t1] = max(0, conflicts[t1] - 1)
                    break

    return tiles_to_remove

def linear_conflict_heuristic_1d(board_1d):
    distance = manhattan_distance_1d(board_1d)
    conflicts = 0

    for row in range(BOARD_SIZE):
        row_start = row * BOARD_SIZE
        tiles_in_goal = []
        for col in range(BOARD_SIZE):
            tile = board_1d[row_start + col]
            if tile != 0:
                goal_row, goal_col = GOAL_POSITIONS[tile]
                if goal_row == row:
                    tiles_in_goal.append((tile, col, goal_col))
        conflicts += count_conflicts_list(tiles_in_goal)

    for col in range(BOARD_SIZE):
        tiles_in_goal = []
        for row in range(BOARD_SIZE):
            tile = board_1d[row * BOARD_SIZE + col]
            if tile != 0:
                goal_row, goal_col = GOAL_POSITIONS[tile]
                if goal_col == col:
                    tiles_in_goal.append((tile, row, goal_row))
        conflicts += count_conflicts_list(tiles_in_goal)

    return distance + 2 * conflicts

def get_moves_1d(board_1d, empty_idx):
    possible_moves = []
    empty_row = empty_idx // BOARD_SIZE
    empty_col = empty_idx % BOARD_SIZE
       
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_row = empty_row + dr
        new_col = empty_col + dc
            
        if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
            new_idx = new_row * BOARD_SIZE + new_col
            
            new_board = list(board_1d)
            new_board[empty_idx], new_board[new_idx] = new_board[new_idx], 0
            tile_value = board_1d[new_idx]
                
            possible_moves.append((tuple(new_board), (new_row, new_col, tile_value), new_idx))
        
    return possible_moves

def astar_solve(board, empty_row, empty_col):         
    start_board_1d = tuple(tile for row in board for tile in row)
    empty_idx = empty_row * BOARD_SIZE + empty_col
    solved_state = tuple(list(range(1, BOARD_SIZE * BOARD_SIZE)) + [0])
    
    if start_board_1d == solved_state:
        yield []
        return
    
    open_list = []
    counter = 0 
    heapq.heappush(open_list, (0, 0, counter, start_board_1d, empty_idx))
    
    closed_set = set()
    g_values = {start_board_1d: 0}
    came_from = {}
    
    node_count = 0
    max_nodes = 1000000 
    batch_size = 500 
    
    print("Rozpoczynam rozwiazywanie puzzle...")
    
    while open_list and node_count < max_nodes:
        for _ in range(batch_size):
            if not open_list:
                break
                
            node_count += 1
            if node_count % 10000 == 0:
                print(f"Przeszukano {node_count} wezlow...")
            
            f_value, g_value, _, current_board_1d, c_empty_idx = heapq.heappop(open_list)
            
            if current_board_1d == solved_state:
                print(f"Rozwiazanie znalezione! Odwiedzone wezly: {node_count}")
                path = []
                curr = current_board_1d
                while curr in came_from:
                    prev_tuple, move_info = came_from[curr]
                    path.append(move_info)
                    curr = prev_tuple
                path.reverse()
                print(f"Dlugosc rozwiazania: {len(path)} ruchow")
                yield path
                return
            
            closed_set.add(current_board_1d)

            for neighbor_1d, move_info, n_empty_idx in get_moves_1d(current_board_1d, c_empty_idx):
                if neighbor_1d in closed_set:
                    continue
                
                candidate_g_value = g_value + 1
                
                if (neighbor_1d not in g_values) or (candidate_g_value < g_values[neighbor_1d]):
                    g_values[neighbor_1d] = candidate_g_value
                    h_value = linear_conflict_heuristic_1d(neighbor_1d)
                    f_value = candidate_g_value + h_value
                    
                    counter += 1
                    came_from[neighbor_1d] = (current_board_1d, move_info)
                    heapq.heappush(open_list, (f_value, candidate_g_value, counter, neighbor_1d, n_empty_idx))
        
        yield None
    
    print(f"Nie znaleziono rozwiazania. Przeszukano {node_count} wezlow.")
    yield False

def execute_solution_with_animation(screen, board, solution, font_small, font_large, delay=300):
    if not solution:
        print("Brak rozwiazania do wykonania!")
        return board
    
    current_board = [row[:] for row in board]
    empty_row, empty_col = find_empty(current_board)
    
    print(f"Wykonuje rozwiazanie w {len(solution)} ruchach...")
    
    for i, move_info in enumerate(solution):
        tile_row, tile_col, tile_value = move_info
        
        current_board[empty_row][empty_col] = tile_value
        current_board[tile_row][tile_col] = 0
        empty_row, empty_col = tile_row, tile_col
        
        print(f"Ruch {i+1}/{len(solution)}: Przesunieto pole {tile_value}")
        
        draw_board(screen, current_board, font_small, font_large, solving=True)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        pygame.time.wait(delay)
    
    print("Rozwiazanie wykonane pomyslnie!")
    return current_board


# --- LOGIKA GŁÓWNA ---

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("15 Puzzle - Cyberpunk")
    clock = pygame.time.Clock()
    
    font_small = pygame.font.Font(None, 24)
    font_large = pygame.font.Font(None, 36)
    
    board = create_board()
    board = shuffle_board(board)
    empty_row, empty_col = find_empty(board)
    solved = False
    
    solving = False
    solver_generator = None
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not solving:
                    board = create_board()
                    board = shuffle_board(board)
                    empty_row, empty_col = find_empty(board)
                    solved = False
                
                elif event.key == pygame.K_s and not solved and not solving:
                    print("Rozpoczynam rozwiazywanie A*...")
                    solver_generator = astar_solve(board, empty_row, empty_col)
                    solving = True
            
            if event.type == pygame.MOUSEBUTTONDOWN and not solved and not solving:
                mouseX, mouseY = pygame.mouse.get_pos()
                
                col = (mouseX - MARGIN) // (TILE_SIZE + MARGIN)
                row = (mouseY - MARGIN - HEADER_HEIGHT) // (TILE_SIZE + MARGIN)
                
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    if is_valid_move(row, col, empty_row, empty_col):
                        board[empty_row][empty_col] = board[row][col]
                        board[row][col] = 0
                        empty_row, empty_col = row, col 
                        
                        if is_solved(board):
                            solved = True
        
        if solving:
            try:
                result = next(solver_generator)
                if result is not None: 
                    solving = False
                    if result is not False:
                        board = execute_solution_with_animation(
                            screen, board, result, font_small, font_large
                        )
                        empty_row, empty_col = find_empty(board)
                        solved = is_solved(board)
            except StopIteration:
                solving = False

        draw_board(screen, board, font_small, font_large, solved, solving)
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()