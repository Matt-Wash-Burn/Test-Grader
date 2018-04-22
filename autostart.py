#GPIOstartup.py
import RPi.GPIO as GPIO
from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageOps
from array import array
##import cv2 # OpenCV for perspective transform
import numpy as np
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
import os
import time
import picamera



######################################
# WARPS IMAGE FOR FORMATTING
# Input: raw image file, corner coordinates
# Output: warped image file
######################################
def transform(img):
    # Define calibration box in source (actual) and destination (desired) coordinates
    TLE = [120, 660] # [x , y]
    TRE = [100, 10]
    BLE = [1120, 620]
    BRE = [1100, -12]
    
    y = 612
    x = 400
    
    # img = Image.open(cd+"SDscantronsheet.jpg")
    in_data = np.asarray(img, dtype=np.uint8)
    
    image_without_alpha = in_data[:,:,:3]
    
    # Convert back to Pillow to save Image
    img = Image.fromarray(np.uint8(image_without_alpha))
    
    # x0, y0, x1, y1, x2, y2, y3, y3
    # upper left, lower left, lower right, and upper right corner 
    coeffs= (TLE[0], TLE[1], BLE[0], BLE[1],  BRE[0], BRE[1], TRE[0], TRE[1])
    
    im=img.transform((x, y), Image.QUAD, coeffs,Image.BILINEAR)
    im.save("warpedImagenBILINEAR.jpg")
    return im

    

######################################
# FORMATS IMAGE
# Input: warped  image file
# Output: formatted image file, bounding box
######################################
def format(test):
    
    #blurs the test image and converts to RGB format
    formatted = test.filter(ImageFilter.GaussianBlur(radius=2))
    formatted.convert('RGBA')
    (w, h) = formatted.size
    
    #splits into RGB bands
    if(formatted.mode == 'RGBA'):
        Rformatted, Gformatted, Bformatted, alpha = formatted.split()
        Rformatted = Rformatted.filter(ImageFilter.CONTOUR)
    else:
        Rformatted, Gformatted, Bformatted = formatted.split()
        Rformatted = Rformatted.filter(ImageFilter.CONTOUR)
    
    
    #thresholds the R band
    (width, height) = Rformatted.size
    Rpix = Rformatted.load()
    for i in range(width):
         for j in range(height):
             if (Rpix[i,j] >= 238):
                 Rpix[i,j] = 255
             if(Rpix[i,j] < 238):
                 Rpix[i,j] = 0
    boundbox = Rformatted.getbbox()
    
    Rformatted.save("r.jpg")
    return Rformatted, boundbox
######################################



######################################
# TRAINS ALGORITHM FOR MARK DETECTION
# Input: formatted image file
# Output: list of line y-coordinates and bubble-field x-coordinates
######################################
def train(r):
    lines = array('i') #array to hold y value for each line
    boxes = array('i') #array to hold x value for each bubble column
    
    pix = r.load()
    width, height = r.size
    #finds the y value of each question line (49 lines total)
    line = 0 #current line seeked to
    i=2 #gives the image a starting position to begin seeking from
    while(line < 49):
        while(pix[20, i] >= 160):
            i = i + 1
        while(pix[20, i] <= 160):
            i = i + 1
            if(i == height-1):
                lines.append(i)
                line = line+1
                break
        lines.append(i)
        line = line+1
        
    
    items = []
    items.append(10) #width of bubble
    items.append(13) #space between bubbles
    #returns all line and bubble fields as arrays
    return (lines, items)
######################################



