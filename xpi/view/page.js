function rename_PDF_file() {
   const path = document.getElementById( "path" ).value;
   const name = document.getElementById( "name" ).value;
   browser.runtime.sendMessage(
      "pap.analysis@hpms.org",
      {
         action: "rename",
         path  : path,
         name  : name,
      }
   ).then(
      nfo => {console.log  ( nfo )},
      err => {console.error( err )}
   );
}

document.getElementById( "rename-btn" ).addEventListener('click', e => rename_PDF_file());
