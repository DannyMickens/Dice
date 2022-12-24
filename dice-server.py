
# Python program to implement server side of a dice game
# skeleton client-server architecture from https://www.geeksforgeeks.org/simple-chat-room-using-python/
import socket
import select
import sys
from _thread import *
 
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 
# checks whether sufficient arguments have been provided
if len(sys.argv) != 3:
    print ("Correct usage: script, IP address, port number")
    exit()
 
# takes the first argument from command prompt as IP address
IP_address = str(sys.argv[1])
 
# takes second argument from command prompt as port number
Port = int(sys.argv[2])
 
server.bind((IP_address, Port))

server.listen(2)
 
list_of_clients = []
 
def clientthread(conn, addr):
 
    # sends a message to the client, conn
    welcome_message = "You Have Successfully Connected to the Lobby".encode()
    conn.send(welcome_message)
 
    while True:
        try:
            message = conn.recv(2048) #optimize, client sends int4 with length of remaining message
            if message:
                print ("<" + addr[0] + "> " + message)

                # Calls broadcast function to send message to all
                message_to_send = "<" + addr[0] + "> " + message
                broadcast(message_to_send, conn)

            else:
                # message may have no content if the connection is broken, in this case remove the connection
                remove(conn)
        except:
            continue
 
# function for broadcasting to all clients except for the one from which the message is generated
def broadcast(message, connection):
    for clients in list_of_clients:
        if clients != connection:
            try:
                clients.send(message)
            except:
                clients.close()
                # if the link is broken, we remove the client
                remove(clients)
 
# The following function removes a client connection from the list of clients 
def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)
 
while True:
    conn, addr = server.accept()
 
    # Maintains a list of clients for ease of broadcasting
    list_of_clients.append(conn)
 
    # prints the address of the user that just connected
    print (addr[0] + " connected")
 
    # creates and individual thread for every user that connects
    start_new_thread(clientthread,(conn,addr))    
 
conn.close()
server.close()