######################################
# FINDS ALL MARKED BUBBLES
# Input: line coordinates, bubble-field coordinates, formatted image file
# Output: List of all filled-in bubbles per question
######################################
def find(lines, items, r):
    marks = []
    pix = r.load()
    thresh = 12
    
    period = 21
    one = 40
    two = one + 5*items[1] + period
    three = two + 5*items[1] + period
    four = three + 5*items[1] + period
    for line in range(23): #finds marks on questions 1-20
        submarks = [0, 0, 0, 0, 0]
        for bubble in range(0, 5):
            dots = 0
            for x in range(one + (1+bubble)*items[1], one + (1+bubble)*items[1] + items[0]):
                for y in range(lines[line+26] - 5, lines[line+26] + 2):
                    if (pix[x, y] == 0):
                        dots = dots + 1
                    pix[x, y] = 200 #test fields
            if (dots > thresh):
                submarks[bubble] = 1
        if(line != 5 and line != 11 and line != 17):
            marks.append(submarks)
    r.save("TEST.jpg")
            
    for line in range(23): #finds marks on questions 21-40
        submarks = [0, 0, 0, 0, 0]
        for bubble in range(0, 5):
            dots = 0
            for x in range(two + (1+bubble)*items[1], two + (1+bubble)*items[1] + items[0]):
                for y in range(lines[line+26] - 5, lines[line+26] + 1):
                    if (pix[x, y] == 0):
                        dots = dots + 1
                    pix[x, y] = 200 #test fields
            if (dots > thresh):
                submarks[bubble] = 1
        if(line != 5 and line != 11 and line != 17):
            marks.append(submarks)
    r.save("TEST.jpg")    
    
    for line in range(23): #finds marks on questions 41-60
        submarks = [0, 0, 0, 0, 0]
        for bubble in range(0, 5):
            dots = 0
            for x in range(three + (1+bubble)*items[1], three + (1+bubble)*items[1] + items[0]):
                for y in range(lines[line+26] - 5, lines[line+26] + 2):
                    if (pix[x, y] == 0):
                        dots = dots + 1
                    pix[x, y] = 200 #test fields
            if (dots > thresh):
                submarks[bubble] = 1
        if(line != 5 and line != 11 and line != 17):
            marks.append(submarks)
    r.save("TEST.jpg")
            
    for line in range(23): #finds marks on questions 61-80
        submarks = [0, 0, 0, 0, 0]
        for bubble in range(0, 5):
            dots = 0
            for x in range(four + (1+bubble)*items[1], four + (1+bubble)*items[1] + items[0]):
                for y in range(lines[line+26] - 5, lines[line+26] + 2):
                    if (pix[x, y] == 0):
                        dots = dots + 1
                    pix[x, y] = 200 #test fields
            if (dots > thresh):
                submarks[bubble] = 1
        if(line != 5 and line != 11 and line != 17):
            marks.append(submarks)
    r.save("TEST.jpg")
    
    #returns all bubbled answers as an array [question #][filled bubbles]
    return marks
######################################    
    
    
    
    
    
######################################
# CREATES GRADING RUBRIC BASED OFF OF KEY BUBBLES
# Input: list of filled-in bubbles
# Output: list of bubble weights per question
######################################
def rubric(marks):
    weight = [] #stores the weight of each bubble per question
    for i in range(len(marks)): #keeps going until no questions are left
        if(marks[i] == [0,0,0,0,0]):
            break
        a,b,c,d,e = marks[i]
        weight.append(1.00/(a+b+c+d+e)) #determines fraction of point per correct bubble
    totalpoints = i
    return weight
######################################   
   
   
   
   
######################################
# GRADES EXAMS BASED OFF OF RUBRIC
# Input: list of key and exam marks, list of mark weights per question
# Output: Total score out of max-possible points, list of corrections to be made
######################################
def grade(answerKey, answers, weight):
    score = len(weight)
    corrections = [] #stores corrections to be made for the drawing/correction function
    for i in range(score):
        subcorrections = []
        A,B,C,D,E = answerKey[i]
        a,b,c,d,e = answers[i]
        #creates a corrections-to-be-made list
        corrections.append([A-a, B-b, C-c, D-d, E-e])
        #determines how many points were missed per question
        points = (abs(a-A)+abs(b-B)+abs(c-C)+abs(d-D)+abs(e-E))* weight[i] 
        if(abs(points) > 1):
            points = 1
        #subtracts incorrect marks from total score
        score = score - abs(points)
        
    return score, corrections
######################################   
   


######################################
# DRAWS CORRECTIONS ON EXAM
# Input: Original raw image, lines and bubbles coordinates, corrections list
# Output: Image modified to have corrections
######################################
def corrected(image, lines, items, corrections):
    red = (255,0,0)
    drawings = ImageDraw.Draw(image)
    
    
    period = 21
    one = 40
    two = one + 5*items[1] + period
    three = two + 5*items[1] + period
    four = three + 5*items[1] + period
    
    #1-20
    for i in range(20):
        skip = (i%20)/5
        y0 = lines[i%20+26+skip] - 5
        y1 = lines[i%20+26+skip] 
        if (i > len(corrections)-1):
            break
        else:
            for j in range(len(corrections[i])):
                x0 = one + items[1]*(1+j)
                x1 = one + items[1]*(1+j) + items[0]
                if(corrections[i][j] == 1):
                    drawings.ellipse((x0, y0, x1, y1), red, red)
                if(corrections[i][j] == -1):
                    drawings.line((x0, y0, x1, y1), red, 2)
            
    #21-40
    for i in range(20,40):
        skip = (i%20)/5
        y0 = lines[i%20+26+skip] - 5
        y1 = lines[i%20+26+skip]
        if (i > len(corrections)-1):
            break
        else:
            for j in range(len(corrections[i])):
                x0 = two + items[1]*(1+j)
                x1 = two + items[1]*(1+j) + items[0]
                if(corrections[i][j] == 1):
                    drawings.ellipse((x0, y0, x1, y1), red, red)
                if(corrections[i][j] == -1):
                    drawings.line((x0, y0, x1, y1), red, 2)
            
    #41-60
    for i in range(40,60):
        skip = (i%20)/5
        y0 = lines[i%20+26+skip] - 5
        y1 = lines[i%20+26+skip]
        if (i > len(corrections)-1):
            break
        else:
            for j in range(len(corrections[i])):
                x0 = three + items[1]*(1+j)
                x1 = three + items[1]*(1+j) + items[0]
                if(corrections[i][j] == 1):
                    drawings.ellipse((x0, y0, x1, y1), red, red)
                if(corrections[i][j] == -1):
                    drawings.line((x0, y0, x1, y1), red, 2)
            
    #61-80
    for i in range(60,80):
        skip = (i%20)/5
        y0 = lines[i%20+26+skip] - 5
        y1 = lines[i%20+26+skip]
        if (i > len(corrections)-1):
            break
        else:
            for j in range(len(corrections[i])):
                x0 = four + items[1]*(1+j)
                x1 = four + items[1]*(1+j) + items[0]
                if(corrections[i][j] == 1):
                    drawings.ellipse((x0, y0, x1, y1), red, red)
                if(corrections[i][j] == -1):
                    drawings.line((x0, y0, x1, y1), red, 2)
    
    return image
   
