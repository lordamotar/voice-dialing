Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
currentDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

pythonwPath = currentDir & "\.venv\Scripts\pythonw.exe"
scriptPath = currentDir & "\main.py"

If FSO.FileExists(pythonwPath) Then
    WshShell.Run chr(34) & pythonwPath & chr(34) & " " & chr(34) & scriptPath & chr(34), 0, False
Else
    WshShell.Run "pythonw " & chr(34) & scriptPath & chr(34), 0, False
End If

Set WshShell = Nothing
Set FSO = Nothing
