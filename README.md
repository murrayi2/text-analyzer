# text-analyzer
Reads in xml text message data and uses NLP tools to discover patterns between your contacts.

## Android
Text data xml file generated with the "SMS Backup & Restore" app on the Google Play Store.

## iOS 11 or later
1) Create an unencrypted backup of your iPhone via iTunes (don't select "Encrypt local backup" on the device summary screen)
2) Go to ```~/Library/Application Support/MobileSync/Backup``` and click in to the most recent folder in that directory
3) Find the file named ```3d0d7e5fb2ce288813306e4d4636395e047a3d28```, copy it to this directory, and rename it ```messages.db```
4) Back in the same backup directory, find the file named ```31bb7ba8914766d4ba40d6dfb6113c8b614be442```, copy it to this directory, and rename it ```contacts.db```
5) run ```python sql_to_xml.py``` to generate the xml file needed for the analyzer
