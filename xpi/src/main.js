/**
 * Ce script analyse le contenu du mail affiché quand on clique sur le bouton "Analyse PAP".
 * Si la structure du mail est conforme à l'attendu, on extrait l'information confédérale
 * et on lance la reconnaissance de texte à partir du PDF en pièce jointe.
 */
const START_OF_BODY = "---------- Forwarded message ---------";

async function getFederationAddress( id ) {
   const rawMsg = await browser.messages.getRaw( id );
   let   sob    = rawMsg.indexOf( START_OF_BODY );
   if( sob > -1 ) {
      sob += START_OF_BODY.length;
      let toNdx = rawMsg.indexOf( "To: ", sob );
      if( toNdx - sob > 200 ) {
         console.error( "Le champ 'To: ' est très loin du début, c'est louche ! (%d)", toNdx );
      }
      else {
         // On cherche la prochaine ligne vide
         const end = rawMsg.indexOf( "\r\n\r\n", toNdx );
         const to  = rawMsg.slice( toNdx + 3, end );
         // On enlève les caractères de sauts de ligne (CR, LF) et on découpe aux virgules
         // pour constituer un tableau d'adresses composé normalement de deux adresses :
         // celle de l'UL et celle de la fédération concernée par le PAP
         const addresses = to.replaceAll( "Cc:", "," ).replaceAll( "\n", "" ).replaceAll( "\r", "" ).split( ',' );
         for( let address of addresses ) {
            if( address.indexOf( "ulcgtmerignac@gmail.com" ) < 0 ) {
               return address;
            }
         }
         return 'Aucune';
      }
   }
   return undefined;
}

const escapeTextForHtml = ( unsafe ) => {
   return unsafe
      .replaceAll( '"' , '&quot;' )
      .replaceAll( "'" , '&#039;' )
      .replaceAll( '\n', '<br/>'  );
}

browser.runtime.onMessage.addListener(( request, sender, sendResponse ) => {
   console.log( "request: %o", request );
   if( request.action === "rename" ) {
      browser.runtime.sendNativeMessage(
         "pap.pdf.analysis", {
            action: "rename",
            path  : request.path,
            name  : request.name
         });
      sendResponse({ response: "OK" });
   }
   else {
      sendResponse({ response: `KO, unknown action ${request.action}` });
   }
});

browser.messageDisplayAction.onClicked.addListener( async( tab, info ) => {
   const messageHeader = await browser.messageDisplay.getDisplayedMessage( tab.id );
   const attachements  = await browser.messages.listAttachments( messageHeader.id );
   // S'il n'y a qu'une seule pièce-jointe
   if( attachements.length > 0 ) {
      // On extrait l'adresse e-mail de la fédération concernée
      const federation = await getFederationAddress( messageHeader.id );
      if( federation ) {
         try {
            for( const attachement of attachements ) {
               const ext = attachement.name.slice( -4 ).toLowerCase();
               if( ext == ".pdf" ) {
                  // On enregistre la pièce-jointe dans le répertoire de téléchargement de Thunderbird
                  const file = await browser.messages.getAttachmentFile( messageHeader.id, attachement.partName );
                  const url  = URL.createObjectURL( file );
                  const id   = await browser.downloads.download({
                     url: url,
                     filename: file.name,
                     conflictAction: "overwrite",
                     saveAs: false
                  });
                  const downloaded = await browser.downloads.search({id: id});
                  const path       = downloaded[0].filename;
                  // On lance l'OCR tesseract sur l'image produite à partir du PDF
                  const info = await browser.runtime.sendNativeMessage(
                     "pap.pdf.analysis", {
                        action: "extract-text",
                        path  : path
                     });
                  // On affiche un dialogue avec les informations collectées
                  await browser.windows.create({
                     url   : "view/page.html",
                     type  : "popup",
                     width : 1200,
                     height:  900
                  });
                  const tab  = await browser.tabs.query({title: "Protocole d'Accord Pré-électoral"});
                  const code =
                    `document.getElementById( "path"       ).value     = "${escapeTextForHtml( path )}";
                     document.getElementById( "name"       ).value     = "${escapeTextForHtml( info.date + '_' + info.name )}";
                     document.getElementById( "date"       ).value     = "${escapeTextForHtml( info.timestamp )}";
                     document.getElementById( "place"      ).value     = "${escapeTextForHtml( info.place )}";
                     document.getElementById( "federation" ).value     = "${escapeTextForHtml( federation )}";
                     document.getElementById( "text"       ).innerHTML = "${escapeTextForHtml( info.text )}";`;
                  browser.tabs.executeScript( tab.id, {code: code});
               }
            }
         }
         catch( e ) {
            console.error( e );
         }
      }
      else {
         console.error( "On n'a pas trouvé le début du corps du message !" );
      }
   }
   else {
      console.error( "Il n'y a pas de pièce-jointe ou plus d'une !" );
   }
});
