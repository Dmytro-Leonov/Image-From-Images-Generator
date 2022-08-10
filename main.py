import os
import numpy as np
import cv2
from PIL import Image
from natsort import os_sorted

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_FOLDER, DIR_FOLDER, IMAGE_FOLDER, CONVERTED_IMAGES_FOLDER = \
    ROOT_DIR+ "\SourceImages", ROOT_DIR+ "\ProcessedImages", ROOT_DIR+ "\ImagesToConvert", ROOT_DIR+ "\ConvertedImages"


class AvgColor:
    def __init__(self, avg_color: list, path: str):
        self.color_rgb = avg_color
        self.path = path


def progress_bar(current, total, title, bar_length=20):
    fraction = current / total
    progress = int(fraction * bar_length) * '█'
    padding = int(bar_length - len(progress)) * '░'
    ending = '\n' if current == total else '\r'
    print(f"{title} [{progress}{padding}] {int(fraction*100)}%", end=ending)


def crop_center(pil_img):
    img_width, img_height = pil_img.size
    crop_size = min([img_width, img_height])
    return pil_img.crop(((img_width - crop_size) // 2,
                         (img_height - crop_size) // 2,
                         (img_width + crop_size) // 2,
                         (img_height + crop_size) // 2))


def prepare_images(size=(32, 32)):
    subfolders = [f[0] for f in os.walk(SRC_FOLDER)][1:]
    if not subfolders:
        raise OSError("No folders to choose images from")
    folder = None
    print("Choose folder to use:")
    for i, image in enumerate(subfolders):
        print(f"{i + 1}: {image}")
    done = False
    while not done:
        try:
            print("Enter choice: ", end="")
            choice = int(input())
            folder = subfolders[choice - 1]
            done = True
        except ValueError:
            print("Invalid input")
        except IndexError:
            print("Invalid choice")
    images = os.listdir(folder)
    if not images:
        raise OSError("No images to convert")
    for i, file in enumerate(images):
        image = Image.open(os.path.join(folder, file))
        image = crop_center(image)
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(os.path.join(DIR_FOLDER, f"img_{i}.jpg"))


def calculate_avg_color_and_brightness():
    colors = []
    for i, file in enumerate(os.listdir(DIR_FOLDER)):
        image_path = os.path.join(DIR_FOLDER, file)
        image_avg_color = AvgColor(
            [int(ch) for ch in np.array(Image.open(image_path).convert('RGB')).mean(0).mean(0)], image_path
        )
        colors.append(image_avg_color)

    return colors


def open_and_resize(base_width=200):
    images = os_sorted(os.listdir(IMAGE_FOLDER))
    if not images:
        raise OSError("No images to convert")
    image = None
    print("Choose image to convert:")
    for i, image in enumerate(images):
        print(f"{i + 1}: {image}")
    done = False
    while not done:
        try:
            print("Enter choice: ", end="")
            choice = int(input())
            image = images[choice - 1]
            done = True
        except ValueError:
            print("Invalid input")
        except IndexError:
            print("Invalid choice")
    image = Image.open(os.path.join(IMAGE_FOLDER, image))
    w_percent = (base_width / float(image.size[0]))
    height = int((float(image.size[1]) * float(w_percent)))
    return np.array(image.resize((base_width, height), Image.ANTIALIAS))


def save_image(image):
    max_num = 0
    for im in os.listdir(CONVERTED_IMAGES_FOLDER):
        try:
            last = int(im.split(".")[0])
            if last > max_num:
                max_num = last
        except ValueError:
            pass
    cv2.imwrite(os.path.join(CONVERTED_IMAGES_FOLDER, f"{max_num + 1}.jpg"), image)


def generate_art(image_to_convert: np.ndarray, images_domain_color: list):
    full_percentage = np.prod(image_to_convert.shape[:2])
    current_progress = 0
    full_image = []
    colors = np.array([color.color_rgb for color in images_domain_color])
    for i in range(image_to_convert.shape[0]):
        row_of_images = []
        for j in range(image_to_convert.shape[1]):
            color = np.array(image_to_convert[i, j])
            distances = np.sqrt(np.sum((colors - color) ** 2, axis=1))
            index_of_smallest = np.where(distances == np.min(distances))
            closest_color = colors[index_of_smallest]
            for color in images_domain_color:
                if np.array_equal(color.color_rgb, closest_color[0]):
                    row_of_images.append(cv2.imread(color.path))
                    current_progress += 1
                    progress_bar(current_progress, full_percentage, "Generating image:")
                    break
        full_image.append(cv2.hconcat(row_of_images))
    print("Compiling final image...")
    result = cv2.vconcat(full_image)
    save_image(result)


def clear_processed_images():
    for image in os.listdir(DIR_FOLDER):
        os.remove(os.path.join(DIR_FOLDER, image))


def main():
    clear_processed_images()
    print("Processed images cleared")
    prepare_images()
    print("Source images processed")
    images_avg_color = calculate_avg_color_and_brightness()
    print("Avg color calculated for every image")
    image_to_convert = open_and_resize()
    generate_art(image_to_convert, images_avg_color)
    print("Image compiled")


if __name__ == '__main__':
    main()
