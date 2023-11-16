from PIL import Image
import json
    
global_possible_states = list(range(16)) + [21, 23, 29, 31, 38, 39, 46, 47, 55, 63, 74, 75, 78, 79, 95, 110, 111, 127, 137, 139, 141, 143, 157, 159, 175, 191, 203, 207, 223, 239, 255]

def reset_bases():
    # Bits of an 8-bit number follow this order
    # NW, SW, SE, NE, W, E, S, N
    # 0-15 represent ones with non-diagonals

    binary_targets = [bin(num)[2:].zfill(8) for num in global_possible_states]

    # NW - 1001
    # both = 4
    # else or with 0011 = 2
    # else or with 1100 = 3

    # NW, SW, SE, NE
    diagonal_masks = ["1001", "1010", "0110", "0101"]

    results = {}
    for idx, number in enumerate(binary_targets):
        results[global_possible_states[idx]] = []
        for quarter in range(4):
            if number[quarter] == "1":
                results[global_possible_states[idx]].append(5)
            elif(int(number[4:], 2) & int(diagonal_masks[quarter], 2) == int(diagonal_masks[quarter], 2)):
                results[global_possible_states[idx]].append(4)
            elif(int(number[4:], 2) & int(diagonal_masks[quarter], 2) & 12 != 0): # 1100
                results[global_possible_states[idx]].append(3) # Horizontal
            elif(int(number[4:], 2) & int(diagonal_masks[quarter], 2) & 3 != 0): # 0011
                results[global_possible_states[idx]].append(2) # Vertical
            else:
                results[global_possible_states[idx]].append(1)

    with open("output.json", "w") as f:
        f.write(json.dumps(results, indent=4))

def get_sprite(SourcePixels, offsets):
    center = (15, 4) # really 15, 4, but i needed some alterations
    size = (32, 32)
    amounts = [
        (range(center[0]+1), range(center[1]+1)),
        (range(center[0]+1), range(center[1]+1, size[1])),
        (range(center[0]+1, size[0]), range(center[1]+1, size[1])),
        (range(center[0]+1, size[0]), range(center[1]+1)),
               ]

    img = Image.new('RGBA', size)
    # img = img.convert('RGBA') # conversion to RGBA
    PixelsFinal = img.load()

    global_offsets = {
        1: (0, 0),
        2: (32, 0),
        3: (64, 0),
        4: (0, 32),
        5: (32, 32)
    }

    for areas, our_offset in zip(amounts, offsets):
        for i in areas[0]:
            input_x = i + global_offsets[our_offset][0]
            for j in areas[1]:
                input_y = j + global_offsets[our_offset][1]
                PixelsFinal[i,j] = SourcePixels[input_x,input_y]

    img.save("output.png")
    img.close()
