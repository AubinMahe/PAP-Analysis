# Protocole d'Accord Préélectoral

Les employeurs invitent les organisations syndicales à des réunions de négociation du Protocole d'Accord Préélectoral (PAP).

On cherche à obtenir les informations suivantes à partir de ces courriers :

- L'adresse
- La date
- L'heure

Reçu par mail, ce courrier est un PDF généré par une imprimante qui prend en photo la ou les pages et les agrège dans un document PDF, sans structure.

La forme des couriers varie énormément, les tournures de phrases sont complètement différente d'un employeur à l'autre.

## Solutions et outils

On souhaite développer un outil intégré à Thunderbird (extension XPI), qui, après extraction de la pièce jointe, pilote l'analyse de son contenu par ChatGPT d'OpenAI en vue de générer une synthèse affichée dans une fenêtre dédiée, au format HTML, facilitant le copier-coller vers Excel.

La première partie est développée en JavaScript et épouse les standards de développement des extensions Thunderbird.

La seconde est un script Python 3 qui pilote ChatGPT d'OpenAI, qui travaille à partir de texte brut ; l'OCR "Tesseract" est donc utilisé, dans sa déclinaison Python pour transformer des images en texte. Tesseract prend en entrée une ou plusieurs images, il est donc nécessaire d'extraire les images du PDF, la librairie python pdf2image est utilisée à cette fin.

             +-----------+             +-------------+             +--------+
    (PDF) -->| pdf2image |--> (PNG) -->| pytesseract |--> (TXT) -->| OpenAI |--> (JSON)
             +-----------+             +-------------+             +--------+

## Configuration

Le fichier `pap.pdf.analysis.json` doit être placé dans le dossier `${HOME}/.mozilla/native-messaging-hosts/`.
C'est lui qui fait le lien entre l'extension Thunderbird et le scrip Python `analyse.py`.

## Délivrable

Le fichier `pap.xpi`, produit par le script `build-xpi.sh`.
