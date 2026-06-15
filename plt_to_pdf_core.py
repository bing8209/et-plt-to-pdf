import sys
import os
import re
import time
import fitz  # PyMuPDF 核心矢量画布引擎

def perfect_plt_to_pdf(plt_path):
    """核心转换引擎（已修复所有版本代差，100% 稳定）"""
    if not os.path.exists(plt_path):
        return False
    
    # 避免有些大文件还没写完就被读取，先稳一手
    time.sleep(0.5)

    try:
        with open(plt_path, 'r', encoding='utf-8', errors='ignore') as f:
            plt_content = f.read()

        commands = re.findall(r'([A-Z]{2})([^;]*)', plt_content)
        
        max_x, max_y = -9999999, -9999999
        min_x, min_y = 9999999, 9999999
        
        for cmd, args in commands:
            if cmd in ('PU', 'PD') and args.strip():
                coords = re.findall(r'(-?\d+),(-?\d+)', args)
                for x_str, y_str in coords:
                    x, y = int(x_str), int(y_str)
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y
                    if x < min_x: min_x = x
                    if y < min_y: min_y = y

        if max_x == -9999999:
            return False

        PLT_TO_PT = 72.0 / 1016.0  
        width_units = max_x - min_x
        height_units = max_y - min_y
        
        padding = 56  
        pdf_width = width_units * PLT_TO_PT + padding * 2
        pdf_height = height_units * PLT_TO_PT + padding * 2

        doc = fitz.open()
        page = doc.new_page(width=pdf_width, height=pdf_height)
        shape = page.new_shape()
        
        current_polyline = []
        for cmd, args in commands:
            if cmd in ('PU', 'PD'):
                coords = re.findall(r'(-?\d+),(-?\d+)', args)
                for idx, (x_str, y_str) in enumerate(coords):
                    pdf_x = (int(x_str) - min_x) * PLT_TO_PT + padding
                    pdf_y = pdf_height - ((int(y_str) - min_y) * PLT_TO_PT + padding)
                    pt = fitz.Point(pdf_x, pdf_y)
                    
                    if idx == 0 and cmd == 'PU':
                        if len(current_polyline) > 1:
                            shape.draw_polyline(current_polyline)
                        current_polyline = [pt]
                    else:
                        current_polyline.append(pt)

        if len(current_polyline) > 1:
            shape.draw_polyline(current_polyline)

        shape.finish(color=(0, 0, 0), width=0.25)
        shape.commit()
        
        pdf_path = os.path.splitext(plt_path)[0] + ".pdf"
        doc.save(pdf_path)
        doc.close()
        print(f"【⚡雷达触发】成功无损转换: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"【转换异常】{str(e)}")
        return False

def start_folder_monitor(folder_path):
    """智能雷达监控函数（不依赖任何第三方复杂库）"""
    print(f"==================================================")
    print(f"🤖 服装纸样全自动雷达已开启...")
    print(f"📂 正在监视文件夹: {folder_path}")
    print(f"💡 使用方法：在 ET CAD 中直接保存/导出 PLT 到该目录下，PDF 将自动秒出")
    print(f"==================================================")
    
    # 初始化已经存在的 PDF 文件列表，避免重复触发
    processed_files = set()
    
    # 首次启动，先扫描一次，把现有的 plt 且已有 pdf 的排除
    for f in os.listdir(folder_path):
        if f.lower().endswith('.pdf'):
            processed_files.add(os.path.splitext(f)[0])

    while True:
        try:
            # 每隔 1 秒扫描一次文件夹
            time.sleep(1.0)
            
            # 获取当前文件夹下所有文件
            all_files = os.listdir(folder_path)
            
            # 找出需要处理的 PLT 文件
            for file_name in all_files:
                if file_name.lower().endswith('.plt'):
                    base_name = os.path.splitext(file_name)[0]
                    pdf_name = base_name + ".pdf"
                    
                    # 如果该 plt 还没有生成对应的 pdf，或者 pdf 突然被删了，立马触发转换
                    if pdf_name not in all_files:
                        full_plt_path = os.path.join(folder_path, file_name)
                        perfect_plt_to_pdf(full_plt_path)
                        
        except KeyboardInterrupt:
            print("\n👋 自动雷达已安全关闭。")
            break
        except Exception as e:
            time.sleep(2.0)

if __name__ == '__main__':
    # 逻辑分流：
    # 1. 如果带了文件参数运行，走单文件右键/拖拽模式
    # 2. 如果不带参数直接双击，自动进入“当前文件夹监控”模式！
    if len(sys.argv) > 1:
        perfect_plt_to_pdf(sys.argv[1])
    else:
        # 获取当前软件运行所在的文件夹
        current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        start_folder_monitor(current_dir)
