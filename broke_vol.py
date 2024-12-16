import os
import struct

def create_boot_sector():
    """Tạo ra boot sector cho volume theo kiến trúc FAT32"""
    boot_sector = bytearray(512)
    
    # Các chỉ thị của boot sector
    boot_sector[0] = 0xEB  # JMP instruction
    boot_sector[1] = 0x58  # JMP offset
    boot_sector[2] = 0x90  # NOP
    boot_sector[3:11] = b'MSDOS5.0'  # OEM Name
    
    # Tham số của khối BIOS 
    boot_sector[11:13] = (512).to_bytes(2, 'little')  # Bytes per sector
    boot_sector[13] = 8  # Sectors per cluster
    boot_sector[14:16] = (32).to_bytes(2, 'little')  # Reserved sectors
    boot_sector[16] = 2  # Number of FATs
    boot_sector[17:19] = (0).to_bytes(2, 'little')  # Root entries
    boot_sector[19:21] = (0).to_bytes(2, 'little')  # Small sectors
    boot_sector[21] = 0xF8  # Media type
    boot_sector[510:512] = b'\x55\xAA'  # Boot signature
    
    return boot_sector

def create_test_volume():
    """
    Tạo ra test volume với boot sector và một số file ảnh
    Volume có kích thước 10MB
    """
    volume_path = "Image00.vol"
    volume_size = 10 * 1024 * 1024  # 10MB

    # Tạo ra boot sector
    boot_sector = create_boot_sector()
    
    print(f"Creating volume: {volume_path}")
    with open(volume_path, 'wb') as f:
        f.write(boot_sector)
        f.write(b'\x00' * (volume_size - len(boot_sector)))

    # Danh sách các file ảnh
    image_files = [
        'images/image01.png',
        'images/image02.png',
        'images/image03.png',
        'images/image04.jpg',
        'images/image05.jpg'
    ]

    # Sao chép các file ảnh vào volume
    print("\nCopying images to volume:")

    data_offset = 512 + 4096  # Vị trí bắt đầu ghi dữ liệu sau boot sector và FAT directory

    # Mở volume để ghi dữ liệu
    with open(volume_path, 'r+b') as vol_file:
        for image_file in image_files:
            if not os.path.exists(image_file):
                print(f"Warning: {image_file} not found, skipping.")
                continue
                
            # Đọc dữ liệu từ file ảnh
            with open(image_file, 'rb') as src_file:
                image_data = src_file.read()
                
            # Ghi dữ liệu vào volume với kích thước hedader 4 bytes
            vol_file.seek(data_offset)
            size_header = len(image_data).to_bytes(4, 'little')
            vol_file.write(size_header)
            vol_file.write(image_data)
            
            # Đọc dữ liệu từ volume để kiểm tra
            vol_file.seek(data_offset + 4)
            written_data = vol_file.read(len(image_data))
            if written_data == image_data:
                print(f"Successfully wrote {image_file} ({len(image_data)} bytes)")
            else:
                print(f"Error: Failed to write {image_file}")
                
            data_offset += 4 + len(image_data)  # Cập nhật vị trí ghi dữ liệu tiếp theo
    
    # Tạo ra sự cố trên volume tương tự như khi volume bị hỏng hoặc đã bị format
    print("\nSimulating damage...")
    with open(volume_path, "r+b") as f:
        f.seek(512)  # Bắt đầu từ vị trí của FAT directory
        f.write(b'\x00' * 4096)  # Ghi dữ liệu rác vào FAT directory

if __name__ == "__main__":
    create_test_volume()