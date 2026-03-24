import ezdxf
doc = ezdxf.readfile('output_pages/上部T梁第11页_6-1-6-3.dxf')
msp = doc.modelspace()
for e in msp:
    if e.dxftype() in ['MTEXT', 'TEXT']:
        text = e.dxf.text if e.dxftype() == 'TEXT' else e.text
        if '蜂窝' in text or '麻面' in text:
            print(f"文本: {text}")
            print(f"位置: ({e.dxf.insert[0]:.2f}, {e.dxf.insert[1]:.2f})")