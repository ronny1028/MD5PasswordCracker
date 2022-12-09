import socket
import time
from _thread import *
import threading


'''password "aBdQn" --> MD5 "0954aadcc1c9366879c03ab1a5f4a12e" '''

#a variable to record our search progress by int
searchCount = 0
#a flag that indicates whether we found the password
found = 0
#store the password result we found
passwordResult = 0
#the timer for recording the start time
timer1 = 0

#A function that takes an integer as input, and return a string of 5 chars
#The int input "data" act as a search progress tracker
#So that we can iterate through combinations of chars easily by only increasing the value of "data"
def intToGuess(data):
    #a string for tranforming int values to char. kind of like ASCII code, but starts from 0
    #i.e. possibleChars[0] = "a"
    possibleChars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLNMOPQRSTUVWXYZ"
    #an empty string, for returning result
    stringResult = ""
    #answer = [0, 0, 0, 0, 0] represents password "aaaaa"; each value of this array represents a char in final string guess, from left to right
    answer = [0, 0, 0, 0, 0]
    for index in range(len(answer)) :
        #Update array with the current data divided by the value of 52 to the power of (4-index)
        #data = 1 --> answer = [0, 0, 0, 0, 1] --> stringResult "aaaab"
        #data = 53 --> answer = [0, 0, 0, 1, 1] --> stringResult "aaabb"
        answer[index] = data // pow(52, 4-index)
        #update the remaining value of data
        data = data % pow(52, 4-index)
    #transform the values in "answer[]" to chars, and concatenate them
    stringResult = possibleChars[answer[0]] + possibleChars[answer[1]] + possibleChars[answer[2]] + possibleChars[answer[3]] + possibleChars[answer[4]]
    return stringResult



print_lock = threading.Lock() 
#Thread function, in one thread we try 100,000 counts of guesses
#Create a new thread and build connection
def guess100kTimes(c): 
    global searchCount
    #global flag for whether answer is found
    global found
     
    data = c.recv(1024) 
    #The worker sends a message when its connection to server is created
    if data.decode('ascii') == "connected":
        #if the "found" flag is true, tell the worker by sending and empty byte message
        if found == 1:
            c.send(b'')
        else:
            # not "found" yet
            #send the MD5 input provided by user to worker
            c.send(PASSWORD_DIGEST.encode('ascii'))
            #provide the staring searchCount to worker
            c.send(searchCount.to_bytes(5, "big"))
            #and add a customized step size per thread connection, which is 100,000
            searchCount = searchCount + 100000
        print_lock.release()

    #The worker sends a "found" message when it founds the matching MD5
    elif data.decode('ascii') == "found":
        #record the end time
        timer2 = time.perf_counter()
        c.send("Affirmative.".encode('ascii'))
        #send affirmative, and wait for "i" from the worker
        data = c.recv(1024)
        passwordResult = int.from_bytes(data, "big")
        #print results in console
        print("The cracked password is: " + intToGuess(passwordResult))
        print("Time spent: " + str((timer2-timer1)*1000) + " ms")
        
        #Change the global flag to close the socket in main()
        found = 1
        print_lock.release() 

    #The worker sends a "not found" message if the password wasn't found in the given searchCount range
    elif data.decode('ascii') == "not found":
        print("searching ...... Last guess we tried is: " + intToGuess(searchCount-100000))
        #if the "found" flag is true, tell the worker by sending and empty byte message
        if found == 1:
            c.send(b'')
        else:
            #not found yet
            #provide another starting searchCount to worker
            c.send(searchCount.to_bytes(5, "big"))
            searchCount = searchCount + 100000
        print_lock.release() 

    #Finally, close the connection
    c.close() 

def Main():
    global PASSWORD_DIGEST
    global timer1

    #hard-coded public routable IP address and port number
    host = '143.215.216.202'   
    #Opens a socket at port 10086
    port = 10086
    
    # scan user MD5 input
    print("Please enter the MD5 to crack:")
    PASSWORD_DIGEST = str(input())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
    s.bind((host, port)) 
    print("socket created and binded to port: ", port) 
  
    s.listen(5) 
    print("socket is listening now") 

    #Start timer from the time the socket start listening
    timer1 = time.perf_counter()

    #Keep looping until the answer is found
    while found == 0:
        # in each iteration, we create another connection
        c, addr = s.accept()
        print_lock.acquire()
        #and a new thread for that connection, so that multiple workers can work concurrently
        start_new_thread(guess100kTimes, (c,))
    #Finally, close socket connection when password result is found
    s.close()

if __name__ == '__main__': 
    Main()