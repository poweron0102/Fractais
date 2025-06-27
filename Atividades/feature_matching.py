import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision.models as models
from torchvision import transforms


def sift_matching(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    # Calculo
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    matched_img = cv2.drawMatches(
        img1, kp1, img2, kp2, good, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    cv2.imwrite(f"sift.png", matched_img)


def vgg_matching(img1_path, img2_path):
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    img1_tensor = transform(img1_rgb).unsqueeze(0)
    img2_tensor = transform(img2_rgb).unsqueeze(0)

    model = models.vgg16(weights='DEFAULT').features[:23]
    model.eval()

    with torch.no_grad():
        features1 = model(img1_tensor)
        features2 = model(img2_tensor)

    def get_kps_descriptors(features):
        _, c, h, w = features.shape
        descriptors = features.view(c, -1).t().numpy().astype(np.float32)

        # campo receptivo = 8px
        kps = []
        stride = 8
        for y in range(h):
            for x in range(w):
                kps.append(cv2.KeyPoint(x * stride + 4, y * stride + 4, 8))
        return kps, descriptors

    kps1, des1 = get_kps_descriptors(features1)
    kps2, des2 = get_kps_descriptors(features2)

    flann = cv2.FlannBasedMatcher({'algorithm': 1, 'trees': 5}, {'checks': 50})
    matches = flann.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    img1_resized = cv2.resize(img1_rgb, (224, 224))
    img2_resized = cv2.resize(img2_rgb, (224, 224))
    matched_img = cv2.drawMatches(
        img1_resized, kps1, img2_resized, kps2, good, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    plt.imsave(f"vgg.png", matched_img)


img1 = input("Digite o caminho da primeira imagem: ")
img2 = input("Digite o caminho da segunda imagem: ")

sift_matching(img1, img2)
vgg_matching(img1, img2)
