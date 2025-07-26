import yaml
import string
import zone
import copy
from enum import IntEnum

class BuilderAction(IntEnum):
    Wait = 0

    MoveUp = 1
    MoveDown = 2
    MoveLeft = 3
    MoveRight = 4
    MoveUpLeft = 5
    MoveUpRight = 6
    MoveDownLeft = 7
    MoveDownRight = 8

    BuildUp = 9
    BuildDown = 10
    BuildLeft = 11
    BuildRight = 12

    BreakUp = 13
    BreakDown = 14
    BreakLeft = 15
    BreakRight = 16

    def parse(x: int):
        if x < BuilderAction.Wait or x > BuilderAction.BreakRight:
            return None
        return BuilderAction(x)

class Board:

    # url を受け取り各種変数を設定
    def __init__(self,url):
        with open(url, encoding='utf-8') as file:
            self.obj        = yaml.safe_load(file)      # ファイルを読み込む

        self.width          = self.obj["fieldWidth"]    # 盤面の縦の長さ
        self.height         = self.obj["fieldHeight"]   # 盤面の横の長さ
        self.f_point        = [0,0,0]                   # 先手のポイント(城ポイント, 城壁ポイント, 陣地ポイント)
        self.s_point        = [0,0,0]                   # 後手のポイント
        self.firstbuilders  = self.obj["firstAttacker"]["builders"]     # 先手の職人一覧
        self.secondbuilders = self.obj["secondAttacker"]["builders"]    # 後手の職人一覧
        self.shirofactor    = self.obj["shiroFactor"]   # 城ポイント係数
        self.johekifactor   = self.obj["johekiFactor"]  # 陣地ポイント係数
        self.jinchifactor   = self.obj["jinchiFactor"]  # 陣地ポイント係数
        self.turninterval   = self.obj["turnInterval"]  # １ターンあたりの制限時間
        self.turncount      = self.obj["turnCount"]     # 最大ターン数
        self.turn_now       = 1             # 現在のターン数
        self.now_regions    = [[],[]]       # それぞれのプレイヤーの陣地
        self.old_regions    = [[],[]]       # それぞれのプレイヤーの１ターン前の陣地
        self.not_regions    = [[],[]]       # それぞれのプレイヤーの解放された陣地
        self.regions_count  = [0,0]         # それぞれのプレイヤーの陣地数
        self.shiro_count    = [0,0]         # それぞれのプレイヤーが所持している城の数
        self.board          = [['.'] * self.width for _ in range(self.height)]      # 空の盤面を作る
        self.ike_point      = []            # 池の座標
        self.siro_point     = []            # 城の座標
        self.honyaku = { 0: "stay",1:"su",2:"sd",3:"sl",4: "sr",5: "sul",6: "sur",7: "sdl",8: "sdr",9: "wu",10: "wd",11: "wl",12: "wr",13: "bu",14: "bd",15: "bl",16: "br"}
        I =0
        self.zahyo          = {}
        self.log            = []

        # フィールドの入力
        for i in self.obj["field"]:
            J =0

            for j in i:
                self.board[I][J] = j

                if j == "@":
                    self.ike_point.append(str(J)+"/"+str(I))

                elif j == "+":
                    self.siro_point.append(str(J)+"/"+str(I))
                elif j != ".":
                    for w in self.firstbuilders + self.secondbuilders:
                        if w == j:
                            self.zahyo[w] = [I,J]
                            break
                J+=1

            I += 1


    def isAction(self,name,act):
        old_borad = copy.deepcopy(self.board)
        old_zahyo = copy.deepcopy(self.zahyo)
        name =str(name)
        y,x = self.zahyo[name]
        do = [x,y,self.honyaku[act],name]
        if name in self.firstbuilders:
            wall = "w"
        else:
            wall = "W"
        self.action(do,[],wall)
        if old_borad == self.board:
            return 0
        else :
            self.board = old_borad
            self.zahyo = old_zahyo
            return 1

    # 盤面をきれいに出力する関数(テスト用)
    def out(self):
        for i in self.board:

            for j in i: 

                while len(j) < 4:
                    j += " "
                print(j, end="")
            print()
        print()
    

    # 盤面情報を受け取りそれぞれのプレイヤーのポイントを数える関数
    def point(self):
        self.f_point  = [0,0,0]
        self.s_point  = [0,0,0]

        # 城壁の数を数える
        for i in self.board:

            for w in i:
                if 'w' in w:
                    self.f_point[1] += 1
                elif "W" in w:
                    self.s_point[1] += 1
        self.regions_count[0] = len(self.now_regions[0]) + len(self.not_regions[0])
        self.regions_count[1] = len(self.now_regions[1]) + len(self.not_regions[1])
        self.f_point[0]  = self.shiro_count[0] * self.obj["shiroFactor"]
        self.s_point[0]  = self.shiro_count[1] * self.obj["shiroFactor"]
        self.f_point[1] *= self.obj["johekiFactor"]
        self.s_point[1] *= self.obj["johekiFactor"]
        self.f_point[2]  = self.regions_count[0] * self.obj["jinchiFactor"]
        self.s_point[2]  = self.regions_count[1] * self.obj["jinchiFactor"]

        return [self.f_point,self.s_point]


    # point 関数から情報を受け取りそれぞれのプレイヤーの総合得点を数える関数
    def sum(self,player):
        points = self.point()
        count = 0
        
        if player == "first":
            for w in points[0]:
                count += w

        elif player == "second":

            for w in points[1]:
                count += w

        elif player == "and":
            return [self.sum("first"),self.sum("second")]

        else :
            return points
        return count  


    # 入力された行動を順番に並べ、action 関数に送る関数
    def game(self,act):
        self.turn_now += 1
        self.log.append({"turn":self.turn_now})
        self.log[-1].update(dict(act))
        key = list(act)
        for w in key:
            act[str(w)] = self.honyaku[act[w]]
        # どちらのターンか数える
        if self.turn_now % 2  == 1:
            me = self.firstbuilders

        else:
            me = self.secondbuilders
        
        rank = ["stay", "b","w","s"]    # 行動の早さ順の表
        do = []     # 職人の座標、行動、名前を一つに管理する
        no = []     # 職人の移動先の座標を取得する（職人同士が同じ移動先をしたいした場合用）
        J = 0
        I = 0
        y_p = 0     # 移動先のＹ座標
        x_p = 0     # 移動先のＸ座標
        
        # それぞれの職人の座標を調べ、座標・行動・職人名を1つのリストにする
        for w in range(len(act)):
            switch= 0
            y,x = self.zahyo[me[w]]
            do.append([x,y,act[me[w]],me[w]])

        # 行動の並び変え
        for i in rank:
            I = 0
            try:
                for j in do:
                    if i in j[2]:
                        do[J],do[I] = do[I],do[J]
                        J += 1
                        break
                    I += 1
            except:
                pass
        # 移動する職人のみの移動先の座標を入手する [1]
        for w in do:

            if "s" in w[2]:
                act = w[2]
                y_p = w[1]
                x_p = w[0]

                if 'u' in act:
                    y_p -= 1

                elif 'd' in act:
                    y_p += 1

                if 'l' in act:
                    x_p -= 1 

                elif 'r' in act:
                    x_p += 1

                no.append([x_p,y_p,w[3]])

        # 移動先がかぶらないように移動先の座標を取得する
        for w in do:

            if 's' in w[2]:
                no.append([w[0],w[1],w[3]])

        for w in do:
            self.action(w,no,me)
        self.jinti()

        # 盤面出力(テスト用)
        # self.out()
        return

    # 陣地を見つける関数
    def jinti(self):
        wall = 'w'
        c = 0
        self.regions_cont = [0,0]
        self.old_regions = copy.deepcopy(self.now_regions)
        wall_ = []

        # 陣地の判別をする
        for w in range(2):
            regions = [['.'] * self.width for _ in range(self.height)]
            self.now_regions[c].clear()

            for i in range(len(self.board)):

                for j in range(len(self.board[0])):
                    
                    # 城壁と空き地のみの盤面を送る
                    if wall in self.board[i][j]:
                        regions[i][j] ='w'
                        wall_.append(str(j)+"/"+str(i))

                    else:
                        regions[i][j] = '@'

            kari = zone.search_zones(regions)

            # 陣地の数を数える
            for i in kari:

                for j in i:
                    self.now_regions[c].append(j)
                    self.regions_cont[c] += 1

            for i in self.old_regions[c]:

                if i in self.now_regions[c]:
                    pass        

                else:
                    self.not_regions[c].append(i)
            
            c += 1
            wall = "W"
        c = 0

        # 解放された陣地の上書きを行う(解放された陣地の上に城壁がある)
        for k in self.not_regions:
            delete = []

            for w in k:

                for i in self.now_regions:

                    if w in i or w in wall_:
                        delete.append(w)
                        break

                else:
                    self.regions_cont[c] += 1

            for w in delete:
                self.not_regions[c].remove(w)
            c+= 1
        

        self.shiro_count = [0,0]

        for j in range(2):

            for i in self.siro_point:

                if i in self.now_regions[j] or i in self.not_regions[j]:
                    self.shiro_count[j] += 1
        return


    # 行動を実行し、それを盤面に反映する関数
    def action(self,do,no,me):
        switch = 0  # for 文から抜け出すためのスイッチ
        switch2 = 0 # for 文から抜け出すためのスイッチ
        string = '' # 移動や破壊を行った場合に使う
        x = copy.copy(do[0])   # 現在のＹ座標
        y = copy.copy(do[1])   # 現在のＸ座標
        act = do[2] # 行動内容
        name = do[3]   # 職人の名前
        y_p = copy.deepcopy(y)     # 行動先のＹ座標
        x_p = copy.deepcopy(x)     # 行動先のＸ座標

        if self.turn_now % 2  == 0:
            wall = "W"

        else:
            wall = "w"

        if 'u' in act:
            y_p -= 1

        elif 'd' in act:
            y_p += 1

        if 'l' in act:
            x_p -= 1 

        elif 'r' in act:
            x_p += 1 

        if((x_p >= 0 and x_p  < self.height) and ( y_p >= 0 and y_p  < self.width) ) == 0:
            # print("out of renge")
            return

        # 待機
        if act == "stay":
            return
            
        # 壁破壊
        elif 'b' in act:

            for i in self.board[y_p][x_p]:

                if i == 'W' or i == 'w':
                    switch2 = 1

                else:
                    string +=  i

            if string ==  '':
                string += '.'

            if switch2 == 1:
                self.board[y_p][x_p] = string

        # 壁設置
        elif 'w' in act:
            q  = me

            for i in self.board[y_p][x_p]:

                if i in 'Ww':
                    return

                elif i in q or i == '.' or '@' in i:
                    switch2 = 1
                    self.board[y_p][x_p] = wall

                if switch2 == 1 and i != '.':
                    self.board[y_p][x_p]+= i

        # 移動
        elif 's' in act:

            # [1]のリストを使い、移動先がかぶった場合互いに移動しないようにする
            for p in no:

                if name != p[2] and x_p == p[0] and y_p == p[1]:
                    switch = 1
                    break

            if switch != 0:
                return
            
            # 自分の壁・空き地にのみ移動する
            p = self.board[y_p][x_p]

            if  (p == "." or  p == wall or p == '+') and switch2 == 0 and len(p) == 1:
                switch2 = 1
                for  j in self.board[y][x]:
                    if j != name:
                        string += j
                self.board[y_p][x_p] = name

                a = 0
                for w in self.zahyo:
                    if name in w:
                        self.zahyo[name] = [y_p,x_p]
                    a +=1                        

                

                # 移動元の処理
                if string == '':
                    string = '.'
                self.board[y][x] = string

            if switch2 == 1 and p != '.':
                self.board[y_p][x_p]+= p
        return

