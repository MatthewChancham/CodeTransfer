import tkinter as tk
import random

# --- CONFIG ---
BOARD_SIZE = 500
CELL = 20
GRID_COLOR_1 = "#3a3a3a"
GRID_COLOR_2 = "#2e2e2e"
SNAKE_COLOR = "#00ff00"
HEAD_COLOR = "#55ff55"
FOOD_COLOR = "#ff4444"
SPEED = 120  # ms per frame


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Google‑Style Snake")

        self.canvas = tk.Canvas(root, width=BOARD_SIZE, height=BOARD_SIZE, bg="black")
        self.canvas.pack()

        self.best_score = 0
        self.state = "home"  # home, game, dead

        self.root.bind("<KeyPress>", self.key_press)

        self.draw_home()

    # ---------------- HOME SCREEN ----------------
    def draw_home(self):
        self.canvas.delete("all")
        self.draw_grid()

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 - 40,
            text="SNAKE",
            fill="white",
            font=("Arial", 40, "bold")
        )

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 + 10,
            text="Press SPACE to start",
            fill="white",
            font=("Arial", 18)
        )

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 + 60,
            text=f"Best Score: {self.best_score}",
            fill="white",
            font=("Arial", 16)
        )

    # ---------------- GRID BACKGROUND ----------------
    def draw_grid(self):
        for x in range(0, BOARD_SIZE, CELL):
            for y in range(0, BOARD_SIZE, CELL):
                color = GRID_COLOR_1 if (x//CELL + y//CELL) % 2 == 0 else GRID_COLOR_2
                self.canvas.create_rectangle(x, y, x+CELL, y+CELL, fill=color, outline=color)

    # ---------------- GAME SETUP ----------------
    def start_game(self):
        self.state = "game"
        self.canvas.delete("all")
        self.draw_grid()

        self.direction = "Right"
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.spawn_food()
        self.score = 0

        self.score_text = self.canvas.create_text(
            10, 10, anchor="nw", fill="white", font=("Arial", 16),
            text=f"Score: {self.score}"
        )

        self.update()

    # ---------------- INPUT ----------------
    def key_press(self, event):
        key = event.keysym

        if self.state == "home" and key == "space":
            self.start_game()
            return

        if self.state == "dead" and key == "space":
            self.draw_home()
            self.state = "home"
            return

        if self.state != "game":
            return

        if key in ("Up", "Down", "Left", "Right"):
            opposite = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
            if opposite[key] != self.direction:
                self.direction = key

    # ---------------- FOOD ----------------
    def spawn_food(self):
        while True:
            fx = random.randint(0, BOARD_SIZE // CELL - 1)
            fy = random.randint(0, BOARD_SIZE // CELL - 1)
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    # ---------------- GAME LOOP ----------------
    def update(self):
        if self.state != "game":
            return

        self.move_snake()
        self.draw()

        self.root.after(SPEED, self.update)

    # ---------------- SNAKE MOVEMENT ----------------
    def move_snake(self):
        head_x, head_y = self.snake[0]

        if self.direction == "Up":
            head_y -= 1
        elif self.direction == "Down":
            head_y += 1
        elif self.direction == "Left":
            head_x -= 1
        elif self.direction == "Right":
            head_x += 1

        # WALL COLLISION → GAME OVER
        if head_x < 0 or head_x >= BOARD_SIZE // CELL or head_y < 0 or head_y >= BOARD_SIZE // CELL:
            self.game_over()
            return

        new_head = (head_x, head_y)

        # SELF COLLISION
        if new_head in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        # FOOD
        if new_head == self.food:
            self.score += 1
            self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
            self.spawn_food()
        else:
            self.snake.pop()

    # ---------------- DRAWING ----------------
    def draw(self):
        self.canvas.delete("snake")
        self.canvas.delete("food")

        # Draw snake
        for i, (x, y) in enumerate(self.snake):
            x1, y1 = x * CELL, y * CELL
            x2, y2 = x1 + CELL, y1 + CELL
            color = HEAD_COLOR if i == 0 else SNAKE_COLOR
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tag="snake")

        # Draw food
        fx, fy = self.food
        x1, y1 = fx * CELL, fy * CELL
        x2, y2 = x1 + CELL, y1 + CELL
        self.canvas.create_oval(x1, y1, x2, y2, fill=FOOD_COLOR, outline="", tag="food")

    # ---------------- GAME OVER ----------------
    def game_over(self):
        self.state = "dead"
        self.best_score = max(self.best_score, self.score)

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 - 20,
            text="GAME OVER",
            fill="white",
            font=("Arial", 32, "bold")
        )

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 + 20,
            text=f"Score: {self.score}   Best: {self.best_score}",
            fill="white",
            font=("Arial", 18)
        )

        self.canvas.create_text(
            BOARD_SIZE // 2, BOARD_SIZE // 2 + 60,
            text="Press SPACE to return to Home",
            fill="white",
            font=("Arial", 16)
        )


# ---------------- RUN ----------------
root = tk.Tk()
SnakeGame(root)
root.mainloop()
