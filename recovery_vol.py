import os
import shutil
from typing import List, Tuple

class ImageRecovery:
    """
    Class để phục hồi các file ảnh từ volume file
    SIGNATURES: Các định dạng file ảnh được hỗ trợ
    DELETED_MARKER: Byte đánh dấu file đã bị xóa
    ENTRY_SIZE: Kích thước của mỗi entry trong FAT directory

    """
    SIGNATURES = {
        'jpg': {
            'header': b'\xff\xd8\xff',
            'footer': b'\xff\xd9'
        },
        'png': {
            'header': b'\x89PNG\r\n\x1a\n',
            'footer': b'IEND\xaeB`\x82'
        }
    }
    
    DELETED_MARKER = 0xE5
    ENTRY_SIZE = 32


    def __init__(self, volume_path: str, output_dir: str):
        """
        Hàm khởi tạo
        volume_path: Đường dẫn tới volume file
        output_dir: Thư mục chứa các file ảnh được phục hồi
        """
        if not os.path.exists(volume_path):
            raise FileNotFoundError(f"Volume file not found: {volume_path}")
        
        self.volume_path = volume_path
        self.output_dir = output_dir
        self.clear_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        
    def clear_output_dir(self):
        """Xóa toàn bộ file trong thư mục output nếu tồn tại"""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
    def find_original_filename(self, volume_data: bytes, start_pos: int, ext: str) -> str:
        search_start = max(0, start_pos - 10000)
        """
        Tìm tên file gốc của file ảnh
        volume_data: Dữ liệu của volume file
        start_pos: Vị trí bắt đầu của file ảnh (byte đầu tiên của header)
        ext: Phần mở rộng của file
        Nếu tồn tại thì return tên file gốc + ext
        Nếu không tồn tại thì return recovered_{start_pos}{ext}
        """
        
        for pos in range(search_start, start_pos):
            if pos + self.ENTRY_SIZE > len(volume_data):
                break
                
            entry = volume_data[pos:pos + self.ENTRY_SIZE]
            
            if entry[0] == self.DELETED_MARKER:
                try:
                    name = entry[1:8].decode('ascii', errors='ignore').rstrip()
                    file_ext = entry[8:11].decode('ascii', errors='ignore').rstrip()
                    
                    name = ''.join(c for c in name if c.isprintable())
                    file_ext = ''.join(c for c in file_ext if c.isprintable())
                    
                    if file_ext.lower() == ext[1:].lower() and name:
                        return f"{name}{ext}"
                except UnicodeDecodeError:
                    continue
        
        return f"recovered_{start_pos}{ext}"

    def find_all_images(self, data: bytes) -> List[Tuple[int, int, str]]:
        """
        Tìm tất cả các file ảnh trong volume file
        data: Dữ liệu của volume file
        Return: Danh sách các tuple (start_pos, end_pos, ext) của các file ảnh
        """
        image_blocks = []
        
        for ext, signatures in self.SIGNATURES.items():
            header = signatures['header']
            footer = signatures['footer']
            
            start_pos = 0
            while True:
                start_pos = data.find(header, start_pos)
                if start_pos == -1:
                    break
                
                end_pos = data.find(footer, start_pos)
                if end_pos != -1:
                    end_pos += len(footer)
                    image_blocks.append((start_pos, end_pos, f".{ext}"))
                
                start_pos += 1
        
        return sorted(image_blocks)

    def recover_images(self) -> int:
        """
        Phục hồi các file ảnh từ volume file
        Return: Số lượng file ảnh phục hồi được
        """
        try:
            with open(self.volume_path, 'rb') as f:
                volume_data = f.read()
        except IOError as e:
            print(f"Error reading volume: {e}")
            return 0

        image_blocks = self.find_all_images(volume_data)
        recovered_count = 0

        for start, end, ext in image_blocks:
            try:
                image_data = volume_data[start:end]
                filename = self.find_original_filename(volume_data, start, ext)
                
                base, ext = os.path.splitext(os.path.join(self.output_dir, filename))
                output_path = f"{base}{ext}"
                counter = 1
                
                while os.path.exists(output_path):
                    output_path = f"{base}_{counter}{ext}"
                    counter += 1

                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                recovered_count += 1
                print(f"Recovered: {os.path.basename(output_path)}")
                
            except Exception as e:
                print(f"Error recovering image at position {start}: {e}")
                continue

        return recovered_count

def main():
    try:
        volume_path = 'Image00.vol'
        # Thư mục chứa các file ảnh được phục hồi
        output_dir = 'recovered_images'
        
        recovery = ImageRecovery(volume_path, output_dir)
        count = recovery.recover_images()
        
        print(f"\nRecovery complete. Recovered {count} images.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()