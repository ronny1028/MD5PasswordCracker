import socket 
import hashlib
from server import intToGuess


def Main():
    #Store the value of search range given by server, default set to -1
    searchRange = -1

    #A flag indicating whether a matching digest has been found by this client/worker
    foundFlag = 0
    #hard-coded public routable IP address and port number
    #TODO update this line if server ip changed
    host = '143.215.216.202'
    port = 10086
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,port))

    # if successfully connected, send a message to server to inticiate the process
    s.send("connected".encode('ascii'))
 
    try:
        #retrieve the content of server message
        MATCH_DIGEST = s.recv(32).decode('ascii')
        if MATCH_DIGEST == '':
            #empty message indicates server already found a result
            foundFlag = 1
            s.close()
        else:
            #normal message, print the message including the hash hexdigest that needs to be matched
            print(MATCH_DIGEST)
            #Next, retrieve the range that the worker needs to search
            data = s.recv(1024)
            searchRange = int.from_bytes(data, "big")
            print(searchRange)
            s.close()
    except ConnectionResetError:
        print("Password has been found and the connection is terminated")
        foundFlag = 1

    #we successfully receieved MATCH_DIGEST and "searchRange" from the section above, now we can loop and try guessings
    while foundFlag==0:
        #create another flag. The flag "flag" is only used to mark whether the for loop below have found a matching hash digest
        flag = 0
        for i in range(searchRange, searchRange+100000):
            #try 100000 guesses
            strI = intToGuess(i)
            digResult = hashlib.md5(strI.encode('ascii')).hexdigest()
            #if the digResult matches the digest in MATCH_DIGEST
            if digResult == MATCH_DIGEST:
                #set flag to true, and record the current value of i
                flag = 1
                searchRange = i
                break
        
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #now, we either finished 100000 iterations, or found a matching digest
        if flag == 1:
            #if we found a matching digest
            s.connect((host, port))
            s.send("found".encode('ascii'))
            #wait for affirmative from server
            s.recv(1024)
            #and then send the "searchRange" value to sercver
            s.send(searchRange.to_bytes(5, "big"))
            #change flag so that the outer while loop breaks
            foundFlag = 1
        else:
            #if we did not find a matching digest in given searchRange
            s.connect((host, port))
            s.send("not found".encode('ascii'))
            #wait for another message from server
            try:
                data = s.recv(1024)
                if data == b'':
                    #change flag so that the outer while loop breaks
                    foundFlag = 1
                else:
                    #update searchRange value, get prepared for the next iteration
                    searchRange = int.from_bytes(data, "big")
                    print(searchRange) 
            except ConnectionResetError:
                print("Password has been found and the connection is terminated")
                #change flag so that the outer while loop breaks
                foundFlag = 1
        
        s.close()
        

if __name__ == '__main__': 
    Main()