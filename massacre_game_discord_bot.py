# option = input("T or P?: ")
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
import random
import copy
from dotenv import load_dotenv
import os

load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")
discord_streaming_url = os.getenv("DISCORD_STREAMING_URL")
discord_owner_id = os.getenv("DISCORD_OWNER_ID")

if not discord_token or not discord_owner_id:
    raise RuntimeError("DISCORD_TOKEN and DISCORD_OWNER_ID environment variables are required.")

try:
    discord_owner_id = int(discord_owner_id)
except ValueError as error:
    raise RuntimeError("DISCORD_OWNER_ID must be a numeric Discord user ID.") from error

print("Started")
# Sets all the bots information
bot = commands.Bot(command_prefix="!", case_insensitive=True, description='A Buushy Product', owner_id=discord_owner_id, activity=discord.Streaming(name="PrivateBot", url=discord_streaming_url))
# Removes the default help command
bot.remove_command("help")


# All the default variables
def DefaultEverything(Parameter=None):
    bot.GameAvailable = False  # Wether a game is available or not
    bot.GameState = None  # The current state that the game is in
    if Parameter != "Cancel":
        bot.Cancel = False  # Wether someone cancelled or not
    bot.Left = None  # The player that left the game
    bot.Winner = None  # The winner of the game
    bot.Deck = None  # All the cards in the deck
    bot.Turn = None  # Who's turn it is
    bot.TopCard = "None"  # The card that is at the top of the pile
    bot.LastCard = "None"  #  The last card on the pile that is not a Jack/Joker
    bot.Cards = []  # All the cards in the pile
    bot.CardSameNum = 0  # How many of the card is the same card
    bot.Invites = {}  # All invites that are sent with !game invite
    if Parameter != "PlayerInfo":
        # All the players information
        bot.PlayerInfo = {"P1": {"Player": None, "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}},
                          "P2": {"Player": None, "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}}}
DefaultEverything()  # Makes all the default variables exist
# Changes how messages are displayed
bot.MessageOutput = "Replace"   # Edit, Replace, Edit+Replace
bot.GameRestart = False  # Allows old games to be played
if bot.GameRestart:
    # Sets both players cards, Player turn and how many cards are in the deck
    bot.PlayerInfo["P1"]["Cards"] = None
    bot.PlayerInfo["P2"]["Cards"] = None
    bot.RiggedTurn = "P1"
    bot.RiggedDeck = None


# Different colours for discord embeds
def Colour(colour):
    if colour == "Purple":
        return 0x6a0dad
    elif colour == "Red":
        return 0xFF0000
    elif colour == "Gold":
        return 0xFFD700
    elif colour == "Gray":
        return 0x808080


# Deletes bot message and host message
async def MSGDel(msg, cmd):
    await asyncio.sleep(7)  # Waits 7 seconds
    await msg.delete()  # Deletes bot message
    try:  # Tries to delete host message
        await cmd.message.delete()
    except:
        pass


# Determines which player the command author is
def WhichPlayer(Player):
    if Player == bot.PlayerInfo["P1"]["Player"]:
        Player = "P1"
    elif Player == bot.PlayerInfo["P2"]["Player"]:
        Player = "P2"
    else:  # If the command author not a player, it will return None
        Player = None
    return Player


# Creates the deck with each card
def CreateDeck():
    bot.Deck = ["J1", "J2"]  # Puts joker cards in the deck
    for cardNum in range(13):  # Loops 13 times to apply card numbers 2-14
        for Type in ["H", "C", "D", "S"]:  # Goes through each type when making a card
            bot.Deck.append(f"{Type}{cardNum + 2}")  # Puts the card into the deck


# Gets deck, Picks a card and removes it from deck
def RandomCard(Rigged=None):
    if Rigged is None:
        Card = random.choice(bot.Deck)  # Randomly selects a Card from the deck
    else:  # If the game is rigged
        Card = Rigged  # Make the entered card into the Card variable
    bot.Deck.remove(Card)  # Removes the rigged card from the deck
    return Card  # Returns the Card


#
def SortCardsInHand(Player):
    CardsInOrder = {}
    for Number in range(15):
        CardsInOrder[str(Number+2)] = []
    for Card in bot.PlayerInfo[Player]["Cards"]["Hand"]:
        if Card[0] == "J":
            if Card[1:] == "1":
                CardsInOrder["15"].append(Card)
            elif Card[1:] == "2":
                CardsInOrder["16"].append(Card)
        else:
            CardsInOrder[Card[1:]].append(Card)
    SortedDeck = []
    for Number in CardsInOrder:
        if CardsInOrder[Number]:
            SortedDeck += CardsInOrder[Number]
    bot.PlayerInfo[Player]["Cards"]["Hand"] = SortedDeck


def StarterCards():
    # Hidden Cards
    if bot.GameRestart:
        for category in ["Hand", "Shown", "Hidden"]:
            for Player in ["P1", "P2"]:
                if category == "Hidden":
                    Cards = bot.PlayerInfo[Player]["Cards"]["Hidden"]["Cards"]
                else:
                    Cards = bot.PlayerInfo[Player]["Cards"][category]
                for card in copy.deepcopy(Cards):
                    Cards.append(RandomCard(card))
        bot.Deck = bot.RiggedDeck
    else:
        for Player in ["P1", "P2"]:
            Cards = bot.PlayerInfo[Player]["Cards"]
            for _ in range(3):
                Cards["Hidden"]["Cards"].append(RandomCard())
                Cards["Shown"].append(RandomCard())
                Cards["Hand"].append(RandomCard())
    SortCardsInHand("P1")
    SortCardsInHand("P2")


async def DisplayCards(CommandSender):
    def SendToPlayer(Player, Opponent):
        def Formatter(Cards):
            if type(Cards) == str:
                Cards = [Cards]
            TypesToEmojis = {"H": ":heart:", "D": ":diamonds:", "S": ":spoon:", "C": ":four_leaf_clover:",
                             "J": ":clown:"}
            ValuesToLetters = {"11": "J", "12": "Q", "13": "K", "14": "A"}
            BoldAllValues = "2,3,4,5,6,7,8,9,10,J,Q,K,A".split(",")
            CardString = ""
            for Card in Cards:
                for Type in TypesToEmojis:
                    Card = Card.replace(Type, TypesToEmojis[Type])
                for Value in ValuesToLetters:
                    Card = Card.replace(Value, ValuesToLetters[Value])
                for Value in BoldAllValues:
                    Card = Card.replace(Value, f"**{Value}**")
                if Card.startswith(":clown:"):
                    Card = Card.replace("1", "**1**")
                CardString += f"{Card} / "
            if not Cards:
                return "\u200B"
            else:
                return CardString[:-3]
        def EAF(embed, name, value, inline=True):
            embed.add_field(name=name, value=value, inline=inline)
        PData = bot.PlayerInfo[Player]
        OData = bot.PlayerInfo[Opponent]
        PCards = PData['Cards']
        OCards = OData['Cards']
        if bot.GameState != "Results" and bot.Left is None:
            PlayerHidden, OpponentHidden = [], []
            PDexHidden = PCards["Hidden"]
            ODexHidden = OCards["Hidden"]
            for Card in PDexHidden["Cards"]:
                if PDexHidden["IsShown"][PDexHidden["Cards"].index(Card)]:
                    PlayerHidden.append(Card)
                else:
                    PlayerHidden.append(":grey_question:")
            for Card in ODexHidden["Cards"]:
                if ODexHidden["IsShown"][ODexHidden["Cards"].index(Card)]:
                    OpponentHidden.append(Card)
                else:
                    OpponentHidden.append(":grey_question:")
            if bot.GameState == "Intermission":
                Title = "Intermission"
            elif bot.GameState == "Gameplay":
                if Player == bot.Turn:
                    Title = "Your Turn"
                elif Opponent == bot.Turn:
                    Title = "Opponent's Turn"
            elif bot.GameState == "Game Over":
                Title = "Game Over"
            else:
                Title = "None"
            if bot.CardSameNum == 4:
                description = f"NO CARD (Burnt by 4x {Formatter(bot.LastCard[1:])} Cards)"
            elif bot.LastCard[1:] == "10":
                description = f"NO CARD (Burnt by 10 Card)"
            elif bot.TopCard == "None":
                description = f"NO CARD"
            else:
                if len(bot.Cards) == 1:
                    description = f"{Formatter(bot.TopCard)} (1 Card)"
                else:
                    if bot.CardSameNum >= 2:
                        ShowMultiplier = f" ({bot.CardSameNum}x)"
                    else:
                        ShowMultiplier = ""
                    if bot.TopCard[1:] == "11" or bot.TopCard[0] == "J":
                        description = f"{Formatter(bot.TopCard)} ({Formatter(bot.LastCard)}{ShowMultiplier}) ({len(bot.Cards)} Cards)"
                    else:
                        description = f"{Formatter(bot.TopCard)}{ShowMultiplier} ({len(bot.Cards)} Cards)"
            embed = discord.Embed(title=Title, description=description, color=Colour("Purple"))
            EAF(embed, f"Your Hand ({len(PCards['Hand'])} Cards)", Formatter(PCards["Hand"]))
            EAF(embed, "\u200B", "\u200B") # Blank
            EAF(embed, "Opponent's Hand", f"{len(OCards['Hand'])} Cards")
            EAF(embed, "Top Cards", Formatter(PCards["Shown"]))
            EAF(embed, "\u200B", "\u200B")  # Blank
            EAF(embed, "Opponent's Top Cards", Formatter(OCards["Shown"]))
            EAF(embed, "Hidden Cards", Formatter(PlayerHidden))
            EAF(embed, "\u200B", "\u200B")  # Blank
            EAF(embed, "Opponent's Hidden Cards", Formatter(OpponentHidden))
            TypeConversions = ":heart:=**H**, :diamonds:=**D**, :spoon:=**S**, :four_leaf_clover:=**C**, :clown:=**J**"
            EAF(embed, "\u200B", f"{TypeConversions}", False)
            CardsInDeck = f"{len(bot.Deck)} cards in the deck"
            if bot.GameState == "Intermission":
                if not PData["Ready"] and not OData["Ready"]:
                    embed.set_footer(text=f"{CardsInDeck}\nType `!mready` when ready to continue")
                elif PData["Ready"] and OData["Ready"]:
                    embed.set_footer(text=f"{CardsInDeck}\nReady! (2/2)")
                elif PData["Ready"]:
                    embed.set_footer(text=f"{CardsInDeck}\nReady! (1/2)")
                elif OData["Ready"]:
                    embed.set_footer(text=f"{CardsInDeck}\nType `!mready` when ready to continue (1/2)")
            elif bot.GameState == "Game Over":
                embed.set_footer(text=f"Game Over")
            else:
                embed.set_footer(text=f"{CardsInDeck}")
        else:
            if bot.Left == "P1":
                bot.Winner = bot.PlayerInfo["P2"]["Player"]
            elif bot.Left == "P2":
                bot.Winner = bot.PlayerInfo["P1"]["Player"]
            if bot.Winner == PData["Player"]:
                if bot.Left is None:
                    embed = discord.Embed(title="Game Over", description=f"You have won!", color=Colour("Gold"))
                else:
                    embed = discord.Embed(title="Game Over", description=f"You have won! (Opponent Left)", color=Colour("Gold"))
            else:
                if bot.Left is None:
                    embed = discord.Embed(title="Game Over", description=f"{bot.Winner.mention} has won!", color=Colour("Gold"))
                else:
                    embed = discord.Embed(title="Game Over", description=f"{bot.Winner.mention} has won! (You left)", color=Colour("Gold"))
            embed.set_thumbnail(url=bot.Winner.avatar_url)
            EAF(embed, "Your Hidden", Formatter(PCards["Hidden"]["Cards"]))
            EAF(embed, "Their Hidden", Formatter(OCards["Hidden"]["Cards"]))
            if bot.Left is None:
                if bot.Cancel:
                    embed.set_footer(text="Canceled")
                elif not PData["Ready"] and not OData["Ready"]:
                    embed.set_footer(text="Type `!mready` to play again or `!mcancel` to stop playing")
                elif PData["Ready"] and OData["Ready"]:
                    embed.set_footer(text=f"Ready! (2/2)")
                elif PData["Ready"]:
                    embed.set_footer(text=f"Ready! (1/2)")
                elif OData["Ready"]:
                    embed.set_footer(text="Type `!mready` to play again or `!mcancel` to stop playing (1/2)")
        return embed
    P1Data, P2Data = bot.PlayerInfo["P1"], bot.PlayerInfo["P2"]
    if not P1Data["MSG"]:
        bot.PlayerInfo["P1"]["MSG"].append(await P1Data["Player"].send(embed=SendToPlayer("P1", "P2")))
        bot.PlayerInfo["P2"]["MSG"].append(await P2Data["Player"].send(embed=SendToPlayer("P2", "P1")))
    else:
        P1MSG, P2MSG = P1Data["MSG"][-1], P2Data["MSG"][-1]
        async def msg_delete(msg, player=None):
            # if player is None:
            #     forplayer = ""
            # else:
            #     forplayer = f" For Player {player}"
            # print(msg)
            # for themsg in msg:
            #     print(themsg)
            for themsg in copy.copy(msg[:-1]):
                # try:
                # await themsg.edit(embed=discord.Embed(title="DELETED", description=f"DELETED", color=Colour("Gold")))
                # await asyncio.sleep(1)
                try:
                    # print(themsg.content)
                    # print(themsg.embeds[0].fields[0])
                    # print(themsg.embeds[0].footer)
                    await themsg.delete()
                except:
                    pass
                msg.remove(themsg)
                    # try:
                    #     await themsg.edit(
                    #         embed=discord.Embed(title="DELETED", description=f"DELETED", color=Colour("Gold")))
                    #     print("couldn't delete")
                    # except:
                    #     print("couldn't edit or delete")
                # print(f"Msg deleted{forplayer}")
                # except Exception as e:
                #     print(e)
                #     print(f"First Delete Not Work{forplayer}")
                #     for i in range(5):
                #         await asyncio.sleep(1)
                #         try:
                #             await themsg.delete()
                #         except:
                #             print(f"{i+1}) Delete Not Work{player}")
                #     print(themsg)


        if bot.MessageOutput == "Edit":
            await P1MSG.edit(embed=SendToPlayer("P1", "P2"))
            await P2MSG.edit(embed=SendToPlayer("P2", "P1"))
        elif bot.MessageOutput == "Edit+Replace":
            if CommandSender == "Both":
                await P1MSG.edit(embed=SendToPlayer("P1", "P2"))
                await P2MSG.edit(embed=SendToPlayer("P2", "P1"))
            elif CommandSender == P1Data["Player"]:
                NewP1MSG = await P1Data["Player"].send(embed=SendToPlayer("P1", "P2"))
                await P1MSG.delete()
                P1Data["MSG"] = NewP1MSG
                await P2MSG.edit(embed=SendToPlayer("P2", "P1"))
            elif CommandSender == P2Data["Player"]:
                await P1MSG.edit(embed=SendToPlayer("P1", "P2"))
                NewP2MSG = await P2Data["Player"].send(embed=SendToPlayer("P2", "P1"))
                await P2MSG.delete()
                P2Data["MSG"] = NewP2MSG
        elif bot.MessageOutput == "Replace":
            P1Data["MSG"].append(await P1Data["Player"].send(embed=SendToPlayer("P1", "P2")))
            P2Data["MSG"].append(await P2Data["Player"].send(embed=SendToPlayer("P2", "P1")))
            await msg_delete(P1Data["MSG"], "1")
            await msg_delete(P2Data["MSG"], "2")
            # P1Data["MSG"], P2Data["MSG"] = NewP1MSG, NewP2MSG


async def Intermission():
    bot.GameState = "Intermission"
    await DisplayCards("Both")
    while True:
        if bot.PlayerInfo["P1"]["Ready"] and bot.PlayerInfo["P2"]["Ready"]:
            break
        else:
            await asyncio.sleep(1)
    bot.PlayerInfo["P1"]["Ready"], bot.PlayerInfo["P2"]["Ready"] = False, False
    bot.GameState = "Gameplay"
    SortCardsInHand("P1")
    SortCardsInHand("P2")


async def WhoStarts():
    BothPlayersLowestCard = {"P1": {"Value": 100, "Type": None}, "P2": {"Value": 100, "Type": None}}
    for Player in ["P1", "P2"]:
        for Card in bot.PlayerInfo[Player]["Cards"]["Hand"]:
            if Card[0] != "J":
                if int(Card[1:]) < BothPlayersLowestCard[Player]["Value"]:
                    BothPlayersLowestCard[Player]["Value"] = int(Card[1:])
                    BothPlayersLowestCard[Player]["Type"] = Card[0]
                elif int(Card[1:]) == BothPlayersLowestCard[Player]["Value"]:
                    CardTypeNum = {"H": 1, "C": 2, "D": 3, "S": 4}
                    if CardTypeNum[Card[0]] < CardTypeNum[BothPlayersLowestCard[Player]["Type"]]:
                        BothPlayersLowestCard[Player]["Type"] = Card[0]
    if BothPlayersLowestCard["P1"]["Value"] < BothPlayersLowestCard["P2"]["Value"]:
        bot.Turn = "P1"
    elif BothPlayersLowestCard["P2"]["Value"] < BothPlayersLowestCard["P1"]["Value"]:
        bot.Turn = "P2"
    elif BothPlayersLowestCard["P1"]["Value"] == BothPlayersLowestCard["P2"]["Value"]:
        CardTypeNum = {"H": 1, "C": 2, "D": 3, "S": 4}
        if CardTypeNum[BothPlayersLowestCard["P1"]["Type"]] < CardTypeNum[BothPlayersLowestCard["P2"]["Type"]]:
            bot.Turn = "P1"
        elif CardTypeNum[BothPlayersLowestCard["P2"]["Type"]] < CardTypeNum[BothPlayersLowestCard["P1"]["Type"]]:
            bot.Turn = "P2"
    await asyncio.sleep(1)
    await DisplayCards("Both")


async def MainGame():
    bot.Invites = {}
    CreateDeck()
    StarterCards()
    if not bot.GameRestart:
        await Intermission()
        await WhoStarts()
    elif bot.GameRestart:
        bot.GameState = "Gameplay"
        bot.Turn = bot.RiggedTurn
        await DisplayCards("Both")


async def GameOver():
    bot.GameState = "Game Over"
    await DisplayCards("Both")
    await asyncio.sleep(10)
    bot.GameState = "Results"
    await DisplayCards("Both")
    while True:
        if bot.PlayerInfo["P1"]["Ready"] and bot.PlayerInfo["P2"]["Ready"]:
            bot.PlayerInfo = {"P1": {"Player": bot.PlayerInfo["P1"]["Player"], "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}},
                              "P2": {"Player": bot.PlayerInfo["P2"]["Player"], "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}}}
            DefaultEverything("PlayerInfo")
            break
        elif bot.Cancel:
            await DisplayCards("Both")
            bot.PlayerInfo = {"P1": {"Player": None, "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}},
                              "P2": {"Player": None, "Ready": False, "MSG": [], "Cards": {"Hidden": {"Cards": [], "IsShown": [False, False, False]}, "Shown": [], "Hand": []}}}
            DefaultEverything("Cancel")
            break
        else:
            await asyncio.sleep(1)
    if not bot.Cancel:
        await MainGame()
    else:
        bot.Cancel = False


@bot.command(aliases=["ms", "swap"])
async def MSwap(cmd, HandCard=None, ShownCard=None):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.GameState != "Intermission":
        message = await cmd.channel.send(embed=discord.Embed(title="Not Intermission",
                                                             description="You can only swap cards during intermission",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.PlayerInfo[Player]["Ready"]:
        message = await cmd.channel.send(embed=discord.Embed(title="Cant Swap When Ready",
                                                             description="You can not swap out cards when you are ready. Type `!mready` to swap cards",
                                                             color=Colour("Gray")))
        await MSGDel(message, cmd)
    elif HandCard is None or ShownCard is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Missing Command Requirements",
                                                             description="To swap cards type:\n`!ms (Card in hand) (Card 1-3 on top)`\n`!ms C5 S2`",
                                                             color=Colour("Gray")))
        await MSGDel(message, cmd)
    else:
        def ChangeValues(Card):
            Card = Card.upper()
            if Card[1:] == "J":
                Card = Card[0] + "11"
            elif Card[1:] == "Q":
                Card = Card[0] + "12"
            elif Card[1:] == "K":
                Card = Card[0] + "13"
            elif Card[1:] == "A":
                Card = Card[0] + "14"
            return Card
        HandCard = ChangeValues(HandCard)
        ShownCard = ChangeValues(ShownCard)
        PCards = bot.PlayerInfo[Player]["Cards"]
        # cards arn't in deck
        if HandCard not in PCards["Hand"]:
            message = await cmd.channel.send(embed=discord.Embed(title="Not In Hand",
                                                                 description="The card you entered is not in your hand",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif ShownCard not in PCards["Shown"]:
            message = await cmd.channel.send(embed=discord.Embed(title="Not On Top",
                                                                 description="The card you entered is not in your top cards",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        else:
            # get handcard
            ShownCardIndex = PCards["Shown"].index(ShownCard)
            HandCardIndex = PCards["Hand"].index(HandCard)
            PCards["Shown"][ShownCardIndex] = HandCard
            PCards["Hand"][HandCardIndex] = ShownCard
            await DisplayCards(cmd.author)


@bot.command(aliases=["mpu", "pickup"])
async def MPickUp(cmd, arg=None):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.GameState != "Gameplay":
        message = await cmd.channel.send(embed=discord.Embed(title="Cant pickup cards",
                                                             description="You can only pickup cards during gameplay",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif Player != bot.Turn:
        message = await cmd.channel.send(embed=discord.Embed(title="Not your Turn",
                                                             description="You can only play cards during your turn",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif len(bot.Cards) == 0:
        message = await cmd.channel.send(embed=discord.Embed(title="No cards on pile",
                                                             description="There are no cards in the pile to pickup",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif arg is not None:
        message = await cmd.channel.send(embed=discord.Embed(title="Can't Pickup With Arguments",
                                                             description="To pickup the cards in the pile, you have to only type `!mpu`",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    else:
        bot.PlayerInfo[Player]["Cards"]["Hand"] += bot.Cards
        SortCardsInHand(Player)
        bot.Cards = []
        bot.TopCard = "None"
        Players = ["P1", "P2"]
        Players.remove(Player)
        bot.Turn = Players[0]
        await DisplayCards(cmd.author)


@bot.command(aliases=["mr", "ready"])
async def MReady(cmd):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.GameState != "Intermission" and bot.GameState != "Results":
        message = await cmd.channel.send(embed=discord.Embed(title="Not Intermission",
                                                             description="You can not ready outside of intermissions",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    else:
        PData = bot.PlayerInfo[Player]
        if not PData["Ready"]:
            PData["Ready"] = True
        elif PData["Ready"]:
            PData["Ready"] = False
        await DisplayCards(cmd.author)


@bot.command(aliases=["mc", "cancel"])
async def MCancel(cmd):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.GameState != "Results":
        message = await cmd.channel.send(embed=discord.Embed(title="Game Not Finished",
                                                             description="Wait until the game has finished to cancel",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.PlayerInfo[Player]["Ready"]:
        message = await cmd.channel.send(embed=discord.Embed(title="Cant Cancel When Ready",
                                                             description="You can not cancel when you are ready. Type `!mready` to cancel",
                                                             color=Colour("Gray")))
        await MSGDel(message, cmd)
    else:
        bot.Cancel = True
        await DisplayCards(cmd.author)


@bot.command(aliases=["leave"])
async def MLeave(cmd):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif bot.GameState == "Results":
        message = await cmd.channel.send(embed=discord.Embed(title="Can't leave during results",
                                                             description="To stop playing use `!mcancel`",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    else:
        bot.Left = Player
        await DisplayCards(cmd.author)
        DefaultEverything()


@bot.command()
async def Ping(cmd):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    else:
        Players = ["P1", "P2"]
        Players.remove(Player)
        message = await bot.PlayerInfo[Players[0]]["Player"].send("ping")
        await message.delete()


@bot.command(aliases=["mp", "place"])
async def MPlace(cmd, Card=None):
    Player = WhichPlayer(cmd.author)
    if Player is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Not in Game",
                                                             description="You are not a player in the game",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif Card is None:
        message = await cmd.channel.send(embed=discord.Embed(title="Missing Command Requirements",
                                                             description="To play a card, type:\n`!mp (Card in hand)`\n`!mp D4`",
                                                             color=Colour("Gray")))
        await MSGDel(message, cmd)
    elif bot.GameState != "Gameplay":
        message = await cmd.channel.send(embed=discord.Embed(title="Cant place cards",
                                                             description="You can only play cards during gameplay",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    elif Player != bot.Turn:
        message = await cmd.channel.send(embed=discord.Embed(title="Not your Turn",
                                                             description="You can only play cards during your turn",
                                                             color=Colour("Red")))
        await MSGDel(message, cmd)
    else:
        Card = Card.upper()
        AllCards = Card.split(",")
        SameCards = True
        for CardIndex in range(len(AllCards)):
            TempCards = list(AllCards)
            del TempCards[CardIndex]
            try:
                if AllCards[CardIndex] in ["1", "2", "3"]:
                    if len(AllCards) > 1:
                        SameCards = False
                        break
                elif AllCards[CardIndex][1:] != AllCards[0][1:] and AllCards[CardIndex][0] != "J":
                    SameCards = False
                    break
                elif AllCards[CardIndex] in TempCards:
                    SameCards = False
                    break
                if AllCards[CardIndex][0] == "J":
                    ShouldBreak = False
                    for Card in TempCards:
                        if Card[0] != "J":
                            ShouldBreak = True
                            break
                    if ShouldBreak:
                        SameCards = False
                        break
            except Exception as e:
                print(e)
                print(AllCards)
                print(CardIndex)
                print(AllCards[CardIndex])
        if not SameCards:
            message = await cmd.channel.send(embed=discord.Embed(title="Cards not entered correctly",
                                                                 description="To use multiple cards, format your command like this:\n`!mp c8,d8\n(different card types and same value)`",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif SameCards:
            PCards = bot.PlayerInfo[Player]["Cards"]
            try:
                HiddenCardNum = int(AllCards[0])
            except:
                HiddenCardNum = 100
            if not PCards["Hand"] and not PCards["Shown"] and not 1 <= HiddenCardNum <= 3:
                message = await cmd.channel.send(embed=discord.Embed(title="Not a valid Number",
                                                                     description="You are using your hidden cards, please choose a number between `1-3`",
                                                                     color=Colour("Gray")))
                await MSGDel(message, cmd)
            elif not PCards["Hand"] and not PCards["Shown"] and PCards["Hidden"]["IsShown"][HiddenCardNum-1]:
                message = await cmd.channel.send(embed=discord.Embed(title="Cant Play Card",
                                                                     description="The hidden card you are trying to play has already been played",
                                                                     color=Colour("Red")))
                await MSGDel(message, cmd)
            else:
                # Make sure MP accepts "J, Q, K, A"
                ChangedValues = []
                for card in AllCards:
                    if card[1:] == "J":
                        card = card[0] + "11"
                    elif card[1:] == "Q":
                        card = card[0] + "12"
                    elif card[1:] == "K":
                        card = card[0] + "13"
                    elif card[1:] == "A":
                        card = card[0] + "14"
                    ChangedValues.append(card)
                AllCards = ChangedValues
                for card in AllCards:
                    if not PCards["Hand"] and PCards["Shown"] and card not in PCards["Shown"]: # Hand empty + Card not in Shown
                        message = await cmd.channel.send(embed=discord.Embed(title="Not In Top Cards",
                                                                             description=f"The card {card} is not in your top cards",
                                                                             color=Colour("Red")))
                        await MSGDel(message, cmd)
                        break
                    elif PCards["Hand"] and card not in PCards["Hand"]: # Hand full + Card not in Shown
                        message = await cmd.channel.send(embed=discord.Embed(title="Not In Hand",
                                                                             description=f"The card {card} is not in your hand",
                                                                             color=Colour("Red")))
                        await MSGDel(message, cmd)
                        break
                else:
                    # If hidden cards used, change card to hidden card
                    async def PlaceCard():
                        if Card[1:] == "11" or Card[0] == "J":
                            if bot.TopCard[1:] != "11" and bot.TopCard[0] != "J":
                                bot.LastCard = bot.TopCard
                        else:
                            bot.LastCard = Card
                        if Card[1:] == "10":
                            bot.TopCard = "None"
                            bot.Cards = []
                        else:
                            bot.TopCard = Card
                            for card in AllCards:
                                bot.Cards.append(card)
                        if bot.Deck:
                            for _ in AllCards:
                                if len(bot.Deck) >= 1 and (len(PCards["Hand"])-len(AllCards)) < 3:
                                    PCards["Hand"].append(RandomCard())
                        if not PCards["Hand"] and not PCards["Shown"]:
                            PCards["Hidden"]["IsShown"][HiddenCardNum - 1] = True
                        elif not PCards["Hand"]:
                            for card in AllCards:
                                PCards["Shown"].remove(card)
                        else:
                            for card in AllCards:
                                PCards["Hand"].remove(card)
                            SortCardsInHand(Player)
                        IsShown = PCards["Hidden"]["IsShown"]
                        CardSameNum = 0
                        if len(bot.Cards) >= 2 and bot.Cards[-1][0] != "J" and bot.Cards[-1][1:] != "11":
                            def SameCardCheck(CardSameNum, CardNum):
                                if len(bot.Cards) >= CardNum + 1:
                                    if bot.Cards[-(CardNum + 1)][1:] == bot.Cards[-1][1:]:  # if num to last card is same as first
                                        CardSameNum += 1
                                        CardNum += 1
                                        if CardSameNum < 4:
                                            CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                    elif bot.Cards[-(CardNum + 1)][0] == "J" or bot.Cards[-(CardNum + 1)][1:] == "11":
                                        CardNum += 1
                                        CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                return CardSameNum, CardNum
                            CardSameNum, CardNum = SameCardCheck(1, 1)
                        elif len(bot.Cards) >= 2 and bot.Cards[-1][0] == "J":
                            # Card = J1/J2
                            def SameCardCheck(CardSameNum, CardNum):
                                if len(bot.Cards) >= CardNum + 1:
                                    if bot.Cards[-(CardNum + 1)][0] == bot.Cards[-1][0]:  # if num to last card is same as first
                                        CardSameNum += 1
                                        CardNum += 1
                                        if CardSameNum < 2:
                                            CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                    elif bot.Cards[-(CardNum + 1)][1:] == "11":
                                        CardNum += 1
                                        CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                return CardSameNum, CardNum
                            CardSameNum, CardNum = SameCardCheck(1, 1)
                            CardSameNum += 2
                        elif len(bot.Cards) >= 2 and bot.Cards[-1][1:] == "11":
                            # Card = H/C/D/S 11
                            def SameCardCheck(CardSameNum, CardNum):
                                if len(bot.Cards) >= CardNum + 1:
                                    if bot.Cards[-(CardNum + 1)][1:] == bot.Cards[-1][1:]:  # if num to last card is same as first
                                        CardSameNum += 1
                                        CardNum += 1
                                        if CardSameNum < 4:
                                            CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                    elif bot.Cards[-(CardNum + 1)][0] == "J":
                                        CardNum += 1
                                        CardSameNum, CardNum = SameCardCheck(CardSameNum, CardNum)
                                return CardSameNum, CardNum
                            CardSameNum, CardNum = SameCardCheck(1, 1)
                        bot.CardSameNum = CardSameNum
                        if Card[1:] == "10" or CardSameNum == 4:
                            if CardSameNum == 4:
                                bot.TopCard = "None"
                                bot.Cards = []
                            await DisplayCards(cmd.author)
                            if IsShown[0] and IsShown[1] and IsShown[2] and not PCards["Hand"] and not PCards["Shown"]:
                                await asyncio.sleep(1)
                                bot.Winner = cmd.author
                                await GameOver()
                            else:
                                Players = ["P1", "P2"]
                                Players.remove(Player)
                                if PCards["Hand"] or bot.PlayerInfo[Players[0]]["Cards"]["Hand"]:
                                    await Intermission()
                                bot.Turn = Player
                                await asyncio.sleep(1)
                                await DisplayCards("Both")
                        else:
                            if IsShown[0] and IsShown[1] and IsShown[2] and not PCards["Hand"] and not PCards["Shown"]:
                                await DisplayCards(cmd.author)
                                await asyncio.sleep(1)
                                bot.Winner = cmd.author
                                await GameOver()
                            else:
                                Players = ["P1", "P2"]
                                Players.remove(Player)
                                bot.Turn = Players[0]
                                await DisplayCards(cmd.author)
                    async def HiddenPickUp():
                        PCards["Hidden"]["IsShown"][HiddenCardNum - 1] = True
                        PCards["Hand"].append(Card)
                        PCards["Hand"] += bot.Cards
                        SortCardsInHand(Player)
                        bot.Cards = []
                        bot.TopCard = "None"
                        Players = ["P1", "P2"]
                        Players.remove(Player)
                        bot.Turn = Players[0]
                        await DisplayCards(cmd.author)
                    # 2 7 10 11(Jack)
                    if not PCards["Hand"] and not PCards["Shown"]:
                        Card = PCards["Hidden"]["Cards"][HiddenCardNum-1]
                        AllCards = [Card]
                    else:
                        Card = AllCards[-1]
                    # If Player card is not-special/7
                    if Card[1:] in "3,4,5,6,7,8,9,12,13,14".split(","):
                        if bot.TopCard[1:] == "11" or bot.TopCard[0] == "J":
                            if bot.LastCard == "None":
                                await PlaceCard()
                            elif bot.LastCard[1:] == "7":
                                if int(Card[1:]) <= 7:
                                    await PlaceCard()
                                elif not PCards["Hand"] and not PCards["Shown"]:
                                    await HiddenPickUp()
                                else:
                                    message = await cmd.channel.send(embed=discord.Embed(title="Card not valid",
                                                                                         description="Your card is higher than a 7 and not a special card",
                                                                                         color=Colour("Red")))
                                    await MSGDel(message, cmd)
                            elif int(Card[1:]) >= int(bot.LastCard[1:]):  # If Player card is more/equal to the top card
                                await PlaceCard()
                            elif not PCards["Hand"] and not PCards["Shown"]:
                                await HiddenPickUp()
                            else:
                                message = await cmd.channel.send(embed=discord.Embed(title="Card not valid",
                                                                                     description="The card entered has to be higher or equal to the previous card, or be a valid special card",
                                                                                     color=Colour("Red")))
                                await MSGDel(message, cmd)
                        elif bot.TopCard[1:] == "7":  # If the top card is 7
                            if int(Card[1:]) <= 7: # If Player card is less than 7 or is a 7
                                await PlaceCard()
                            elif not PCards["Hand"] and not PCards["Shown"]:
                                await HiddenPickUp()
                            else:
                                message = await cmd.channel.send(embed=discord.Embed(title="Card not valid",
                                                                                     description="Your card is higher than a 7 and not a special card",
                                                                                     color=Colour("Red")))
                                await MSGDel(message, cmd)
                        elif bot.TopCard == "None":  # If the top card is nothing
                            await PlaceCard()
                        elif int(Card[1:]) >= int(bot.TopCard[1:]):  # If Player card is more/equal to the top card
                            await PlaceCard()
                        elif not PCards["Hand"] and not PCards["Shown"]:
                            await HiddenPickUp()
                        else:
                            message = await cmd.channel.send(embed=discord.Embed(title="Card not valid",
                                                                                 description="The card entered has to be higher or equal to the previous card, or be a valid special card",
                                                                                 color=Colour("Red")))
                            await MSGDel(message, cmd)
                    elif Card[1:] == "2" and Card[0] != "J":
                        await PlaceCard()
                    elif Card[1:] == "10":  # Burn
                        await PlaceCard()
                    elif Card[1:] == "11" or Card[0] == "J":  # Blank/Skip
                        await PlaceCard()


@bot.command(aliases=["g"])
async def Game(cmd, command="", Player="None"):
    command = command.lower()
    # Whether its starting or joining a game
    if command == "start" or command == "s":
        if bot.GameState is not None:
            message = await cmd.channel.send(embed=discord.Embed(title="Game In Progression",
                                                                 description="Wait before the game ends before starting a new game",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif bot.GameAvailable:
            # Queue already started
            message = await cmd.channel.send(embed=discord.Embed(title="Queue already started",
                                                                 description="type `!Game join` to join",
                                                                 color=Colour("Gray")))
            await MSGDel(message, cmd)
        elif not bot.GameAvailable:  # If the queue has or hasn't started yet
            # Makes a game available to join
            bot.GameAvailable = True
            # Makes command sender Player1
            bot.PlayerInfo["P1"]["Player"] = cmd.author
            # Queue starts and allows message to be changed globally
            bot.WaitingForPlayerJoin = await cmd.channel.send(embed=discord.Embed(title="Queue Started 1/2",
                          description="Waiting for player 2 to join",
                          color=Colour("Purple")))
    elif command == "join" or command == "j":
        if bot.GameState is not None:
            message = await cmd.channel.send(embed=discord.Embed(title="Game In Progression",
                                                                 description="Wait before the game ends before starting a new game",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif not bot.GameAvailable:  # If the queue has or hasn't started yet
            # No queue
            message = await cmd.channel.send(embed=discord.Embed(title="No queue has been started",
                                                                 description="type `!Game start` to start a queue",
                                                                 color=Colour("Gray")))
            await MSGDel(message, cmd)
        elif bot.GameAvailable:
            # Checking if Player2 is not Player1
            if cmd.author == bot.PlayerInfo["P1"]["Player"]:
                # Player2 is Player1
                message = await cmd.channel.send(embed=discord.Embed(title="Unable to join",
                                                                     description=f"You are already Player 1, you need another player to join",
                                                                     color=Colour("Red")))
                await MSGDel(message, cmd)
            else:
                # Sets Player2 as command sender
                bot.PlayerInfo["P2"]["Player"] = cmd.author
                # Joins game
                await cmd.channel.send(embed=discord.Embed(title="Joining Game",
                                                                     description=f"You are now in a game with {bot.PlayerInfo['P1']['Player'].mention}",
                                                                     color=Colour("Purple")))
                # Changes queue started message
                await bot.WaitingForPlayerJoin.edit(embed=discord.Embed(title="Game has started 2/2",
                          description=f"Player 1: {bot.PlayerInfo['P1']['Player'].mention}\nPlayer 2: {bot.PlayerInfo['P2']['Player'].mention}",
                          color=Colour("Purple")))
                for Invite in bot.Invites:
                    await bot.Invites[Invite]["InviterMSG"].edit(embed=discord.Embed(title="Invite Invalid",
                                                           description="Game has already started",
                                                           color=Colour("Red")))
                    await bot.Invites[Invite]["InvitedMSG"].edit(embed=discord.Embed(title="Invite Invalid",
                                                           description="Game has already started",
                                                           color=Colour("Red")))
                await MainGame()
    elif command == "invite" or command == "i":
        async def MentionedPlayer():
            try:
                Member = await MemberConverter().convert(cmd, Player)
            except discord.ext.commands.errors.MemberNotFound:
                Member = "None"
            return Member
        if bot.GameState is not None:
            message = await cmd.channel.send(embed=discord.Embed(title="Game In Progression",
                                                                 description="Wait before the game ends before inviting a player",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif bot.GameAvailable:
            # Queue already started
            message = await cmd.channel.send(embed=discord.Embed(title="Queue already started",
                                                                 description="Cant invite when a queue is open, type `!Game join` to join",
                                                                 color=Colour("Gray")))
            await MSGDel(message, cmd)
        elif Player == "None":
            message = await cmd.channel.send(embed=discord.Embed(title="No Player @'d",
                                                                 description="To invite a player, type `!game invite @(player-name)` or type `!game start`",
                                                                 color=Colour("Gray")))
            await MSGDel(message, cmd)
        elif (await MentionedPlayer()) == "None":
            message = await cmd.channel.send(embed=discord.Embed(title="Player Not Valid",
                                                                 description="Please mention a player to invite them",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif (await MentionedPlayer()) == cmd.author:
            message = await cmd.channel.send(embed=discord.Embed(title="Cant Invite Yourself",
                                                                 description="You can not invite yourself to a game",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        else:
            CreateInvite = True
            Player = await MentionedPlayer()
            for Invite in bot.Invites:
                bot.Invites[Invite]
                if bot.Invites[Invite]["Inviter"] == cmd.author and bot.Invites[Invite]["Invited"] == Player:
                    CreateInvite = False
                    break
            if not CreateInvite:
                message = await cmd.channel.send(embed=discord.Embed(title="Invite already exists",
                                                                     description="You have already created an invite with this player",
                                                                     color=Colour("Red")))
                await MSGDel(message, cmd)
            else:
                try:
                    embed = discord.Embed(title=f"You have been invited to a game of Massacre ({len(bot.Invites) + 1})",
                                          description=f"Type `!game accept {len(bot.Invites) + 1}` to accept the invite",
                                          color=Colour("Purple"))
                    embed.set_footer(text=f"Invite by '{cmd.author.display_name}'")
                    InvitedMSG = await Player.send(embed=embed)
                    embed = discord.Embed(title=f"Invited Player",
                                          description=f"You have invited player to Game `{len(bot.Invites) + 1}`",
                                          color=Colour("Purple"))
                    embed.set_footer(text=f"Invite by '{cmd.author.display_name}'")
                    InviterMSG = await cmd.channel.send(embed=embed)
                    bot.Invites[str(len(bot.Invites)+1)] = {"Inviter": cmd.author, "Invited": Player, "InviterMSG": InviterMSG, "InvitedMSG": InvitedMSG}
                except:
                    message = await cmd.channel.send(embed=discord.Embed(title="Cant Message Player",
                                                                         description="This bot can not send an invite message to the player",
                                                                         color=Colour("Red")))
                    await MSGDel(message, cmd)
    elif command == "accept" or command == "a":
        if bot.GameState is not None:
            message = await cmd.channel.send(embed=discord.Embed(title="Game In Progression",
                                                                 description="Wait before the game ends before accepting an invite",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif bot.GameAvailable:
            # Queue already started
            message = await cmd.channel.send(embed=discord.Embed(title="Queue already started",
                                                                 description="Cant accept invite when a queue is open, type `!Game join` to join",
                                                                 color=Colour("Gray")))
            await MSGDel(message, cmd)
        elif Player == "None":
            message = await cmd.channel.send(embed=discord.Embed(title="No Invite Specified",
                                                                 description="You have to specify an invite number to accept",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif Player not in bot.Invites:
            message = await cmd.channel.send(embed=discord.Embed(title="Invite Does Not Exist",
                                                                 description="You have to specify an valid invite number to accept",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif cmd.author != bot.Invites[Player]["Invited"]:
            message = await cmd.channel.send(embed=discord.Embed(title="Not Invited",
                                                                 description="You were not invited by that invite number",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        else:
            bot.PlayerInfo["P1"]["Player"] = bot.Invites[Player]["Inviter"]
            bot.PlayerInfo["P2"]["Player"] = cmd.author
            await bot.Invites[Player]["InvitedMSG"].edit(embed=discord.Embed(title=f"Joining Game",
                                                                             description=f"You are now in a game with {bot.PlayerInfo['P1']['Player'].mention}",
                                                                             color=Colour("Purple")))
            await bot.Invites[Player]["InviterMSG"].edit(embed=discord.Embed(title=f"Game Started",
                                                                             description=f"Player 1: {bot.PlayerInfo['P1']['Player'].mention}\nPlayer 2: {bot.PlayerInfo['P2']['Player'].mention}",
                                                                             color=Colour("Purple")))
            await bot.Invites[Player]["Inviter"].send(embed=discord.Embed(title="Invite Accepted",
                                                                             description=f"{bot.PlayerInfo['P2']['Player'].mention} has accepted your invite",
                                                                             color=Colour("Purple")))
            del bot.Invites[Player]
            for Invite in bot.Invites:
                await bot.Invites[Invite]["InviterMSG"].edit(embed=discord.Embed(title="Invite Invalid",
                                                                                 description="Game has already started",
                                                                                 color=Colour("Red")))
                await bot.Invites[Invite]["InvitedMSG"].edit(embed=discord.Embed(title="Invite Invalid",
                                                                                 description="Game has already started",
                                                                                 color=Colour("Red")))
            bot.GameAvailable = True
            await MainGame()
    elif command == "leave" or command == "l":
        if bot.GameState is not None:
            message = await cmd.channel.send(embed=discord.Embed(title="Game In Progression",
                                                                 description="Wait before the game ends before starting a new game",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif not bot.GameAvailable:
            message = await cmd.channel.send(embed=discord.Embed(title="Cant Leave queue",
                                                                 description="You must start a queue to leave one",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        elif cmd.author != bot.PlayerInfo["P1"]["Player"]:
            message = await cmd.channel.send(embed=discord.Embed(title="Not In Queue",
                                                                 description="You must be in a queue to leave one",
                                                                 color=Colour("Red")))
            await MSGDel(message, cmd)
        else:
            bot.GameAvailable = False
            bot.PlayerInfo["P1"]["Player"] = None
            await bot.WaitingForPlayerJoin.edit(embed=discord.Embed(title="Queue Ended",
                          description="Player 1 left the queue",
                          color=Colour("Red")))
            await MSGDel(bot.WaitingForPlayerJoin, cmd)
    else:
        # Give options on how to use command
        message = await cmd.channel.send(embed=discord.Embed(title="Massacre Bot",
                                                             description="Please type either of the following:\n`!Game start`\n`!Game join`\n`!Game leave`",
                                                             color=Colour("Gray")))
        await MSGDel(message, cmd)


@bot.command(aliases=["mh", "help"])
async def MHelp(cmd):
    GameStart = "**!Game Start** - Starts a queue for another player to join.\n\n"
    GameJoin = "**!Game Join** - Joins a previously made queue.\n\n"
    GameLeave = "**!Game Leave** - Leaves a previously made queue.\n\n"
    MPlace = "**!MPlace/Place/MP (Card)** - If you own the card entered, it will be placed (if using hidden cards, type '1-3').\n\n"
    MPlaceMulti = "**!MPlace/Place/MP (Card),(Card)** - If you own the cards entered, they will be placed.\n\n"
    MPickUp = "**!MPickUp/Pickup/MPU** - Picks up the pile and puts the cards into your hand.\n\n"
    MSwap = "**!MSwap/Swap/MS (Hand Card) (Top Card)** - During intermissions, it swaps the card in your hand with one of your top cards.\n\n"
    MReady = "**!MReady/Ready/MR** - Readies you up when prompted (Intermissions & Results).\n\n"
    MCancel = "**!MCancel/Cancel/MC** - During Results, this would stop you from playing another game.\n\n"
    MLeave = "**!MLeave/Leave** - This makes you forfeit the game and lets the other player win.\n\n"
    Ping = "**!Ping** - This pings the other player.\n\n"
    MHelp = "**!MHelp/Help/MH** - Shows all bot commands."
    AllCommands = f"{GameStart}{GameJoin}{GameLeave}{MPlace}{MPlaceMulti}{MPickUp}{MSwap}{MReady}{MCancel}{MLeave}{Ping}{MHelp}"
    await cmd.channel.send(embed=discord.Embed(title="Massacre Commands", description=AllCommands, color=Colour("Gray")))


@bot.command()
async def SuperSecretPrint(cmd):
    if cmd.author.id == bot.owner_id:
        print(bot.PlayerInfo["P1"]["Cards"])
        print(bot.PlayerInfo["P2"]["Cards"])
        print(bot.Deck)
        print(bot.Cards)
        print(bot.Turn)


TOKEN = discord_token
bot.run(TOKEN)
