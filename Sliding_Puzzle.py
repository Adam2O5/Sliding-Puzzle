import pygame
import random
import sys
import heapq
import copy
import time

pygame.init()

WIDTH, HEIGHT = 370, 430
BOARD_SIZE = 4
TILE_SIZE = 80
MARGIN = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
ORANGE = (255, 160, 0)
GREEN = (100, 200, 100)
RED = (200, 100, 100)
FPS = 60

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
    
    if(is_solved(board_copy)):
        return shuffle_board(board_copy)
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

def draw_board(screen, board, solved=False, solving=False):
    screen.fill(WHITE)
    
    font_small = pygame.font.Font(None, 24)
    instructions = [
        "Click tile to move it",
        "Press space to shuffle",
        "Press 's' to use solver"
    ]
    
    for i, instruction in enumerate(instructions):
        text = font_small.render(instruction, True, BLACK)
        screen.blit(text, (100, 10 + i * 20))
    
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            x = j * (TILE_SIZE + MARGIN) + MARGIN
            y = i * (TILE_SIZE + MARGIN) + MARGIN + 60
            
            if board[i][j] == 0:
                pygame.draw.rect(screen, GRAY, (x, y, TILE_SIZE, TILE_SIZE))
            else:
                if solved:
                    color = GREEN
                elif solving:
                    color = RED
                else:
                    color = ORANGE
                
                pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 2)
                
                font = pygame.font.Font(None, 36)
                text = font.render(str(board[i][j]), True, WHITE)
                text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                screen.blit(text, text_rect)

def manhattan_distance(board):
    distance = 0
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            num = board[x][y]
            if num != 0:
                target_row = (num - 1) // BOARD_SIZE
                target_col = (num - 1) % BOARD_SIZE
                  
                distance += abs(x - target_row) + abs(y - target_col)
    return distance

def count_conflicts_in_line(board, line_index, is_row):# true = rzêdy, false = kolumny
    tiles_in_goal_line = []

    for i in range(BOARD_SIZE):
        if is_row:
            tile = board[line_index][i]
            current_pos = i
        else:
            tile = board[i][line_index]
            current_pos = i

        if tile != 0:
            goal_row = (tile - 1) // BOARD_SIZE
            goal_col = (tile - 1) % BOARD_SIZE
            if is_row:
                if goal_row == line_index:
                    tiles_in_goal_line.append((tile, current_pos, goal_col))
            else:
                if goal_col == line_index:
                    tiles_in_goal_line.append((tile, current_pos, goal_row))

    if len(tiles_in_goal_line) < 2:
        return 0

    conflicts = {}

    for i, (tile1, pos1, goal1) in enumerate(tiles_in_goal_line):
        conflicts[tile1] = 0
        for j, (tile2, pos2, goal2) in enumerate(tiles_in_goal_line):
            if i != j:
                if (pos1 < pos2 and goal1 > goal2) or (pos1 > pos2 and goal1 < goal2):
                    conflicts[tile1] += 1
    
    tiles_to_remove = 0
    remaining_conflicts = conflicts.copy()

    while any(count > 0 for count in remaining_conflicts.values()):
        max_conflicts = max(remaining_conflicts.values())
        tile_to_remove = None

        for tile, count in remaining_conflicts.items():
            if count == max_conflicts:
                tile_to_remove = tile
                break

        remaining_conflicts[tile_to_remove] = 0
        tiles_to_remove += 1

        for tile1, pos1, goal1 in tiles_in_goal_line:
            if tile1 == tile_to_remove:
                continue
            for tile2, pos2, goal2 in tiles_in_goal_line:
                if tile2 == tile_to_remove:
                    if (pos1 < pos2 and goal1 > goal2) or (pos1 > pos2 and goal1 < goal2):
                        remaining_conflicts[tile1] = max(0, remaining_conflicts[tile1] - 1)
                    break

    return tiles_to_remove

def linear_conflict_heuristic(board):
    manhattan_dist = manhattan_distance(board)

    linear_conflicts = 0

    for row in range(BOARD_SIZE):
        linear_conflicts += count_conflicts_in_line(board, row, True)

    for col in range(BOARD_SIZE):
        linear_conflicts += count_conflicts_in_line(board, col, False)  

    return manhattan_dist + 2 * linear_conflicts

