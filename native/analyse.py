#!/usr/bin/env -S python3 -u
# -*- coding: utf-8 -*-
"""
This script is associated to a native Mozilla extension,
cf. ~/.mozilla/native-messaging-hosts/pap.pdf.analysis@hpms.org.json.

The runtime interface is driven by native Mozilla Thunderbird extension
contract, cf. methods get_message and send_message of the PAP_Analysis class.
"""
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


class PAP_Analysis:

   def eprint( self, *args, **kwargs ):
      """If debug is ON, print a message to stderr."""
      if self.DEBUG:
         print( *args, file = sys.stderr, **kwargs )

   def get_message( self ):
      """Retrieve action and data from Thunderbird XPI extension."""
      try:
         raw_length = sys.stdin.buffer.read( 4 )
         self.eprint( f'raw_length = {raw_length}' )
         message_length = struct.unpack( '=I', raw_length)[0]
         self.eprint( f'message_length = {message_length}' )
         message = sys.stdin.buffer.read(message_length).decode("utf-8")
         self.eprint( f'message = {message}' )
         return json.loads( message )
      except:
         traceback.print_exc()
         sys.exit( 0 )

   def encode_message( self, message_content ):
      """Encode a message for transmission, given its content."""
      encoded_content = json.dumps( message_content ).encode( "utf-8" )
      encoded_length  = struct.pack( '=I', len( encoded_content ))
      return {
         'length' : encoded_length,
         'content': struct.pack( str( len( encoded_content )) + "s",
                                 encoded_content )
      }

   def send_message( self, encoded_message ) -> None:
      """Send an encoded message to stdout."""
      sys.stdout.buffer.write( encoded_message[ 'length' ])
      sys.stdout.buffer.write( encoded_message[ 'content' ])
      sys.stdout.buffer.flush()

   def extract_text_from_pdf( self, pdf_path: str ) -> str | None:
      """Extract text from a PDF file with Tesseract OCR.

      Arguments:
         pdf_path: the path of the PDF file to analyze.

      Returns:
         The content of the PDF file as raw text.
      """
      try:
         name = os.path.basename( pdf_path )
         if name[ len( name ) - 4 : ].lower() == '.pdf':
            name   = name[ : len( name ) - 4 ]
            PNG    = '/tmp/' + name
            images = pdf2image.convert_from_path( pdf_path )
            if images:
               self.eprint( f"images: {images}" )
               text = ""
               for image in images:
                  image_path = f'{PNG}.png'
                  image.save( image_path, 'PNG')
                  text += pytesseract.image_to_string( image_path )
               self.eprint( f"text: {text}" )
               return text
      except Exception as x:
         print( x, file = sys.stderr )
      self.eprint( f"Path doesn't denote a PDF file: {pdf_path}" )
      return None

   def extract_info_from_text( self, text: str ) -> dict:
      """Use OpenAI ChatGPT to analyse a PAP text and extract keys
      information.

      Arguments:
         text: the PDF content to analyze.

      Returns:
         A dictionary with the following keys:
            'date'     : 2024.xx.xx
            'timestamp': xx/xx/2024 xx:xx:00
            'place'    : The address of the enterprise
            'text'     : The content of the PDF file as raw text.
      """
      try:
         if text:
            request = [{
               "role"   : "system",
               "content": "Vous êtes un assistant utile qui répond en " +
                           "JSON. Aidez-moi à analyser une invitation " +
                           "à une réunion contenue dans le texte joint."
            },{
               "role"   : "user",
               "content": [{
                  "type": "text",
                  "text":
                     "Extraire du texte suivant, " +
                     "le lieu de la réunion de négociation du protocole "+
                     "d'accord préélectoral dans le champ 'place', " +
                     "la date de cette réunion dans le champ 'date' au "+
                     "format JJ/MM/AAAA, " +
                     "l'heure de cette réunion dans le champ 'timestamp' "+
                     "au format hh:mm:ss."
               },{
                  "type": "text",
                  "text": text
               }]
            }]
            self.eprint( f"request = '{request}'" )
            client = openai.OpenAI( api_key = self.OPENAI_API_KEY )
            result = client.chat.completions.create( model = self.MODEL, messages = request )
            answer = result.choices[0].message.content
            self.eprint( f"answer before replacement = '{answer}'" )
            answer = answer.replace( '"heure"'       , '"timestamp"' )
            answer = answer.replace( '"lieu"'        , '"place"' )
            answer = answer.replace( '"lieu_reunion"', '"place"' )
            self.eprint( f"answer after replacement = '{answer}'" )
            # Parfois, OpenAI ajoute la décoration ```json\n et \n``` autour du texte de la réponse.
            start  = answer.find( '{' )
            stop   = answer.find( '}' )
            self.eprint( f"answer before replacement (JSON) = '{answer}'" )
            answer = answer[start:stop+1]
            self.eprint( f"answer after replacement (JSON) = '{answer}'" )
            info   = json.loads( answer )
            info['text'] = text
            info['timestamp'] = f"{info['date']} {info['timestamp']}"
            parts  = info['date'].split('/')
            info['date'] = f"{parts[2]}.{parts[1]}.{parts[0]}"
            if not ( "place" in info ):
               for key in info:
                  if ( key != 'date' )and( key != 'timestamp' ):
                     info['place'] = info[key]
                     self.eprint( f"key 'place' added from '{key}': {info}" )
            return info
      except Exception as x:
         print( x, file = sys.stderr )
      return {
         'date'     : '2024.xx.xx',
         'timestamp': 'xx/xx/2024 xx:xx:00',
         'place'    : 'xxx',
         'text'     : text
      }

   def listen_to_thunderbird( self ) -> None:
      """Listen to thunderbird messages.

      This function treat messages from Thunderbird extension in a forever loop.
      Messages contains 'action' and data.
      Action can be 'extract-text' or 'rename', other fields are action dependant.
      For 'extract-text' the other field is 'path', for 'rename' they are 'path' and 'name'.

      Arguments:
         None.

      Returns:
         Never.
      """
      while True: # Once launched, wait for request
         try:
            message = self.get_message()
            self.eprint( f"message['action'] = \"{message['action']}\"" )
            if message['action'] == "extract-text":
               name = os.path.basename( message['path'] )
               self.eprint( f"name = \"{name}\"" )
               ext = name[ len( name ) - 4 : ].lower()
               self.eprint( f"ext = \"{ext}\"" )
               if ext == '.pdf':
                  name = name[11:].strip()   # On enlève le début du nom "2024 03 05 "
                  if( name[0:1] == "-" ):
                     name = name[1:].strip() # On enlève le tiret et l'espace qui suit
                  if( name[0:3] == "PAP" ):
                     name = name[3:].strip() # On enlève "PAP" et l'espace qui suit
                  self.eprint( f"name = \"{name}\"" )
                  text = self.extract_text_from_pdf( message['path'] )
                  info = self.extract_info_from_text( text )
                  self.eprint( f"info = \"{info}\"" )
                  # yyyy/mm/dd hh:mm:00
                  hm_parts = info['timestamp'].split(' ')
                  hm_parts = hm_parts[1].split(':')
                  # YYYY.MM.DD-HH:MM
                  date = f"{info['date']}-{hm_parts[0]}.{hm_parts[1]}"
                  self.send_message(
                     self.encode_message({
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
                  newPath = f'{self.NEW_PATH}/{year}/{month}/{name}'
                  try:
                     parentDir = os.path.dirname( newPath )
                     os.mkdir( parentDir, 0o777 )
                     self.eprint( f'{parentDir} created' )
                  except:
                     traceback.print_exc()
                  pathlib.Path( oldPath ).rename( newPath )
                  self.eprint( f'{oldPath} renamed to {newPath}' )
               else:
                  self.eprint( f"{basename} doesn't end by .pdf!" )
         except Exception:
            traceback.print_exc()

   def __init__( self ):
      """PAP PDF Analysis constructor.

      This function changes the current directory then loads the content of
      '.env' file which contains OpenAI API key and other preferences.
      """
      os.chdir( os.path.dirname( os.path.abspath( __file__ )))
      dotenv.load_dotenv()
      self.DEBUG          = os.getenv("DEBUG").lower() == 'true'
      self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
      self.MODEL          = os.getenv("MODEL")
      self.NEW_PATH       = os.getenv("NEW_PATH")


if __name__ == '__main__':
   pap = PAP_Analysis()
   pap.listen_to_thunderbird()
