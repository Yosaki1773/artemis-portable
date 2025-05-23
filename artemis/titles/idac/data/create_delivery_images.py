import hashlib
import os


def prepare_images(image_folder="titles/idac/data/images"):
    print(f"Preparing image delivery files in {image_folder}...")

    for file in os.listdir(image_folder):
        if file.endswith(".png") or file.endswith(".jpg"):
            # dpg_name = "adv-" + file[:-4].upper()
            dpg_name = file[:-4]
            if file.endswith(".png"):
                dpg_name += ".dpg"
            else:
                dpg_name += ".djg"

            if os.path.exists(os.path.join(image_folder, dpg_name)):
                continue
            else:
                with open(
                    os.path.join(image_folder, file), "rb"
                ) as original_image_file:
                    original_image = original_image_file.read()
                    image_hash = hashlib.md5(original_image).hexdigest()
                    print(
                        f"DPG for {file} not found, creating with hash {image_hash.upper()} ..."
                    )
                    md5_buf = bytes.fromhex(image_hash)
                    dpg_buf = md5_buf + original_image
                    dpg_name = "adv-" + image_hash.upper() + dpg_name[:-4]
                    with open(os.path.join(image_folder, dpg_name), "wb") as dpg_file:
                        dpg_file.write(dpg_buf)

                    print(f"Created {dpg_name}.")


# Call the function to execute it
prepare_images()