def get_moves(board):
    possible_moves = []
    empty_row, empty_col = find_empty(board)
        
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
       
    for dr, dc in moves:
        new_row, new_col = empty_row + dr, empty_col + dc
            
        if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
            new_board = [row[:] for row in board] 
            new_board[empty_row][empty_col], new_board[new_row][new_col] = new_board[new_row][new_col], 0

            tile_value = board[new_row][new_col]
                
            possible_moves.append((new_board, (new_row, new_col, tile_value)))
        
    return possible_moves

def board_to_tuple(board):
    return tuple(tuple(row) for row in board)

def astar_solve(board):         
    start_state = [row[:] for row in board]
    
    if is_solved(start_state):
        return []
    
    #inicjalizacja priority queue
    open_list = []
    heapq.heappush(open_list, (0, 0, start_state, []))
    
    #zbior odwiedzonych stanow
    closed_set = set()
    
    #slownik najlepszych g_value dla kazdego stanu
    g_values = {board_to_tuple(start_state): 0}
    
    node_count = 0
    max_nodes = 1000000  #limit nodow dla bezpieczenstwa
    
    print("Rozpoczynam rozwiazywanie puzzle...")
    
    while open_list and node_count < max_nodes:
        node_count += 1
        
        if node_count % 10000 == 0:
            print(f"Przeszukano {node_count} wezlow...")
        
        #pobieramy stan z najnizszym f_value
        f_value, g_value, current_board, path = heapq.heappop(open_list)
        current_tuple = board_to_tuple(current_board)
        
        #sprawdzamy, czy obecny stan byl liczony
        if current_tuple in closed_set:
            continue
        closed_set.add(current_tuple)

        if is_solved(current_board):
            print(f"Rozwiazanie znalezione! Odwiedzone wezly: {node_count}")
            print(f"Dlugosc rozwiazania: {len(path)} ruchow")
            return path
        
        #sprawdzamy mozliwe ruchy dla wybranego kandydata
        for neighbor_board, move_info in get_moves(current_board):
            neighbor_tuple = board_to_tuple(neighbor_board)
            
            candidate_g_value = g_value + 1
            
            #sprawdzamy czy kandydat jest optymalny
            if (neighbor_tuple not in g_values) or (candidate_g_value < g_values[neighbor_tuple]):
                g_values[neighbor_tuple] = candidate_g_value
                h_value = linear_conflict_heuristic(neighbor_board)
                f_value = candidate_g_value + h_value
                
                new_path = path + [move_info]
                heapq.heappush(open_list, (f_value, candidate_g_value, neighbor_board, new_path))
    
    print(f"Nie znaleziono rozwiazania. Przeszukano {node_count} wezlow.")
    return None

def execute_solution_with_animation(screen, board, solution, delay=300):# delay
    if not solution:
        print("Brak rozwiazania do wykonania!")
        return board
    
    current_board = [row[:] for row in board]
    
    print(f"Wykonuje rozwiazanie w {len(solution)} ruchach...")
    
    for i, move_info in enumerate(solution):
        tile_row, tile_col, tile_value = move_info
        
        empty_row, empty_col = find_empty(current_board)
        
        current_board[empty_row][empty_col], current_board[tile_row][tile_col] = tile_value, 0
        
        print(f"Ruch {i+1}/{len(solution)}: Przesunieto pole {tile_value}")
        
        draw_board(screen, current_board, solving=True)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return current_board
        
        pygame.time.wait(delay)
    
    print("Rozwiazanie wykonane pomyslnie!")
    return current_board

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("15 Puzzle")
    clock = pygame.time.Clock()
    
    board = create_board()
    board = shuffle_board(board)
    solved = False
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    board = create_board()
                    board = shuffle_board(board)
                    solved = False
                
                elif event.key == pygame.K_s and not solved:
                    print("Rozpoczynam rozwiazywanie A*...")
                    solution = astar_solve(board)
                    
                    if solution:
                        board = execute_solution_with_animation(screen, board, solution)
                        solved = is_solved(board)
                    else:
                        print("Nie mozna znalezc rozwiazania!")
            
            if event.type == pygame.MOUSEBUTTONDOWN and not solved:
                mouseX, mouseY = pygame.mouse.get_pos()
                
                col = (mouseX - MARGIN) // (TILE_SIZE + MARGIN)
                row = (mouseY - MARGIN - 60) // (TILE_SIZE + MARGIN)
                
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    empty_row, empty_col = find_empty(board)
                    if is_valid_move(row, col, empty_row, empty_col):
                        board[empty_row][empty_col] = board[row][col]
                        board[row][col] = 0
                        
                        if is_solved(board):
                            solved = True
        
        draw_board(screen, board, solved)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()