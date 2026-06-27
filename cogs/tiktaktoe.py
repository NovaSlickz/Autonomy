import discord
from discord.ext import commands

# 1. The Button Class (Handles individual square clicks)
class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view
        
        if view.board[self.y][self.x] != 0:
            return

        if view.player_x is None:
            view.player_x = interaction.user
        elif view.player_o is None and interaction.user != view.player_x:
            view.player_o = interaction.user

        if view.current_player == view.X and interaction.user != view.player_x:
            await interaction.response.send_message("It's not your turn! ❌ is playing.", ephemeral=True)
            return
        elif view.current_player == view.O and view.player_o is not None and interaction.user != view.player_o:
            await interaction.response.send_message("It's not your turn! ⭕ is playing.", ephemeral=True)
            return
        elif view.current_player == view.O and view.player_o is None and interaction.user == view.player_x:
            await interaction.response.send_message("You need someone else to click and challenge you!", ephemeral=True)
            return

        if view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = 'X'
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"❌ **{view.player_x.display_name}** made a move! Next up: ⭕ **{view.player_o.display_name if view.player_o else 'Challenger'}**"
        else:
            self.style = discord.ButtonStyle.success
            self.label = 'O'
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"⭕ **{view.player_o.display_name}** made a move! Next up: ❌ **{view.player_x.display_name}**"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f"🎉 ❌ **{view.player_x.display_name}** wins the game!"
            elif winner == view.O:
                content = f"🎉 ⭕ **{view.player_o.display_name}** wins the game!"
            else:
                content = "🤝 It's a tie game!"

            for child in view.children:
                child.disabled = True
            view.stop()

        await interaction.response.edit_message(content=content, view=view)


# 2. The View Class (Creates the 3x3 grid layout)
class TicTacToeView(discord.ui.View):
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player_x: discord.User):
        super().__init__(timeout=180)
        self.player_x = player_x
        self.player_o = None
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        for across in self.board:
            if abs(sum(across)) == 3:
                return self.O if sum(across) == 3 else self.X
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if abs(value) == 3:
                return self.O if value == 3 else self.X
        diag1 = self.board[0][0] + self.board[1][1] + self.board[2][2]
        diag2 = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if abs(diag1) == 3:
            return self.O if diag1 == 3 else self.X
        if abs(diag2) == 3:
            return self.O if diag2 == 3 else self.X
        if all(i != 0 for row in self.board for i in row):
            return self.Tie
        return None


# 3. The Cog Class (Where your hybrid command lives)
class TicTacToe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Notice we use @commands.hybrid_command instead of @bot.hybrid_command inside a cog
    @commands.hybrid_command(name="game", description="Starts a modern game of Tic-Tac-Toe!")
    async def game(self, ctx: commands.Context):
        view = TicTacToeView(player_x=ctx.author)
        await ctx.send(f"🎮 **{ctx.author.display_name}** started a match! Click any square to challenge them as ⭕!", view=view)


# 4. The Setup Function (Tells discord.py how to load this file)
async def setup(bot: commands.Bot):
    await bot.add_cog(TicTacToe(bot))
