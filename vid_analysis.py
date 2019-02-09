import requests
from pprint import pprint
import time
import wave
import cv2
import urllib, json
import requests
from PIL import Image
import subprocess

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("""Importing the Speech SDK for Python failed.""")
    import sys
    sys.exit(1)


def prep_files():
    #webm file from html stuff has to be called RecordedVideo.webm
    #convert webm to mp4
    command = "ffmpeg -i RecordedVideo.webm ConvertedVideo.mp4"
    subprocess.call(command, shell=True)
    #extract audio from 
    command = "ffmpeg -i RecordedVideo.mp4 -ab 160k -ac 2 -ar 44100 -vn audio.wav"
    subprocess.call(command, shell=True)

def speech_to_text(fname):
    # <SpeechContinuousRecognitionWithFile>
    # Set up the subscription info for the Speech Service:
    # Replace with your own subscription key and service region (e.g., "westus").
    speech_key, service_region = "726c413a94124443b16dc18cbbaab56d", "westus"

    # Specify the path to an audio file containing speech (mono WAV / PCM with a sampling rate of 16
    # kHz).
    afilename = fname
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    audio_config = speechsdk.audio.AudioConfig(filename=afilename)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    done = False
    total_text = list()
    def stop_cb(evt):
        """callback that stops continuous recognition upon receiving an event `evt`"""
        print('CLOSING on {}'.format(evt))
        speech_recognizer.stop_continuous_recognition()
        #print(' '.join(total_text))
        nonlocal done
        done = True

    
    # Connect callbacks to the events fired by the speech recognizer
    #speech_recognizer.recognizing.connect(lambda evt: print(evt.result.text) )
    #speech_recognizer.recognized.connect(lambda evt: print('RECOGNIZED: {}'.format(evt)))
    #speech_recognizer.recognized.connect(lambda evt: print(evt.result.text))
    speech_recognizer.recognized.connect(lambda evt: total_text.append((evt.result.text, (time.time() - start))))
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    start = time.time()
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)
    return total_text

def vidparse():
    # Replace the subscription_key string value with your valid subscription key.
    # subscription_key = 'd46920f5b1314be8b41e14fb88d702fe'
    subscription_key = '5a076632c4254c11b500da5f4acd3f17'

    ## Request headers.
    header = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    # Request parameters.
    params = urllib.parse.urlencode({
        'returnFaceAttributes': 'smile,emotion',
    })

    api_url = "https://westus.api.cognitive.microsoft.com/face/v1.0/detect?%s"%params

    ###############

    # vidcap = cv2.VideoCapture("adithi.mov")
    vidcap = cv2.VideoCapture(0)

    counter = 0

    success,image = vidcap.read()
    success = True
    while success:
        print("now")
        success,image = vidcap.read()
        frame_img = Image.fromarray(image)
        frame_img.save("frame_img.jpg", "JPEG", quality=80, optimize=True, progressive=True)
        with open("frame_img.jpg", 'rb') as f:
            img_data = f.read()

        r = requests.post(api_url, params=params,
                    headers=header,
                    data=img_data)
        cv2.imshow("output", image)
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break
        print (r.json())


    vidcap.release()
    cv2.destroyAllWindows()

def text_analysis(text):
    subscription_key = "9ca01fb5107449439a19c6b1bfd56e09"
    text_analytics_base_url = "https://westcentralus.api.cognitive.microsoft.com/text/analytics/v2.0/"
    sentiment_api_url = text_analytics_base_url + "sentiment"
    dlist = list()
    for i in range(0,len(text)):
        dicty = dict()
        dicty['id'] = str(i)
        dicty['language'] = 'en'
        dicty['text'] = text[i]
        dlist.append(dicty)

    documents = {'documents' : dlist}
    headers   = {"Ocp-Apim-Subscription-Key": subscription_key}
    response  = requests.post(sentiment_api_url, headers=headers, json=documents)
    sentiments = response.json()
    senti_list = list()
    for i in range(0,len(sentiments['documents'])):
        tup = (documents['documents'][i]['text'], sentiments['documents'][i]['score'])
        senti_list.append(tup)
    return senti_list


def main():
    prep_files()
    texty = speech_to_text("audio.wav")
    text = list()
    for i in range(0,len(texty)):
        list.append(texty[i][0])
    #text emotions is list of tuples (text,sentiment score)
    text_emotions = text_analysis(text)

