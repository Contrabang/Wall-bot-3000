import os
import sys
import time
import struct
import zlib
import tempfile
import shutil

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
CHUNK_SIZE_LENGTH = 4
CHUNK_TYPE_LENGTH = 4
CRC_LENGTH = 4
CHUNK_HEADER_LENGTH = CHUNK_SIZE_LENGTH + CHUNK_TYPE_LENGTH

ZTXT_CHUNK_TYPE = b'zTXt'
IHDR_CHUNK_TYPE = b'IHDR'

def extract_keyword_text(png_path):
    return decode_ztxt(extract_ztxt_chunk(png_path)[2])

def insert_keyword_text(png_path, keyword, text):
    replace_ztxt_chunk(png_path, encode_ztxt(keyword, text))

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

            chunk_size = struct.unpack('!I', chunk_size_bytes)[0] # network (big endian), unsigned int
            chunk_type = f.read(CHUNK_TYPE_LENGTH)

            if chunk_type == ZTXT_CHUNK_TYPE:
                chunk_data = f.read(chunk_size+CRC_LENGTH)
                # chunk_data = keyword, text, crc
                return (chunk_size_bytes, chunk_type, chunk_data)

            f.seek(chunk_size + CRC_LENGTH, os.SEEK_CUR)

    print('Error: zTXt chunk not found in the PNG')
    return

def decode_ztxt(chunk_data):
    # Find the null separator to split the keyword and the compressed text
    null_separator_index = chunk_data.find(b'\x00')
    if null_separator_index == -1:
        raise ValueError("Invalid zTXT chunk: No null separator found")
    
    # Extract the keyword
    keyword = chunk_data[:null_separator_index].decode('latin-1')
    
    # The compression method is the byte right after the null separator
    compression_method = chunk_data[null_separator_index + 1]
    if compression_method != 0:
        raise ValueError("Unsupported compression method: {}".format(compression_method))
    
    # The rest is the compressed text data
    compressed_text_data = chunk_data[null_separator_index + 2:]
    
    # Decompress the text data using zlib. Automatically discards the CRC.
    decompressed_text_data = zlib.decompress(compressed_text_data)
    
    # Decode the decompressed text to a string
    text = decompressed_text_data.decode('latin-1')
    
    return keyword, text

def __keyword_text_to_bytes(keyword, text):
    if '\x00' in keyword:
        raise ValueError("Keyword cannot contain null character (\\x00)")
    
    # Compress the text data using zlib
    compressed_text_data = zlib.compress(text.encode('latin-1'))
    
    # Construct the zTXT chunk data
    chunk_data = bytearray()
    chunk_data.extend(keyword.encode('latin-1'))
    chunk_data.append(0)  # Null separator
    chunk_data.append(0)  # Compression method (0 for zlib)
    chunk_data.extend(compressed_text_data)
    
    return bytes(chunk_data)

def encode_ztxt(keyword: str, text: str):
    encoded = __keyword_text_to_bytes(keyword, text)
    chunk_size_bytes = struct.pack("!I", len(encoded)) # but the size of the data only includes encoded, not chunk type
    chunk_type = ZTXT_CHUNK_TYPE
    new_crc = struct.pack('!I', zlib.crc32(chunk_type+encoded)) # Yes, CRC includs chunk type but not chunk size
    chunk_data = bytes(encoded + new_crc)

    return (chunk_size_bytes, chunk_type, chunk_data)

def replace_ztxt_chunk(dmi_path, ztxt_chunk_data):
    # ztxt_chunk_data = list(chunk_size_bytes, chunk_type, chunk_data)
    # chunk_data = keyword, text, crc
    
    with open(dmi_path, 'rb') as f_in:
        buffer = tempfile.TemporaryFile()
        shutil.copyfileobj(f_in, buffer)
        buffer.seek(0)

    with open(dmi_path, 'wb') as f_out:
        signature = buffer.read(len(PNG_SIGNATURE))
        if signature != PNG_SIGNATURE:
            print('Error: Invalid PNG file')
            return False
        f_out.write(signature)

        while True:
            chunk_size_bytes = buffer.read(CHUNK_SIZE_LENGTH)
            if not chunk_size_bytes:
                break

            chunk_size = struct.unpack('!I', chunk_size_bytes)[0] # network (big endian), unsigned int
            chunk_type = buffer.read(CHUNK_TYPE_LENGTH)

            if chunk_type == ZTXT_CHUNK_TYPE:
                buffer.seek(chunk_size + CRC_LENGTH, os.SEEK_CUR)
                continue
            f_out.write(chunk_size_bytes)
            f_out.write(chunk_type)
            chunk_data = buffer.read(chunk_size + CRC_LENGTH)
            f_out.write(chunk_data)
            if chunk_type == IHDR_CHUNK_TYPE:
                f_out.write(ztxt_chunk_data[0])
                f_out.write(ztxt_chunk_data[1])
                f_out.write(ztxt_chunk_data[2])
    return True

def _insert_ztxt_chunk(dmi_path, png_path, ztxt_chunk_data):
    # its not advised to usee this outside of this file, use replace_ztxt_chunk instead
    with open(png_path, 'rb') as f_in, open(dmi_path, 'wb') as f_out:
        signature = f_in.read(len(PNG_SIGNATURE))
        if signature != PNG_SIGNATURE:
            print('Error: Invalid PNG file')
            return False

        f_out.write(signature)

        while True:
            chunk_size_bytes = f_in.read(CHUNK_SIZE_LENGTH)
            if not chunk_size_bytes:
                break

            chunk_size = struct.unpack('!I', chunk_size_bytes)[0] # network (big endian), unsigned int
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

                if _insert_ztxt_chunk(dmi_path, png_path, ztxt_chunk_data):
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
