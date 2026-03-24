from bridge_disease_parser import parse_excel
data = parse_excel('K572+774红石牡丹江大桥（右幅）病害.xls')
for part in data['parts']:
    if '上部' in part['name']:
        for comp_id, records in part['grouped_data'].items():
            if '6-1' in comp_id:
                print(f'{comp_id}:')
                for r in records:
                    print(f'  病害类型: [{r.get("病害类型")}]')