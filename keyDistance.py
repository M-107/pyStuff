# https://youtu.be/Mf2H9WZSIyw

import math
from cmath import sqrt

keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M"]]

# Legion Y520 values
dist = 19
shifts = [0, 7, 16]

def keyPos(key):
    for x, i in enumerate(keys):
        if key.upper() in i:
            keyRow = x
            keyCol = i.index(key.upper())
    keyX = shifts[keyRow] + dist * keyCol
    keyY = keyRow * dist
    return([keyX, keyY])

def keyDist(key1, key2):
    xDelta = abs(keyPos(key1)[0] - keyPos(key2)[0])
    yDelta = abs(keyPos(key1)[1] - keyPos(key2)[1])
    keyDist = round(sqrt(xDelta**2 + yDelta**2).real, 2)
    return(keyDist)

def keyAngle(key1, key2, key3):
    angle = math.degrees(math.atan2(keyPos(key3)[1]-keyPos(key2)[1], keyPos(key3)[0]-keyPos(key2)[0]) - math.atan2(keyPos(key1)[1] - keyPos(key2)[1], keyPos(key1)[0]-keyPos(key2)[0]))
    return round(angle + 360 if angle < 0 else angle, 2)

def wordLength(word):
    length = 0.0
    for i in range(0, len(word[:-1])):
        length += keyDist(word[i], word[i+1])
    return(round(length, 2))

def wordAngle(word):
    angle = 0.0
    for i in range(0, len(word[:-2])):
        angle += keyAngle(word[i], word[i+1], word[i+2])
    return(round(angle, 2))

while True:
    word = input("Please input a word:\n")
    if word.isalpha():
        print(f"The lenght of '{word.lower()}' is {wordLength(word)} mm.")
        print(f"The angle of '{word.lower()}' is {wordAngle(word)} °.\n")
    else:
        print("Please input only a signle word using the english alphabet.\n")
