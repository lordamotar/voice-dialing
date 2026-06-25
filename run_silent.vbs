Set WshShell = CreateObject("WScript.Shell")
currentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run "cmd /c run_app.bat", 0, False
Set WshShell = Nothing
