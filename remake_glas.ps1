Get-ChildItem -Recurse -Path .\src_html\glas\* -Include index.html | ForEach-Object { Write-Output & C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/page_content.py --src $_.FullName }
# & C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/generate_main.py

Copy-Item -r -Force .\godot_output\* C:\code\godot-projects\wizardwoes 
Copy-Item -r -force C:\code\godot-projects\wizardwoes\glas\glas\* C:\code\godot-projects\wizardwoes\glas
