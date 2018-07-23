
import os.path
import sys
import json
import random
import string
import webbrowser
import socket
import speech_recognition as sr
import playsound
import time
import time

from naoqi import ALProxy

IP = "192.168.1.102"  # Replace here with your NaoQi's IP address.
PORT = 9559


#access token for dialogflow
CLIENT_ACCESS_TOKEN = 'a4c37b43822649869ac3deca4d7f82a7'

#try to import apiai
try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

# Create a proxy to ALFaceDetection
try:
  faceProxy = ALProxy("ALFaceDetection", IP, PORT)
  print ('faceDetectionProxy created')
except Exception, e:
  print "Error when creating face detection proxy:"
  print str(e)
  exit(1)

# Subscribe to the ALFaceDetection proxy
# This means that the module will write in ALMemory with
# the given period below
period = 500
faceProxy.subscribe("Test_Face", period, 0.0 )

# ALMemory variable where the ALFacedetection modules
# outputs its results
memValue = "FaceDetected"

# Create a proxy to ALMemory
try:
  memoryProxy = ALProxy("ALMemory", IP, PORT)
  print('memoryCreated')
except Exception, e:
  print "Error when creating memory proxy:"
  print str(e)
  exit(1)

tts = ALProxy("ALTextToSpeech", IP, PORT)
print('tts created') 


#this function plays the sound for speech reco
def mPlaySound(path):
    aup = ALProxy("ALAudioPlayer", "127.0.0.1", 54710)
    aup.playFile("resources/audio.m4v")


#this function opens an audio stream, using google's api for decoding user's words
def listen():
    
    r = sr.Recognizer()

    print('listening..')
    with sr.Microphone() as source:
        #playsound('resources/audio.m4v')
        audio = r.listen(source)
    
    try:
        print("recognizing..")
        result = r.recognize_google(audio)
        
        tts.say('you said: '+result)
        return result

    except:
        print('error')
        pass


#this function sends to NAO the results obtained from dialogflow
#is it necessary?
def socketSend(data):
    #name of local node
    HOST = '127.0.0.1'                 

    #port used for comunication
    PORT = 5007                             
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    print 'Connected by', addr
    while 1:
        data = conn.recv(1024)
        if not data: break
        conn.send(data)
    conn.close()
    


#this function builds request to dialogflow, uses the words decoded from the listen() function
#to build the string and makes the request

def buildRequest(request, mString):
    
    mRequest = ""
    
    #if the string is empty there is no context on dialogflow,
    #so the function builds a new request with new context
    
    if mString == "":
        mRequest = raw_input('input_text:')
        #print("input_text:")
        #mRequest = listen()
        request.query = mRequest
        
    #if the string is not empty there is context running, so i need to complete this request    
    else:
        mRequest+=mString
        request.query = mRequest
        
    #print (mRequest)
    return request.query


#this function build the request id using random numbers

def buildSessionID():
    session = 'Session_ID:'
    for count in range(1,7):
        session+=(random.choice(string.digits))
    return session

   
    
def main(mString):
    #new ai object    
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

    #define a new request
    request = ai.text_request()

    request.lang = 'en'  # optional, default value equal 'en'

    request.session_id = buildSessionID()

    request.query = buildRequest(request, mString)
    
    result = json.loads(request.getresponse().read())

    print (u"%s" % result['result']['fulfillment']['speech'])
    #socketSend(u"%s" % result['result']['fulfillment']['speech'])
    tts.say(str(u"%s" % result['result']['fulfillment']['speech']))
    
    
    #if the request is smalltalk, the context will became empty
    if "smalltalk" in result['result']['action']:
        mString = ""
        startFaceReco()
        
     
    #searchRestaurant intent is incomplete -> i need to complete it
    elif (result['result']['actionIncomplete']) == True and (result['result']['metadata']['intentName']) == "searchRestaurant":    
        priceKind = raw_input('you:')
        #priceKind = listen()
        tts.say('What do you want to eat?')
        foodKind = raw_input('What do you want to eat?\nyou:')
        #foodKind = listen()
        intent = result['result']['contexts'][2]['parameters']['Restarants_Bars1']
        
        mString = intent + ' ' + priceKind + ' '+ foodKind
        main(mString)
    
    #searchRestaurant intent is complete -> the url of tripadvisor is opened
    elif(result['result']['actionIncomplete']) == False and (result['result']['metadata']['intentName']) == "searchRestaurant":
        url = result['result']['fulfillment']['data']
        webbrowser.open(url)
        mString = ""
        main(mString)
     
    #events intent 
    elif result['result']['metadata']['intentName'] == "findEvents":  
        url = result['result']['fulfillment']['data']
        print 'opening...',url
        webbrowser.open(url)  
        mString = ""
        startFaceReco()
       
     
    #intent monumenti incompleto -> richiedo monumento     
    elif (result['result']['actionIncomplete']) == True and (result['result']['metadata']['intentName']) == "findMonuments":
        intent = result['result']['contexts'][0]['parameters']['monumentsIntentDetected']
        monumentName = raw_input('input_text: ')
        #monumentName = listen()
        mString = intent + ' '+monumentName
        main(mString)
     
    #intent monumenti completo -> mostro foto + descrizione monumento   
    elif (result['result']['actionIncomplete']) == False and (result['result']['metadata']['intentName']) == "findMonuments":
        url = result['result']['fulfillment']['data']
        print 'opening...',url
        webbrowser.open(url)  
        mString = ""
        startFaceReco()
        
    
     #se l'intent e' completo, dopo la risposta azzera mString e riparte
    else:
        mString = ""
        startFaceReco()
          
         
        

def startFaceReco():
     
    # A simple loop that reads the memValue and checks whether faces are detected.
    for i in range(0, 20):
      time.sleep(3)
      val = memoryProxy.getData(memValue)
    
      print ""
      print "*****"
      print ""
    
      # Check whether we got a valid output.
      if(val and isinstance(val, list) and len(val) >= 2):
    
        # We detected faces !
        # For each face, we can read its shape info and ID.
    
        # First Field = TimeStamp.
        timeStamp = val[0]
    
        # Second Field = array of face_Info's.
        faceInfoArray = val[1]
    
        try:
          # Browse the faceInfoArray to get info on each detected face.
          for j in range( len(faceInfoArray)-1 ):
            faceInfo = faceInfoArray[j]
    
            # First Field = Shape info.
            faceShapeInfo = faceInfo[0]
    
            # Second Field = Extra info (empty for now).
            faceExtraInfo = faceInfo[1]
    
            print('face detected')
            #tts.say("hi there!I'm NAO Mola, i can give you info about restaurants, events, monuments and public services. So, Ask me something!")
            tts.say("hi, there!")
            mString = ""
            main(mString)
            #print "  alpha %.3f - beta %.3f" % (faceShapeInfo[1], faceShapeInfo[2])
            #print "  width %.3f - height %.3f" % (faceShapeInfo[3], faceShapeInfo[4])
    
        except Exception, e:
          print "faces detected, but it seems getData is invalid. ALValue ="
          print val
          print "Error msg %s" % (str(e))
      else:
        print "No face detected"
    
    
    # Unsubscribe the module.
    faceProxy.unsubscribe("Test_Face")
    
    print "Test terminated successfully."



if __name__ == '__main__': 
    startFaceReco()