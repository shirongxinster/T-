'*- coding: utf-8 -*-
' 将病害图例DWG文件导出为DXF
Dim acadApp
Dim acadDoc

On Error Resume Next
Set acadApp = GetObject(, "GstarCAD.Application")
If Err.Number <> 0 Then
    Set acadApp = CreateObject("GstarCAD.Application")
    acadApp.Visible = True
End If

' 获取病害图例文件夹中的所有DWG文件
Dim fso, folder, files, file
Set fso = CreateObject("Scripting.FileSystemObject")
Set folder = fso.GetFolder("K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\病害图例")

For Each file In folder.Files
    If LCase(fso.GetExtensionName(file.Name)) = "dwg" Then
        Dim dwgPath
        Dim dxfPath
        dwgPath = file.Path
        dxfPath = Replace(dwgPath, ".dwg", ".dxf", 1, -1, 1)
        
        ' 打开文件
        Set acadDoc = acadApp.Documents.Open(dwgPath)
        
        ' 导出为DXF - 使用正确的命令格式
        acadDoc.SendCommand "-export dxf " & Chr(34) & dxfPath & Chr(34) & vbCr
        
        WScript.Echo "已导出: " & file.Name
        
        acadDoc.Close False
    End If
Next

acadApp.Quit
WScript.Echo "病害图例导出完成"
