import os
import numpy as np
from numba import njit, cuda


@njit
def grayscale(img: np.ndarray) -> np.ndarray:
    """Converts an RGB image to grayscale using the YUV luma component."""
    gray_val = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]

    img_gray = np.zeros_like(img, dtype=np.uint8)
    img_gray[..., 0] = gray_val
    img_gray[..., 1] = gray_val
    img_gray[..., 2] = gray_val

    return img_gray


@njit
def convolve(img_channel: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Helper function to apply a convolution kernel to a single image channel."""
    k_h, k_w = kernel.shape
    h, w = img_channel.shape
    pad_h, pad_w = k_h // 2, k_w // 2

    padded_img = np.zeros((h + pad_h * 2, w + pad_w * 2), dtype=np.float32)
    padded_img[pad_h:h + pad_h, pad_w:w + pad_w] = img_channel

    output = np.zeros_like(img_channel, dtype=np.float32)

    for i in range(h):
        for j in range(w):
            region = padded_img[i:i + k_h, j:j + k_w]
            output[i, j] = np.sum(region * kernel)

    return output


@njit
def angle_to_hue(angle: np.ndarray) -> np.ndarray:
    """Converts an angle in radians (-pi to +pi) to a hue value (0-255)."""
    return (((angle + np.pi) / (2 * np.pi)) * 255).astype(np.uint8)


@njit
def sobel(img: np.ndarray) -> np.ndarray:
    """
    Applies the Sobel operator and returns a 3-channel representation
    encoding both edge magnitude and direction.
    """
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    gray_channel = img[:, :, 0].astype(np.float32)

    img_x = convolve(gray_channel, kernel_x)
    img_y = convolve(gray_channel, kernel_y)

    magnitude = np.sqrt(img_x ** 2 + img_y ** 2)
    angle = np.arctan2(img_y, img_x)

    mag_norm = (magnitude / np.max(magnitude)) * 255 if np.max(magnitude) > 0 else np.zeros_like(magnitude)
    mag_norm = mag_norm.astype(np.uint8)

    hue = angle_to_hue(angle)

    sobel_output = np.zeros_like(img, dtype=np.uint8)
    sobel_output[:, :, 0] = mag_norm
    sobel_output[:, :, 1] = hue
    sobel_output[:, :, 2] = mag_norm

    return sobel_output


@njit
def comp_sobel_dif(sobel_frag1: np.ndarray, sobel_frag2: np.ndarray) -> float:
    """
    Compares two Sobel feature fragments and returns a similarity score.
    """
    frag1_i32 = sobel_frag1.astype(np.int32)
    frag2_i32 = sobel_frag2.astype(np.int32)

    diff = np.abs(frag1_i32 - frag2_i32)
    weights = np.array([0.25, 0.5, 0.25], dtype=np.float32)
    weighted_diff_sum = np.sum(diff * weights)
    max_diff = sobel_frag1.shape[0] * sobel_frag1.shape[1] * 255.0 * np.sum(weights)

    if max_diff == 0:
        return 1.0
    return 1.0 - (weighted_diff_sum / max_diff)


@cuda.jit(device=True)
def cu_comp_sobel_dif(sobel_frag1, sobel_frag2):
    """
    Compares two Sobel feature fragments on the GPU. This is a 'device function'.
    """
    height, width, _ = sobel_frag1.shape

    # Pesos para os canais (Magnitude, Matiz, Magnitude)
    weights_ch0 = 0.25
    weights_ch1 = 0.50
    weights_ch2 = 0.25

    max_diff_sum = height * width * 255.0 * (weights_ch0 + weights_ch1 + weights_ch2)

    if max_diff_sum == 0:
        return 1.0

    weighted_diff_sum = 0.0
    for y in range(height):
        for x in range(width):
            # Calcula a diferença absoluta para cada canal
            diff0 = abs(float(sobel_frag1[y, x, 0]) - float(sobel_frag2[y, x, 0]))
            diff1 = abs(float(sobel_frag1[y, x, 1]) - float(sobel_frag2[y, x, 1]))
            diff2 = abs(float(sobel_frag1[y, x, 2]) - float(sobel_frag2[y, x, 2]))
            # Soma as diferenças ponderadas
            weighted_diff_sum += (diff0 * weights_ch0) + (diff1 * weights_ch1) + (diff2 * weights_ch2)

    similarity = 1.0 - (weighted_diff_sum / max_diff_sum)
    return similarity
