import os
import sys
import time
import struct

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
CHUNK_SIZE_LENGTH = 4
CHUNK_TYPE_LENGTH = 4
CRC_LENGTH = 4
CHUNK_HEADER_LENGTH = CHUNK_SIZE_LENGTH + CHUNK_TYPE_LENGTH

ZTXT_CHUNK_TYPE = b'zTXt'
IHDR_CHUNK_TYPE = b'IHDR'

def extract_ztxt_chunk(png_path):
    with open(png_path, 'rb') as f:
        signature = f.read(len(PNG_SIGNATURE))
        if signature != PNG_SIGNATURE:
            print('Error: Invalid PNG file')
            return

        while True:
            chunk_size_bytes = f.read(CHUNK_SIZE_LENGTH)
            if not chunk_size_bytes:
                break

            chunk_size = struct.unpack('!I', chunk_size_bytes)[0]
            chunk_type = f.read(CHUNK_TYPE_LENGTH)

            if chunk_type == ZTXT_CHUNK_TYPE:
                chunk_data = f.read(chunk_size+CRC_LENGTH)
                return (chunk_size_bytes, chunk_type, chunk_data)

            f.seek(chunk_size + CRC_LENGTH, os.SEEK_CUR)

    print('Error: zTXt chunk not found in the PNG')
    return

def insert_ztxt_chunk(dmi_path, png_path, ztxt_chunk_data):


    with open(png_path, 'rb') as f_in, open(dmi_path, 'wb') as f_out:
        signature = f_in.read(len(PNG_SIGNATURE))
        if signature != PNG_SIGNATURE:
            print('Error: Invalid PNG file')
            return False

        f_out.write(signature)

        wrote_ztxt = False

        while True:
            chunk_size_bytes = f_in.read(CHUNK_SIZE_LENGTH)
            if not chunk_size_bytes:
                break

            chunk_size = struct.unpack('!I', chunk_size_bytes)[0]
            chunk_type = f_in.read(CHUNK_TYPE_LENGTH)

            if chunk_type == ZTXT_CHUNK_TYPE:
                f_in.seek(chunk_size + CRC_LENGTH, os.SEEK_CUR)
                continue
            f_out.write(chunk_size_bytes)
            f_out.write(chunk_type)
            chunk_data = f_in.read(chunk_size + CRC_LENGTH)
            f_out.write(chunk_data)
            if chunk_type == IHDR_CHUNK_TYPE:
                f_out.write(ztxt_chunk_data[0])
                f_out.write(ztxt_chunk_data[1])
                f_out.write(ztxt_chunk_data[2])

    return True

def watch_for_edits(dmi_path):
    if not dmi_path.endswith(".dmi"):
        print("That's not a .dmi file, exiting...")
        exit(1)
    png_path = dmi_path.replace(".dmi", ".png")
    try:
        with open(dmi_path, 'rb') as f_in, open(png_path, 'wb') as f_out:
            f_out.write(f_in.read())
    except FileNotFoundError:
        print("File not found: %s" % dmi_path)
        exit(1)

    last_modified = os.path.getmtime(png_path)

    ztxt_chunk_data = extract_ztxt_chunk(png_path)
    if not ztxt_chunk_data:
        exit(1)

    print("zTXt chunk length: %d" % len(ztxt_chunk_data[2]))
    print("Extracted zTXt successfully, watching...")

    try:
        while True:
            time.sleep(1)
            modified = os.path.getmtime(png_path)

            if modified > last_modified:
                print('PNG file modified')

                if insert_ztxt_chunk(dmi_path, png_path, ztxt_chunk_data):
                    print('zTXt chunk inserted back into the DMI')
                else:
                    print('Error: Failed to insert zTXt chunk')

                last_modified = modified
    except KeyboardInterrupt:
        print("Exiting...")
        os.remove(png_path)
        sys.exit(0)

if __name__ == '__main__':
    png_path = ""

    if len(sys.argv) >= 2:
        png_path = sys.argv[1]

    while (not png_path or not os.path.exists(png_path)):
        png_path = input("DMI Path: ")
    watch_for_edits(png_path)
