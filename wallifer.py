from PIL import Image
import os
import json
import waiter
import shutil
    
global_possible_states = list(range(16)) + [21, 23, 29, 31, 38, 39, 46, 47, 55, 63, 74, 75, 78, 79, 95, 110, 111, 127, 137, 139, 141, 143, 157, 159, 175, 191, 203, 207, 223, 239, 255]

def handle_shit(png_path, dmi_path, name):
    with open("data/output.json", 'r') as file:
        data = json.load(file)

    source_image = Image.open(png_path)
    source_image = source_image.convert('RGBA') # conversion to RGBA
    SourcePixels = source_image.load()

    center = (15, 4) # really 15, 4, but i needed some alterations
    size = (32, 32)
    amounts = [
        (range(center[0]+1), range(center[1]+1)),
        (range(center[0]+1), range(center[1]+1, size[1])),
        (range(center[0]+1, size[0]), range(center[1]+1, size[1])),
        (range(center[0]+1, size[0]), range(center[1]+1)),
    ]

    global_offsets = {
        1: (0, 0),
        2: (32, 0),
        3: (64, 0),
        4: (0, 32),
        5: (32, 32)
    }

    dmi_file = Image.open(dmi_path)
    dmi_file = dmi_file.convert('RGBA') # conversion to RGBA
    # DMI_pixels = dmi_file.load()

    size_of_input = tuple([dmi_file.size[0] // 32, dmi_file.size[1] // 32])
    # total_idx = (size_of_input[0] * size_of_input[1]) - 1

    # final_idx = 0

    img = Image.new('RGBA', (dmi_file.size[0], int(dmi_file.size[1]*1.5)))
    # img = img.convert('RGBA') # conversion to RGBA
    PixelsFinal = img.load()

    for idx, state in enumerate(global_possible_states):
        target_offset = data[str(state)]

        state_x_offset = (idx % size_of_input[0]) * 32
        state_y_offset = (idx // size_of_input[1]) * 48

        # get_sprite(SourcePixels, target_offset, state)
        for areas, our_offset in zip(amounts, target_offset):
            for i in areas[0]:
                input_x = i + global_offsets[our_offset][0]
                output_x = i + state_x_offset
                for j in areas[1]:
                    input_y = j + global_offsets[our_offset][1]
                    output_y = j + state_y_offset + 16
                    PixelsFinal[output_x,output_y] = SourcePixels[input_x,input_y]

        # final_idx = idx

    # This used to handle fake sliding walls, but we had to ditch it because it broke when we changed to 32x48
    # new_idx = final_idx + 1
    # while (new_idx < total_idx):
    #     state_x_offset = (new_idx % size_of_input[0]) * 32
    #     state_y_offset = (new_idx // size_of_input[1]) * 32
    #     for i in range(32):
    #         i += state_x_offset
    #         for j in range(32):
    #             j += state_y_offset
    #             PixelsFinal[i,j] = DMI_pixels[i,j]

    #     new_idx += 1

    # img.text = dmi_file.text
    output_file = f"./output/{name}.png"
    img.save(output_file)
    img.close()

    keyword, text = waiter.extract_keyword_text(dmi_path)
    text = text.replace("height = 32", "height = 48")
    reecoded_chunk_data = waiter.encode_ztxt(keyword, text)
    new_file_path = os.path.splitext(output_file)[0] + ".dmi"
    shutil.copy2(output_file, new_file_path)
    waiter.insert_ztxt_chunk(new_file_path, output_file, reecoded_chunk_data) # fun fact, PIL can't write zTXt :)

    os.remove(output_file)

def begin(wall_folder):
    local_folder = "./input"

    available_dmis = [os.path.splitext(f)[0] for f in os.listdir(wall_folder) if os.path.isfile(os.path.join(wall_folder, f))]
    available_pngs = [os.path.splitext(f)[0] for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]

    print(matching_files := set(available_dmis).intersection(available_pngs))

    for match in matching_files:
        
        png_path = os.path.join(local_folder, f"{match}.png")
        dmi_path = os.path.join(wall_folder, f"{match}.dmi")

        handle_shit(png_path, dmi_path, match)

if __name__ == "__main__":
    # reset_bases()

    # CHANGE THIS PATH TO THE PATH OF YOUR PARADISE WALLS FOLDER
    wall_folder = r"C:\Users\YOUR_USERNAME\Documents\github\Paradise\icons\turf\walls"
    begin(wall_folder)
