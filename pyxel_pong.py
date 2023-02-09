import pyxel


# Keeps track of position, score and controls for each player
# Also displays and moves the player
class Player:
    def __init__(self, x, y, score, keys, p_id):
        self.x = x
        self.y = y
        self.score = score
        self.key_up = keys[0]
        self.key_dn = keys[1]
        self.player_id = p_id

    # Draw the player, player_id is used to select the correct texture
    def draw(self):
        # pyxel.rect(self.x, self.y, 4, 32, 7)
        # pyxel.rect(self.x + 1, self.y + 1, 2, 30, self.player_id)
        pyxel.blt(self.x, self.y, 0, 4 * self.player_id, 0, 4, 16, 0)
        pyxel.blt(self.x, self.y + 16, 0, 4 * self.player_id, 0, 4, -16, 0)

    # Move the player up/down if he isn't already at the border
    def move(self):
        if pyxel.btnp(self.key_up, 1, 1):
            if self.y > 8:
                self.y -= 1.4
        if pyxel.btnp(self.key_dn, 1, 1):
            if self.y < 145:
                self.y += 1.4


# AI Player checks the ball position and tries to move to it
# Adjusted ability to move and see the ball so it can lose
class PlayerAI:
    def __init__(self, x, y, score, p_id, ball):
        self.x = x
        self.y = y
        self.score = score
        self.player_id = p_id
        self.ball = ball

    def draw(self):
        pyxel.blt(self.x, self.y, 0, 4 * self.player_id, 0, 4, 16, 0)
        pyxel.blt(self.x, self.y + 16, 0, 4 * self.player_id, 0, 4, -16, 0)

    def move(self):
        percieved_y = self.ball.y + pyxel.rndi(-10, 10)
        # print(f"AI sees ball at {self.ball.x}, {percieved_y}")
        if abs(self.x - self.ball.x) > abs(self.x - (self.ball.x + self.ball.v_x)):
            self.towards = True
        else:
            self.towards = False
        if self.towards:
            if percieved_y < self.y + 16:
                if self.y > 8:
                    self.y -= 1.85
            if percieved_y > self.y + 16:
                if self.y < 145:
                    self.y += 1.85


# Keeps track of position and speed of the ball
# Also updates the positions and draws the ball
class Ball:
    def __init__(self, x, y, v_x, v_y):
        self.x = x
        self.y = y
        self.v_x = v_x
        self.v_y = v_y

    def draw(self):
        # pyxel.circ(self.x, self.y, 2, 9)
        pyxel.blt(self.x - 2, self.y - 2, 0, 8, 0, 5, 5, 0)

    def move(self):
        self.x += self.v_x
        self.y += self.v_y


# Draws the playfield, displays the score and checks ball collisions with walls/players
class Director:
    def __init__(self, player1, player2, ball):
        self.p1 = player1
        self.p2 = player2
        self.ball = ball

    # If wall behind a player is hit, the other player gains a point
    # Flash the playfield with the other players's color as well
    def collision_check(self):
        if 4 >= self.ball.x:
            self.ball.v_x *= -1
            self.p2.score += 1
            pyxel.rectb(1, 7, 318, 172, 8)
            pyxel.play(0, 0)
        if 315 <= self.ball.x:
            self.ball.v_x *= -1
            self.p1.score += 1
            pyxel.rectb(1, 7, 318, 172, 3)
            pyxel.play(0, 0)
        if not (11 <= self.ball.y <= 174):
            self.ball.v_y *= -1

    # Reverse ball direction if the player is hit and the ball is moving from infront of the player
    # The second part makes sure the ball won't get stuck behind the player
    def player_check(self):
        if 8 >= self.ball.x and self.ball.v_x < 0:
            if self.p1.y < self.ball.y < self.p1.y + 32:
                self.ball.v_x *= -1
                pyxel.play(0, 1)
        if 311 <= self.ball.x and self.ball.v_x > 0:
            if self.p2.y < self.ball.y < self.p2.y + 32:
                self.ball.v_x *= -1
                pyxel.play(0, 1)

    def draw_field(self):
        pyxel.rectb(1, 7, 318, 172, 13)
        for i in range(1, 8):
            pyxel.line(160, i * 25 - 15, 160, i * 25, 13)

    def draw_scores(self):
        pyxel.text(151, 1, f"{self.p1.score} : {self.p2.score}", 10)

    def show_win(self, player):
        self.ball.v_x = 0
        self.ball.v_y = 0
        self.winmes = f"{player.upper()} IS THE WINNER!"
        print(self.winmes)
        pyxel.rect(40, 20, 240, 30, 1)
        pyxel.text(
            120,
            25,
            self.winmes,
            8 + int((pyxel.frame_count / 100)) % 8,
        )
        pyxel.text(112, 40, "Press 'R' to reset the game", 13)


class App:
    def __init__(self):
        pyxel.init(320, 180, "PONG", fps=60)
        pyxel.load(r"pong_assets.pyxres")
        self.ball = Ball(160, 90, 2, 2)
        self.player1 = Player(2, 80, 0, [pyxel.KEY_UP, pyxel.KEY_DOWN], 0)
        # self.player2 = Player(314, 80, 0, [pyxel.KEY_W, pyxel.KEY_S], 1)
        # self.player1 = PlayerAI(2, 80, 0, 0, self.ball)
        self.player2 = PlayerAI(314, 80, 0, 1, self.ball)
        self.director = Director(self.player1, self.player2, self.ball)
        self.winner = None
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_R):
            self.player1.score = 0
            self.player2.score = 0
            self.winner = None
            self.ball.x = 160
            self.ball.y = 90
            self.ball.v_x = 2
            self.ball.v_y = 2
        if self.player1.score == 5:
            self.winner = "Player 1"
        if self.player2.score == 5:
            self.winner = "Player 2"
        if pyxel.btnp(pyxel.KEY_T):
            self.winner = "TEST P0"
        print(
            f"\nFrame: {pyxel.frame_count}\nPlayer 1: {round(self.player1.y, 1):>5} ({self.player1.score})\nPlayer 2: {round(self.player2.y, 1):>5} ({self.player2.score})\nBall: {self.ball.x}, {self.ball.y}"
        )

    def draw(self):
        pyxel.cls(0)
        self.director.draw_field()
        self.director.draw_scores()
        self.director.collision_check()
        self.director.player_check()
        self.player1.move()
        self.player1.draw()
        self.player2.move()
        self.player2.draw()
        self.ball.move()
        self.ball.draw()
        if self.winner:
            self.director.show_win(self.winner)


App()
