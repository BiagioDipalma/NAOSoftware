'''
Created on 28 giu 2018

@author: BiagioDipalma
'''

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
import winsound

#try to import apiai
try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

#access token for dialogflow
CLIENT_ACCESS_TOKEN = 'a4c37b43822649869ac3deca4d7f82a7'


#r is the speech recognizer 
r = sr.Recognizer()

#m is the microphone used for listening
m = sr.Microphone()



#this function opens an audio stream, using google's api for decoding user's words
def listen():
    
    time.sleep(3)
    print("ok, you can speak after the acustic sound")
    with m as source: r.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(r.energy_threshold))
    print("Say something!")
    winsound.PlaySound(("audio.wav"), winsound.SND_ASYNC)
    with m as source: audio = r.listen(source)
    print("OK! Let me think about it")
    try:
        # recognize speech using Google Speech Recognition
        value = r.recognize_google(audio)

        print value
        # we need some special handling here to correctly print unicode characters to standard output
        if str is bytes:  # this version of Python uses bytes for strings (Python 2)
            value = format(value).encode("utf-8")
            print(u"You said {}".format(value).encode("utf-8"))
            return value
        else:  # this version of Python uses unicode for strings (Python 3+)
            value = format(value)
            print("You said {}".format(value))
            return value
    except sr.UnknownValueError:
        print("Oops! Didn't catch that")
        listen()
    except sr.RequestError as e:
        print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
        listen()



#this function builds request to dialogflow, uses the words decoded from the listen() function
#to build the string and makes the request

def buildRequest(request, mString):
    
    mRequest = ""
    
    #if the string is empty there is no context on dialogflow,
    #so the function builds a new request with new context
    
    if mString == "":
        #mRequest = raw_input('input_text:')
        #print("input_text:")
        mRequest = listen()
        request.query = mRequest
        
    #if the string is not empty there is context running, so i need to complete this request    
    else:
        mRequest+=mString
        request.query = mRequest
        
    print (mRequest)
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
    #tts.say(str(u"%s" % result['result']['fulfillment']['speech']))
    
    
    #if the request is smalltalk, the context will became empty
    if "smalltalk" in result['result']['action']:
        mString = ""
        main(mString)
     
    #searchRestaurant intent is incomplete -> i need to complete it
    elif (result['result']['actionIncomplete']) == True and (result['result']['metadata']['intentName']) == "searchRestaurant":    
        #priceKind = raw_input('you:')
        priceKind = listen()
        #tts.say('What do you want to eat?')
        print("what do you want to eat?")
        #foodKind = raw_input('What do you want to eat?\nyou:')
        foodKind = listen()
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
        #print url
        webbrowser.open(url)  
        mString = ""
        main(mString)
     
    #intent monumenti incompleto -> richiedo monumento     
    elif (result['result']['actionIncomplete']) == True and (result['result']['metadata']['intentName']) == "findMonuments":
        intent = result['result']['contexts'][0]['parameters']['monumentsIntentDetected']
        #monumentName = raw_input('input_text: ')
        monumentName = listen()
        mString = intent + ' '+monumentName
        main(mString)
     
    #intent monumenti comleto -> mostro foto + descrizione monumento   
    elif (result['result']['actionIncomplete']) == False and (result['result']['metadata']['intentName']) == "findMonuments":
        url = result['result']['fulfillment']['data']
        #print url
        webbrowser.open(url)  
        mString = ""
        main(mString) 
    
     #se l'intent e' completo, dopo la risposta azzera mString e riparte
    else:
        mString = ""
        main(mString)    
         
        
if __name__ == '__main__':
    
    mString = ""
    
    main(mString)
    
    




    
    