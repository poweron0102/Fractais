import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import img_to_array, array_to_img
from PIL import Image

# NOTA: É necessário ter o TensorFlow instalado.
# pip install tensorflow

# Carrega o modelo VGG16 pré-treinado no ImageNet.
# `include_top=False` remove a camada de classificação final.
try:
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    # Usaremos a saída de uma camada convolucional intermediária para obter características.
    model = Model(inputs=base_model.input, outputs=base_model.get_layer('block4_pool').output)
except Exception as e:
    print(f"Erro ao carregar o modelo VGG16: {e}")
    print(
        "Certifique-se de que o TensorFlow está instalado e que você tem uma conexão com a internet para baixar os pesos do modelo.")
    model = None


def preprocess_image_for_vgg(img_array: np.ndarray) -> np.ndarray:
    """
    Prepara um array de imagem para o modelo VGG16.
    - Converte o array para uma imagem PIL.
    - Redimensiona para 224x224.
    - Converte de volta para array.
    - Adiciona uma dimensão de batch.
    - Usa a função de pré-processamento da Keras.
    """
    # Garante que o tipo de dado é 'uint8' antes de converter para imagem
    if img_array.dtype != 'uint8':
        img_array = img_array.astype('uint8')
    # Converte array numpy para imagem PIL
    img = array_to_img(img_array)
    # Redimensiona a imagem para o tamanho de entrada esperado pela VGG16
    img = img.resize((224, 224), Image.Resampling.LANCZOS)
    # Converte a imagem de volta para um array numpy
    img_array = img_to_array(img)
    # Adiciona uma dimensão extra para o batch
    img_array = np.expand_dims(img_array, axis=0)
    # Pré-processa a imagem (normalização, etc.) conforme esperado pela VGG16
    img_array = preprocess_input(img_array)
    return img_array


def extract_features(img_array: np.ndarray) -> np.ndarray:
    """
    Extrai o vetor de características de uma imagem usando o modelo VGG16.
    Retorna um vetor de zeros se o modelo não for carregado.
    """
    if model is None:
        return np.zeros((1, 14, 14, 512)).flatten()

    processed_img = preprocess_image_for_vgg(img_array)
    features = model.predict(processed_img, verbose=0)
    # Aplaina o vetor de características para facilitar a comparação
    return features.flatten()
