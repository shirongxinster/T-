# -*- coding: utf-8 -*-
from bridge_disease_parser import parse_excel
import os

excel_path = 'K572+774红石牡丹江大桥（右幅）病害.xls'
if os.path.exists(excel_path):
    data = parse_excel(excel_path)
    print('桥梁名称:', repr(data.get('bridge_name', '')))
    print('路线名称:', repr(data.get('route_name', '')))
