' ==============================================================================
' A TuBe Ultra HD (v1.0.1) - Silent Background Launcher (Zero Windows)
' Executes master batch launcher with window style 0 (SW_HIDE)
' ==============================================================================

Option Explicit
Dim WshShell, fso, scriptDir, batchPath

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Resolve exact absolute path relative to this script
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchPath = scriptDir & "\startapp.bat"

If fso.FileExists(batchPath) Then
    ' WindowStyle 0 = Hidden (Zero Command Prompt Windows Visible)
    ' bWaitOnReturn False = Asynchronous Detached Execution
    WshShell.CurrentDirectory = scriptDir
    WshShell.Run Chr(34) & batchPath & Chr(34), 0, False
Else
    WScript.Echo "Error: startapp.bat not found in: " & scriptDir
End If

Set WshShell = Nothing
Set fso = Nothing
