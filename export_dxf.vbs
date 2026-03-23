'*- coding: utf-8 -*-
' 将DWG文件导出为DXF
Dim acadApp
Dim acadDoc

' 连接AutoCAD/GstarCAD
On Error Resume Next
Set acadApp = GetObject(, "GstarCAD.Application")
If Err.Number <> 0 Then
    Set acadApp = CreateObject("GstarCAD.Application")
    acadApp.Visible = True
End If

' 要导出的文件列表
Dim files(4)
files(0) = "K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\40mT梁.dwg"
files(1) = "K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\双柱墩.dwg"
files(2) = "K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\单柱墩.dwg"
files(3) = "K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\不带台身桥台.dwg"
files(4) = "K:\works\008.S2ReportAndLayoutPic\leftRealJobs_workbuddy\templates\构件\带台身桥台.dwg"

' 导出每个文件
For i = 0 To 4
    Dim dwgPath
    Dim dxfPath
    dwgPath = files(i)
    dxfPath = Replace(dwgPath, ".dwg", ".dxf", 1, -1, 1)
    
    ' 打开文件
    Set acadDoc = acadApp.Documents.Open(dwgPath)
    
    ' 导出为DXF
    acadDoc.SendCommand "-export dxf " & Chr(34) & dxfPath & Chr(34) & " "
    
    WScript.Echo "已导出: " & dxfPath
    
    acadDoc.Close False
Next

acadApp.Quit
WScript.Echo "全部完成"
