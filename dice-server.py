### TO DO LIST ###
# ADD NICKNAMES
# CHECK NETWORKING OVER MULTIPLE INTERNET CONNECTIONS
# FIX WINNING LOGIC. CURRENTLY FIRST PLAYER TO 10000 WINS
# FIX BUG - CLIENT ENTERING A SPACE AFTER ROLLING
# SERVER PROMPT/SCRIPT ARGS TO ALLOW DIFFERENT NUMBER OF PLAYERS
# CLIENT INSTALLATION INSTRUCTIONS ???
# DISPLAY CURRENT ROLL SCORE WHEN ASKING TO KEEP ROLLING


# Python program to implement server side of a dice game
# skeleton client-server architecture from https://www.geeksforgeeks.org/simple-chat-room-using-python/
import socket
import select
import sys
import random
from time import sleep
from threading import Thread, Lock
from collections import Counter
 
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverIP = socket.gethostbyname(socket.gethostname())
serverPort = 8081
players = []
playerThreads = {}
lock = Lock()

###### PLAYER CLASS #####
class Player:

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.nickname = None
        self.score = 0

    def endConnection(self):
        self.conn.close()

##### END OF PLAYER CLASS #####

##### GAME PLAYING FUNCTIONS ##### make these functions of the player class

def takeTurn(player):  
    turnScore = 0
    numSavedDice = 0
    dice = [0, 0, 0, 0, 0, 0]  

    def keepRolling():
        nonlocal numSavedDice
        if (numSavedDice == 0 or numSavedDice == 6): # can only be true before first roll or after rollover
            numSavedDice = 0
            return True
        return (numSavedDice <= 6 and ask(player, "Would you like to continue rolling? (y/n): ") == "y")
    
    def isBust(results):
        # note we don't call calculatePoints just a single time because player 
        # may not want to keep all dice that are worth points
        return calculatePoints(results, True) == 0

    def calculatePoints(results, isDryRun = False):
        rollScore = 0
        # duplicate of results, modified to pull out values that have been used already
        updatedResults = results.copy() if results else []
        print(updatedResults)

        def contains(l1, l2):
            return not (Counter(l2) - Counter(l1))

        def saveDie(dieVal):
            nonlocal numSavedDice
            if isDryRun: return
            dice[numSavedDice] = str(dieVal)
            numSavedDice += 1
            updatedResults.remove(str(dieVal))
        
        def checkFor1250():
            if sorted(updatedResults) == ["1", "2", "3", "4", "5", "6"]:
                for i in range(6):
                    saveDie(i)
                return 1250
            return 0

        def checkForThreeOfAKind():
            #possibility of two sets of three in single roll
            tempScore = 0
            for i in range(1, 7):
                if contains(updatedResults, [str(i) for num in range(3) ]):
                    tempScore += 1000 if i == 1 else i * 100
                    for num in range(3):
                        saveDie(i)
            return tempScore
        
        def checkForOnesAndFives():
            ones = updatedResults.count("1")
            for _ in range(ones):
                saveDie(1)
            fives = updatedResults.count("5")
            for _ in range(fives):
                saveDie(5)
            return 100 * ones + 50 * fives

        return checkFor1250() + checkForThreeOfAKind() + checkForOnesAndFives()
        
    def roll(player):
        print("Rolling for player " + player.addr[0])
        results = [str(x) for x in random.choices(range(1, 7), k=(6 - numSavedDice))]
        resultsMessage = "results " + " ".join(results)
        tell(player, resultsMessage)
        return results
    
    # check that every die the player wants to save exists in the roll
    def isValidResponse(results, response):
        if (len(response) == 0):
            return False
        c1, c2 = Counter(response), Counter(results)
        for key, count in c1.items():
            if count > c2[key]:
                return False
        return True

    # find out what dice the player wants to save, as long as the roll produces points
    def fetchResponse(results):
        response = ask(player, "Which dice would you like to keep? (eg. 2 2 2 5): ")
        while not isValidResponse(results, response.split()):
            response = ask(player, "Invalid selection, please respond with a space separated list"
                                  + " of numbers you would like to keep (eg. 2 2 2 5): ")
        return response.split()
    
    while (keepRolling()):
        tell(player, "Rolling ... ")
        sleep(1) # for 'suspense' ... (simulate a roll) 
        results = roll(player)
        if isBust(results):
            tell(player, "Bust! No points for you")
            turnScore = 0
            break
        response = fetchResponse(results)
        turnScore += calculatePoints(response)
        tell(player, f"Your current roll is at {turnScore} points")
    player.score += turnScore
    tell(player, f"you scored {turnScore} points.\nYour total score is {player.score}")

