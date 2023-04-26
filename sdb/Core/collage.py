from PIL import Image

def make_collage(images, rows, cols):
    w, h = images[0].size
    collage = Image.new('RGB', (w * cols, h * rows))
    for i, image in enumerate(images):
        collage.paste(image, (w * (i % cols), h * (i // cols)))
    return collage