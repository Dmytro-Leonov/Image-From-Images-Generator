import os
from cv2 import cv2
from natsort import os_sorted

OUTPUT_FOLDER, SRC_FOLDER, DIR_FOLDER = "GeneratedClips", "ConvertedImages", "GeneratedClips"


def progress_bar(current, total, title, bar_length=20):
    fraction = current / total
    progress = int(fraction * bar_length) * '█'
    padding = int(bar_length - len(progress)) * '░'
    ending = '\n' if current == total else '\r'
    print(f"{title} [{progress}{padding}] {int(fraction * 100)}%", end=ending)


def choose_image():
    images = os_sorted(os.listdir(SRC_FOLDER))
    if not images:
        raise OSError("No images to zoom")
    image = None
    print("Choose image to zoom:")
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
    print("Retrieving image...")
    return cv2.imread(os.path.join(SRC_FOLDER, image))


def initiate_video(fps, small_side_crop, img_width, img_height, use_width):
    max_num = 0
    for im in os.listdir(DIR_FOLDER):
        try:
            last = int(im.split(".")[0])
            if last > max_num:
                max_num = last
        except ValueError:
            pass
    file_name = os.path.join(DIR_FOLDER, f"{max_num + 1}.mp4")
    if use_width:
        w_percent = small_side_crop / float(img_width)
        large_side_crop = int((float(img_height) * float(w_percent)))
        result = cv2.VideoWriter(file_name,
                                 cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps, (small_side_crop, large_side_crop))
    else:
        h_percent = small_side_crop / float(img_height)
        large_side_crop = int((float(img_width) * float(h_percent)))
        result = cv2.VideoWriter(file_name,
                                 cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps, (large_side_crop, small_side_crop))
    return large_side_crop, result


def resize_and_crop(image, size, small_side_crop, bigger_side_crop, use_width, img_dim):
    if use_width:
        w_percent = size / float(img_dim[0])
        height = int(img_dim[1] * w_percent)
        x1, x2 = (img_dim[0] - size) // 2, (img_dim[0] + size) // 2
        y1, y2 = (img_dim[1] - height) // 2, (img_dim[1] + height) // 2
        image = image[y1: y2, x1: x2]
        image = cv2.resize(image, (small_side_crop, bigger_side_crop), cv2.INTER_AREA)
    else:
        h_percent = size / float(img_dim[1])
        height = int(img_dim[0] * h_percent)
        x1, x2 = (img_dim[0] - height) // 2, (img_dim[0] + height) // 2
        y1, y2 = (img_dim[1] - size) // 2, (img_dim[1] + size) // 2
        image = image[y1: y2, x1: x2]
        image = cv2.resize(image, (bigger_side_crop, small_side_crop), cv2.INTER_AREA)
    return image


def zoom(image, small_side_crop=1080, zoom_factor=60, fps=24, video_length=5):
    total_frames = round(fps * video_length)
    img_height, img_width = image.shape[:2]
    min_resolution = min(img_width, img_height)
    result_min_side = round(min_resolution / zoom_factor)
    frame_step = round((min_resolution - result_min_side) / total_frames)
    use_width = True if img_width <= img_height else False
    large_side_crop, result = initiate_video(fps, small_side_crop, img_width, img_height, use_width)
    total = len(range(min_resolution, result_min_side, -frame_step)) - 1
    total = min_resolution - (min_resolution - frame_step * total)
    for size in range(min_resolution, result_min_side, -frame_step):
        frame = resize_and_crop(image, size, small_side_crop, large_side_crop, use_width, img_dim=(img_width, img_height))
        result.write(frame)
        progress_bar(min_resolution - size, total, "Generating video:")
    print("Video generated")


def main():
    image = choose_image()
    zoom(image)


if __name__ == '__main__':
    main()