##### END OF GAME PLAYING FUNCTIONS #####

##### CLIENT SERVER IO UTIL FUNCTIONS ##### make these functions of a util class
def tell(player, message):
    if isinstance(message, str): message = (message + "\n").encode()
    player.conn.send(message)

def listen(player):
    player.conn.settimeout(30)
    response = player.conn.recv(2048).decode().strip()
    if response:
        return response
    else:
        # message may have no content if the connection is broken, in this case remove the connection
        remove(player)

def ask(player, message):
    tell(player, message)
    response = listen(player)
    return response

##### END OF CLIENT SERVER IO UTIL FUNCTIONS #####

##### COMMUNICATION FUNCTIONS #####

def welcomePlayer(player):
    welcome_message = "You Have Successfully Connected to the Lobby".encode()
    tell(player, welcome_message)

# function for broadcasting to all clients except for the one from which the message is generated
def broadcast(message, connection):
    for player in players:
        if player.conn != connection:
            try:
                tell(player, message)
            except:
                remove(player)

##### END OF COMMUNICATION FUNCTIONS 

def playerAction(player):
    pass
    # try:
    #     while True:
    #         response = listen(player).decode()
    #         if response:
    #              print ("<" + player.addr[0] + "> " + response)
    #              # Calls broadcast function to send message to all
    #              # message_to_send = "<" + player.addr[0] + "> " + response
    #              # broadcast(message_to_send, player.conn)
    # except Exception as e:
    #     print(e)
    #     # continue
    # finally:
    #     remove(player)
 
# The following function removes a client connection from the list of clients
# end the client connection, join the thread, remove the client from the list of players and player threads 
def remove(player):
    print("Removing player " + player.addr[0])
    player.endConnection()
    #playerThreads[player.addr[0]].join()
    #del playerThreads[player.addr[0]]
    players.remove(player)

def collectPlayers():
    global players

    def addPlayer():
        conn, addr = server.accept()
     
        # Maintain a list of clients
        player = Player(conn, addr)
        players.append(player)
    
    def addPlayerThread(): # unused until needing chat room
        # creates and individual thread for every user that connects
        t = Thread(target=playerAction, args=(players[-1],))
        t.start()
        playerThreads[players[-1].addr[0]] = t
        
    # lock.acquire()
    print("Waiting for players...")
    while len(players) < 2:
        addPlayer()
        print (players[-1].addr[0] + " connected")
        # addPlayerThread()
    print("Players found, starting game...")
    # lock.release()

def checkForWinner():
    for player in players:
        if player.score >= 1000:
            return player.addr[0]
    return None

def playGame():
    while checkForWinner() == None:
        for player in players:
            tell(player, "It is your turn!")
            takeTurn(player)
    broadcast(f"We have a winner! Congratulations {checkForWinner()}", server)

##### SETUP/TEARDOWN #####

def setup():
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((serverIP, serverPort))
    print("Server listening on " + serverIP + ":" + str(serverPort))
    server.listen(2) # hold up to two connections for now

def teardown():
    broadcast("game over", server)
    for player in players:
        player.endConnection()
    # for thread in playerThreads.values():
    #     thread.join()
    server.close()
    print("Done")

##### END OF SETUP/TEARDOWN

def main():
    setup()
    try:
        collectPlayers()
        # while len(players) > 0:
        playGame()
    finally:
        teardown()

if __name__ == "__main__":
    # execute only if run as a script
    main()