######################################
# PDF MAKER
# Input: list of corrected exam images
# Output: a PDF file containing all of the results
######################################
def jpg2pdf(exams):
    
    
    for i in range (len(exams)-1):
        im1 = exams[i]
        width, height = im1.size
        out1 = im1.transpose(Image.ROTATE_270)
        width, height = out1.size
        background = Image.new('RGB', (width, height*2), (255, 255, 255, 255))
        offset =(0, 0)
        background.paste(out1, offset)
        if (i+1 < len(exams)):
            im2 = exams[i+1]
            out2 = im2.transpose(Image.ROTATE_270)
            offset =(0, height)
            background.paste(out2, offset)
            i = i + 1
        #background.save("corrected.jpg")
        background.save("out.pdf","PDF", resolution = 100.0)
        merger = PdfFileMerger()
        merger.append(PdfFileReader(file("results.pdf", 'rb')))
        merger.append(PdfFileReader(file("out.pdf", 'rb')))
        merger.write("results.pdf")
    
######################################

    
    
######################################

def start():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    #configures 4 LED GPIO output pins
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(11, GPIO.OUT)
    GPIO.setup(13, GPIO.OUT)
    GPIO.setup(15, GPIO.OUT)

    #configures 4 PB GPIO input pins
    key = 29
    exam = 31
    done = 33
    reset = 35
    GPIO.setup(key, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(exam, GPIO.IN,pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(done, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(reset, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    print ('started')
cam = picamera.PiCamera()



def SCAN(img):
    image = transform(Image.open(img))
    r, bbox = format(image)
    lines, boxes = train(r)
    answers = find(lines, boxes, r)
    return lines, boxes, answers, image

def GRADE(lines, boxes, answers, answerkey, weight, image):
    finalscore, corrections = grade(answerkey, answers, weight)
    image = corrected(test1, lines, boxes, corrections)
    return image, finalscore

def KEY(lines, boxes, answerkey):
    weight = rubric(answerkey)
    return answerkey, weight


##########################################
  #  begin
##########################################
start()


key = transform(Image.open("autorun.jpg"))
test1 = transform(Image.open("autorun1.jpg"))
test2 = transform(Image.open("autorun.jpg"))
exams = [] #list that stores graded exam images

#initialize LEDS as off
GPIO.output(7, GPIO.LOW) 
GPIO.output(11, GPIO.LOW)
GPIO.output(13, GPIO.LOW)
GPIO.output(15, GPIO.LOW)


while True:

    #Key input PB
    if GPIO.input(29):
        started = time.time()
        print "Key Accepted"
        GPIO.output(7, GPIO.HIGH)
        lines, boxes, answers, image = SCAN("autorun.jpg")
        answerkey, weight = KEY(lines, boxes, answers)
        GPIO.output(7, GPIO.LOW)
        end = time.time()
        print(end - started), "seconds elapsed"


    #Exam input PB
    if GPIO.input(31):
        started = time.time()
        print "Exam Accepted"
        GPIO.output(11, GPIO.HIGH)
        lines, boxes, answers, image = SCAN("autorun1.jpg")
        correct, finalscore = GRADE(lines, boxes, answers, answerkey, weight, image)
        GPIO.output(11, GPIO.LOW)
        exams.append(correct)
        end = time.time()
        print(end - started), "seconds elapsed"

    #Done input PB
    if GPIO.input(35):
        started = time.time()
        print "Done Accepted"
        GPIO.output(13, GPIO.HIGH)
        jpg2pdf(exams)
        GPIO.output(13, GPIO.LOW)
        end = time.time()
        print(end - started), "seconds elapsed"

    #Done input PB
    if GPIO.input(33):
        started = time.time()
        print "taking picture..."
        GPIO.output(15, GPIO.HIGH)
        cam.capture("takeone.jpg")
        GPIO.output(15, GPIO.LOW)
        end = time.time()
        print(end - started), "seconds elapsed"
