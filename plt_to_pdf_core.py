import sys
import os
import re
import time
import fitz  # PyMuPDF 核心矢量画布引擎

def perfect_plt_to_pdf(plt_path):
    """核心转换引擎（之前拖拽完美出图的那个版本，原封不动复活）"""
    if not os.path.exists(plt_path):
        return False
    
    # 稳一手，防止文件还在复制中就被读取
    time.sleep(0.5)

    try:
        with open(plt_path, 'r', encoding='utf-8', errors='ignore') as f:
            plt_content = f.read()

        # 提取所有的 HPGL 标准工业指令
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

        # 服装绘图仪标准单位换算
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

        # 极致纤细纯黑线
        shape.finish(color=(0, 0, 0), width=0.25)
        shape.commit()
        
        pdf_path = os.path.splitext(plt_path)[0] + ".pdf"
        doc.save(pdf_path)
        doc.close()
        print(f"【⚡成功】已转换生成 PDF: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"【异常】{str(e)}")
        return False

def start_folder_monitor(folder_path):
    """强力雷达监控机制（完全独立，不干扰拖拽）"""
    print(f"==================================================")
    print(f"🤖 服装纸样【全自动雷达】已重新上线...")
    print(f"📂 正在监视文件夹: {folder_path}")
    print(f"💡 只要有新 PLT 文件落入，PDF 将自动秒出")
    print(f"==================================================")
    
    while True:
        try:
            time.sleep(1.0)
            all_files = os.listdir(folder_path)
            
            for file_name in all_files:
                if file_name.lower().endswith('.plt'):
                    base_name = os.path.splitext(file_name)[0]
                    pdf_name = base_name + ".pdf"
                    
                    # 只要文件夹里缺这个 PDF，立刻强制抓取转换
                    if pdf_name not in all_files:
                        full_plt_path = os.path.join(folder_path, file_name)
                        perfect_plt_to_pdf(full_plt_path)
                        
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(2.0)

if __name__ == '__main__':
    # 🔒 还原最纯净的单文件接收逻辑，绝不干涉 Windows 默认的拖拽参数传递
    if len(sys.argv) > 1:
        perfect_plt_to_pdf(sys.argv[1])
    else:
        # 如果双击直接运行，则自动监控软件所在文件夹
        current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        start_folder_monitor(current_dir)
