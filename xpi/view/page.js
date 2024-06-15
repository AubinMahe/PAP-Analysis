function rename_PDF_file() {
   browser.runtime.sendMessage(
      "pap.analysis@hpms.org",
      {
         action: "rename",
         name  : document.getElementById( "name" ).value
      }
   ).then(
      nfo => {console.log  ( nfo )},
      err => {console.error( err )}
   );
}

document.getElementById( "rename-btn" ).addEventListener('click', e => rename_PDF_file());
