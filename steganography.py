import encryption
from numpy import ndarray

END_DELIMETER = "<--end-->"

def encode_to_image(image: ndarray, message: str, encryption_key) -> ndarray:
    """Encodes the `message` into the `image` and returns the modified image."""

    # make sure the message does not contain the end delimeter
    if END_DELIMETER in message:
        raise ValueError("The message cannot contain the end delimeter: \"" + END_DELIMETER + "\"")

    # encrypt the message
    encrypted_message = encryption.encrypt_blocks(encryption_key, message) + encryption.encrypt(encryption_key, END_DELIMETER)

    # make sure the image is large enough to encode the message
    image_byte_count = image.shape[0] * image.shape[1] * 3 // 8 # width * height * 3 subpixels // 8 bits
    if len(encrypted_message) > image_byte_count:
        raise ValueError("Error, message is too long to be encoded in the provided image.")

    # convert the encrypted message into a binary string
    binary_encrypted_message = "".join(_convert_to_binary_list(encrypted_message))

    # get the length of the encrypted message
    message_length = len(binary_encrypted_message)

    # go through all the pixels in the image
    data_index = 0
    for pixel_row in image:
        for pixel in pixel_row:

            # modify the least significant bit of each color in the pixel to hold the message
            for subpixel_index, subpixel_binary_value in enumerate(_convert_to_binary_list(pixel)):

                # make sure there is still data to write
                if data_index >= message_length:
                    break

                # change the least significant bit in the subpixel
                pixel[subpixel_index] = int(subpixel_binary_value[:-1] + binary_encrypted_message[data_index], 2) # convert the binary to an int for the pixel value
                data_index += 1
    
    return image

def decode_from_image(image: ndarray, decryption_key) -> str:
    """Decodes the message from the `image` and returns the message."""
    
    binary_message_data = ""

    # go through all the pixels in the image
    for pixel_row in image:
        for pixel in pixel_row:

            # extract the least significant bit from each of the subpixels
            for subpixel_binary_value in _convert_to_binary_list(pixel):
                binary_message_data += subpixel_binary_value[-1]
    
    # convert the image bits into bytes (this includes the message + a bunch of messy random pixel data afterward)
    all_image_bytes = bytes([int(binary_message_data[i : i + 8], 2) for i in range(0, len(binary_message_data), 8)])

    decrypted_message_sections = []
    block_size = (decryption_key.key_size + 7) // 8
    cipher_text_section_start_index = 0

    # go through each block and decrypt it until it is the end delimeter
    while True:
        # get the bytes in the current message block
        encrypted_message_bytes = all_image_bytes[
            cipher_text_section_start_index:cipher_text_section_start_index + block_size]
        
        # decrypt the message
        decrypted_block = encryption.decrypt_blocks(decryption_key, encrypted_message_bytes)

        # check if it is the end delimeter and time to stop, otherwise 
        # add the decrypted block to the output and continue
        if decrypted_block == END_DELIMETER:
            break
        else:
            decrypted_message_sections.append(decrypted_block)

        cipher_text_section_start_index += block_size

    return "".join(decrypted_message_sections)

def _convert_to_binary_list(values):
    """Converts and returns the `value` as a list of binary values."""
    return [format(value, "08b") for value in values]