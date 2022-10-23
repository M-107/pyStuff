import numpy as np
from PIL import Image, ImageDraw

blocks_horizontal = 20
blocks_vertical = 20
# land modifier 0 - only water, 100 - only land (apart from borders)
land_modifier = 65
style = 2

# water must be twice bigger than the corner blocks in both dimensions
block_water = Image.open(rf"blocks/{style}/block_water.png")
block_size = block_water.size[0]
# All land
corner_full = Image.open(rf"blocks/{style}/corner_full.png")
# land on the right side
corner_half = Image.open(rf"blocks/{style}/corner_half.png")
# land in bottom right corner
corner_quarter = Image.open(rf"blocks/{style}/corner_quarter.png")
# Water in top left corner
corner_three_quarters = Image.open(rf"blocks/{style}/corner_three_quarters.png")

# make array with random numbers of the block size
layout_borderless = np.random.rand(blocks_vertical - 2, blocks_horizontal - 2)
# turn the nice 0-100 land modifier number into actually usable one
land_modifier_real = (land_modifier - 50) / 100
# edit the array with the just created usable land modifier number
layout_borderless += land_modifier_real
# turn the random numbers into integers, either 1s or 0s in this case
layout_borderless = np.rint(layout_borderless)
# add water (0s) around the whole array
layout = np.pad(layout_borderless, [1])
# print(layout)
# Prepare an empty image of the desired size
width = int(blocks_horizontal * block_size)
height = int(blocks_vertical * block_size)
img = Image.new("RGB", (width, height), (255, 255, 255))

# Check the value of a specific int in the 2d array and the ones around it
# Decide what picture should be used in its place
def make_block(array, x, y):
    pos = (x * block_size, y * block_size)
    half_block = int(block_size / 2)
    temp_img = Image.new("RGB", (block_size, block_size), (0, 255, 0))
    rect = ImageDraw.Draw(temp_img)
    rect.rectangle([(1, 1), (38, 38)], fill=(255, 0, 100))
    # Edges
    if array[y][x - 1] == 0:
        temp_img.paste(corner_half, (0, 0))
        temp_img.paste(corner_half, (0, half_block))
    if array[y + 1][x] == 0:
        temp_img.paste(corner_half.rotate(90), (0, half_block))
        temp_img.paste(corner_half.rotate(90), (half_block, half_block))
    if array[y][x + 1] == 0:
        temp_img.paste(corner_half.rotate(180), (half_block, 0))
        temp_img.paste(corner_half.rotate(180), (half_block, half_block))
    if array[y - 1][x] == 0:
        temp_img.paste(corner_half.rotate(270), (0, 0))
        temp_img.paste(corner_half.rotate(270), (half_block, 0))
    # Corners
    if array[y][x - 1] == 0 and array[y - 1][x] == 0:
        temp_img.paste(corner_quarter, (0, 0))
    if array[y][x - 1] == 0 and array[y + 1][x] == 0:
        temp_img.paste(corner_quarter.rotate(90), (0, half_block))
    if array[y][x + 1] == 0 and array[y + 1][x] == 0:
        temp_img.paste(corner_quarter.rotate(180), (half_block, half_block))
    if array[y][x + 1] == 0 and array[y - 1][x] == 0:
        temp_img.paste(corner_quarter.rotate(270), (half_block, 0))
    # Inner Corners
    if array[y - 1][x - 1] == 0 and array[y - 1][x] == 1 and array[y][x - 1] == 1:
        temp_img.paste(corner_three_quarters, (0, 0))
    if array[y + 1][x - 1] == 0 and array[y + 1][x] == 1 and array[y][x - 1] == 1:
        temp_img.paste(corner_three_quarters.rotate(90), (0, half_block))
    if array[y + 1][x + 1] == 0 and array[y + 1][x] == 1 and array[y][x + 1] == 1:
        temp_img.paste(corner_three_quarters.rotate(180), (half_block, half_block))
    if array[y - 1][x + 1] == 0 and array[y - 1][x] == 1 and array[y][x + 1] == 1:
        temp_img.paste(corner_three_quarters.rotate(270), (half_block, 0))
    # Inner Fills
    if array[y - 1][x - 1] == 1 and array[y][x - 1] == 1 and array[y - 1][x] == 1:
        temp_img.paste(corner_full, (0, 0))
    if array[y + 1][x - 1] == 1 and array[y][x - 1] == 1 and array[y + 1][x] == 1:
        temp_img.paste(corner_full, (0, half_block))
    if array[y + 1][x + 1] == 1 and array[y][x + 1] == 1 and array[y + 1][x] == 1:
        temp_img.paste(corner_full, (half_block, half_block))
    if array[y - 1][x + 1] == 1 and array[y][x + 1] == 1 and array[y - 1][x] == 1:
        temp_img.paste(corner_full, (half_block, 0))
    img.paste(temp_img, pos)


# Run through the array and fill the resulting image accordingly
for y, i in enumerate(layout):
    for x, j in enumerate(i):
        print(
            f"Building block {(y*len(i))+(x+1):>5}/{blocks_horizontal*blocks_vertical:<5}"
        )
        if j == 0:
            img.paste(block_water, (x * block_size, y * block_size))
        else:
            make_block(layout, x, y)

img.show()
# img.save('map.png', quality=95)
