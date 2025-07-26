
import queue



def search_zones(board):
    '''
    # 陣地を判定して座標を返して壁の座標も返す。
    # 入力
    #    board: 盤面　(w: 壁、@,空白地帯)
    #
    # 戻り値 zone:陣地の座標
    #     walls:壁の座標
    '''
    walls = []
    width = len(board[0])
    height = len(board)
    board_com = [[0 for i in range(width+1)]for j in range(height+1)]
    queue_next = queue.Queue()
    zones = []
    for ox in range(width):
        for oy in range(height):
            zone = []
            wall = set()
            if board[oy][ox] == '@':
                queue_next.put((ox, oy))
            a = -1
            b = -1
            flag_outside =False
            while queue_next.qsize() != 0:
                tx, ty = queue_next.get()
                if board_com[ty][tx] == True:
                    continue
                board_com[ty][tx] = True
                if board[ty][tx] != "w":
                    zone.append((tx,ty))
                for dx, dy in [[0,-1], [0, 1], [-1, 0], [1, 0]]:
                        nx = tx + dx
                        ny = ty + dy
                        if nx >= width or ny < 0 or ny >= height or nx < 0:#範囲外だったらフラグを立てる
                            flag_outside = True
                            continue
                        if board[ny][nx] == "w":
                            wall.add((nx,ny))
                        elif board[ny][nx] == "@":#何もなかったらキュー座標を追加
                            queue_next.put((nx, ny))

            if not flag_outside and len(zone) > 0:
                walls.append(wall)
                zones.append(zone)


    return zones,walls




