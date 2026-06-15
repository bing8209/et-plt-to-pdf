import sys
import os
import re
import time
import fitz  # PyMuPDF 核心矢量画布引擎

def perfect_plt_to_pdf(plt_path):
    """核心转换引擎（100% 稳定出图）"""
    if not os.path.exists(plt_path):
        return False
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
        print(f"【⚡成功】已转换生成 PDF: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"【异常】{str(e)}")
        return False

def clean_old_files(folder_path, days=30):
    """【新功能】安全清理函数：只自动删除超过指定天数未修改的旧图纸"""
    now_time = time.time()
    # 30天的秒数 = 30天 * 24小时 * 60分钟 * 60秒
    seconds_threshold = days * 24 * 60 * 60 
    
    try:
        all_files = os.listdir(folder_path)
        for file_name in all_files:
            # 只清理排料图(.plt)和转换出的纸样(.pdf)
            if file_name.lower().endswith(('.plt', '.pdf')):
                full_path = os.path.join(folder_path, file_name)
                
                # 获取文件的最后修改时间
                file_modify_time = os.path.getmtime(full_path)
                
                # 如果这个文件已经躺在这里超过30天没有动过了，直接执行工业安全蒸发
                if (now_time - file_modify_time) > seconds_threshold:
                    os.remove(full_path)
                    print(f"【🧹自动保洁】已自动安全清理30天前的老旧文件: {file_name}")
    except Exception as e:
        print(f"【保洁异常】清理旧文件时出错: {str(e)}")

def start_folder_monitor(folder_path):
    """升级版雷达：兼顾自动转换与定时清理解析"""
    print(f"==================================================")
    print(f"🤖 服装纸样【全自动雷达 + 30天自动保洁】已全面开启...")
    print(f"📂 正在监视文件夹: {folder_path}")
    print(f"⏱️  每隔 1 小时会自动巡检并清理超过 30 天的旧纸样")
    print(f"==================================================")
    
    # 记录上一次清理的时间戳
    last_clean_time = 0
    
    while True:
        try:
            # 每隔 1 秒进行高频扫描，确保拖入文件立马秒出
            time.sleep(1.0)
            current_time = time.time()
            
            # 🔒 【保洁触发器】：每隔 1 小时（3600秒）在后台默默执行一次文件大扫除
            if current_time - last_clean_time > 3600:
                clean_old_files(folder_path, days=30)
                last_clean_time = current_time
            
            all_files = os.listdir(folder_path)
            for file_name in all_files:
                if file_name.lower().endswith('.plt'):
                    base_name = os.path.splitext(file_name)[0]
                    pdf_name = base_name + ".pdf"
                    
                    if pdf_name not in all_files:
                        full_plt_path = os.path.join(folder_path, file_name)
                        perfect_plt_to_pdf(full_plt_path)
                        
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(2.0)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        perfect_plt_to_pdf(sys.argv[1])
    else:
        current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        start_folder_monitor(current_dir)
