# How to use/play
You can find both excecutables inside the 'dir' folder, however, if sounds or game logic is not working, excecute the 'main.py' file directly to play (normally using a compatible python launcher and having pygame & pip installed).

** Since 'dir' folder is not available to to its large size, to make it into an excecutable, change the directory towards the 'main.py' file location, then input this command into the terminal:


MacOS\n
pyinstaller --onefile --windowed --add-data "sounds:sounds" main.py


Windows\n
pyinstaller --onefile --windowed --add-data "sounds;sounds" main.py
