#!/usr/bin/env -S python3 -u
'''
Ce script est associé à l'extension native Mozilla (cf. ~/.mozilla/native-messaging-hosts/pap.pdf.analysis@hpms.org.json).
On ne passe pas le chemin du PDF en paramètre car le contrat des extensions natives est de lire stdio pour décoder les paramètres au format json.
#'''
import os
import pathlib
import struct
import sys
import traceback

import dotenv
import json
import openai
import pdf2image
import pytesseract


def eprint( *args, **kwargs ):
   '''If debug is ON, print a message to stderr.'''
   if DEBUG:
      print( *args, file = sys.stderr, **kwargs )


def get_message():
   '''Retrieve action and data from Thunderbird XPI extension.'''
   try:
      raw_length = sys.stdin.buffer.read( 4 )
      eprint( f'raw_length = {raw_length}' )
      message_length = struct.unpack( '=I', raw_length)[0]
      eprint( f'message_length = {message_length}' )
      message        = sys.stdin.buffer.read(message_length).decode("utf-8")
      eprint( f'message = {message}' )
      return json.loads( message )
   except:
      traceback.print_exc()
      sys.exit( 0 )


def encode_message( message_content ):
   '''Encode a message for transmission, given its content.'''
   encoded_content = json.dumps( message_content ).encode( "utf-8" )
   encoded_length  = struct.pack( '=I', len( encoded_content ))
   return {
      'length' : encoded_length,
      'content': struct.pack( str( len( encoded_content )) + "s", encoded_content )
   }


def send_message( encoded_message ) -> None:
   '''Send an encoded message to stdout.'''
   sys.stdout.buffer.write( encoded_message[ 'length' ])
   sys.stdout.buffer.write( encoded_message[ 'content' ])
   sys.stdout.buffer.flush()


def extract_text_from_pdf( pdf_path: str ) -> str | None:
   '''Extract text from a PDF file with Tesseract OCR.'''
   try:
      name = os.path.basename( pdf_path )
      if name[ len( name ) - 4 : ].lower() == '.pdf':
         name   = name[ : len( name ) - 4 ]
         PNG    = '/tmp/' + name
         images = pdf2image.convert_from_path( pdf_path )
         if images:
            eprint( f"images: {images}" )
            text = ""
            for image in images:
               image_path = f'{PNG}.png'
               image.save( image_path, 'PNG')
               text += pytesseract.image_to_string( image_path )
            eprint( f"text: {text}" )
            return text
   except Exception as x:
      print( x, file = sys.stderr )
   eprint( f"Path doesn't denote a PDF file: {pdf_path}" )
   return None


def extract_info_from_text( text: str ) -> dict:
   '''Use OpenAI ChatGPT to analyse a PAP text and extract keys information.'''
   try:
      if text:
         request = [{
            "role"   : "system",
            "content": "Vous êtes un assistant utile qui répond en JSON. " +\
                        "Aidez-moi à analyser une invitation à une réunion contenue dans le texte joint."
         },{
            "role"   : "user",
            "content": [{
               "type": "text",
               "text":
                  "Extraire du texte suivant, " +
                  "le lieu de la réunion de négociation du protocole d'accord préélectoral dans le champ 'place', " +
                  "la date de cette réunion dans le champ 'date' au format JJ/MM/AAAA, " +
                  "l'heure de cette réunion dans le champ 'timestamp' au format hh:mm:ss."
            },{
               "type": "text",
               "text": text
            }]
         }]
         eprint( f"request = '{request}'" )
         client = openai.OpenAI( api_key = OPENAI_API_KEY )
         result = client.chat.completions.create( model = MODEL, messages = request )
         answer = result.choices[0].message.content
         eprint( f"answer before replacement = '{answer}'" )
         answer = answer.replace( '"heure"'       , '"timestamp"' )
         answer = answer.replace( '"lieu"'        , '"place"' )
         answer = answer.replace( '"lieu_reunion"', '"place"' )
         eprint( f"answer after replacement = '{answer}'" )
         # Parfois, OpenAI ajoute la décoration ```json\n et \n``` autour du texte de la réponse.
         start  = answer.find( '{' )
         stop   = answer.find( '}' )
         eprint( f"answer before replacement (JSON) = '{answer}'" )
         answer = answer[start:stop+1]
         eprint( f"answer after replacement (JSON) = '{answer}'" )
         info   = json.loads( answer )
         info['text'] = text
         info['timestamp'] = f"{info['date']} {info['timestamp']}"
         parts  = info['date'].split('/')
         info['date'] = f"{parts[2]}.{parts[1]}.{parts[0]}"
         if not ( "place" in info ):
            for key in info:
               if ( key != 'date' )and( key != 'timestamp' ):
                  info['place'] = info[key]
                  eprint( f"key 'place' added from '{key}': {info}" )
         return info
   except Exception as x:
      print( x, file = sys.stderr )
   return {
      'date'     : '2024.xx.xx',
      'timestamp': 'xx/xx/2024 xx:xx:00',
      'place'    : 'xxx',
      'text'     : text
   }


while True: # Once launched, wait for request
   try:
      dotenv.load_dotenv()
      DEBUG          = os.getenv("DEBUG")
      OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
      MODEL          = os.getenv("MODEL")
      NEW_PATH       = os.getenv("NEW_PATH")
      message        = get_message()
      eprint( f"message['action'] = \"{message['action']}\"" )
      if message['action'] == "extract-text":
         name = os.path.basename( message['path'] )
         eprint( f"name = \"{name}\"" )
         ext = name[ len( name ) - 4 : ].lower()
         eprint( f"ext = \"{ext}\"" )
         if ext == '.pdf':
            name = name[11:].strip()   # On enlève le début du nom "2024 03 05 "
            if( name[0:1] == "-" ):
               name = name[1:].strip() # On enlève le tiret et l'espace qui suit
            if( name[0:3] == "PAP" ):
               name = name[3:].strip() # On enlève "PAP" et l'espace qui suit
            eprint( f"name = \"{name}\"" )
            text = extract_text_from_pdf( message['path'] )
            info = extract_info_from_text( text )
            eprint( f"info = \"{info}\"" )
            # yyyy/mm/dd hh:mm:00
            hm_parts = info['timestamp'].split(' ')
            hm_parts = hm_parts[1].split(':')
            # YYYY.MM.DD-HH:MM
            date = f"{info['date']}-{hm_parts[0]}.{hm_parts[1]}"
            send_message(
               encode_message({
                  'name'     : name,
                  'date'     : date,
                  'timestamp': info['timestamp'],
                  'place'    : info['place'],
                  'text'     : info['text']
            }))
      elif message['action'] == "rename":
         basename = os.path.basename( message['path'] )
         if basename[ len( basename ) - 4 : ].lower() == '.pdf':
            oldPath = message['path']
            name    = message['name']
            dot     = name.find('.')
            year    = name[0:dot]
            month   = name[dot+1:dot+3]
            newPath = f'{NEW_PATH}/{year}/{month}/{name}'
            try:
               parentDir = os.path.dirname( newPath )
               os.mkdir( parentDir, 0o777 )
               eprint( f'{parentDir} created' )
            except:
               None
            pathlib.Path( oldPath ).rename( newPath )
            eprint( f'{oldPath} renamed to {newPath}' )
   except Exception:
      traceback.print_exc()
