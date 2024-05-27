Get-ChildItem -Recurse -Path .\src_html\glas\* -Include index.html | ForEach-Object { 
	& C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/page_content.py --src $_.FullName
}

# Get-ChildItem -Recurse -Path .\src_html\glas\page-87\* -Include index.html | ForEach-Object { 
#     & C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/page_content.py --src $_.FullName
# }

# generate main navbar/footer
& C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/generate_main.py

# generate content of main
& C:/Users/choosegoose/.virtualenvs/html_to_tscn-UVkTTcz6/Scripts/python.exe c:/code/html_to_tscn/generate_home_content.py --src '.\src_html\wizard woes.html'

Copy-Item -r -Force .\godot_output\* C:\code\godot-projects\wizardwoes 
Copy-Item -r -force C:\code\godot-projects\wizardwoes\glas\glas\* C:\code\godot-projects\wizardwoes\glas
