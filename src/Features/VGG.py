import numpy as np
import torch
from torchvision import models, transforms
from PIL import Image

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Usando dispositivo: {device}")

model = None
try:
    # Carrega o modelo VGG16 pré-treinado
    vgg16 = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1).to(device)

    # Remove as camadas de classificação (fully connected)
    # Usaremos a saída da penúltima camada de max pooling
    model = torch.nn.Sequential(*list(vgg16.features.children())[:24])

    # Coloca o modelo em modo de avaliação (desativa dropout, batchnorm, etc.)
    model.eval()

except Exception as e:
    print(f"Erro ao carregar o modelo VGG16 com PyTorch: {e}")
    print("Certifique-se de que PyTorch e Torchvision estão instalados e que você tem uma conexão com a internet.")

# Define a sequência de transformações para pré-processar a imagem
# 1. Redimensiona para 224x224, o tamanho de entrada esperado pela VGG
# 2. Converte a imagem para um tensor PyTorch
# 3. Normaliza o tensor com a média e desvio padrão usados no treinamento do ImageNet
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def extract_features(img_array: np.ndarray) -> np.ndarray:
    """
    Extrai o vetor de características de uma imagem usando o modelo VGG16 com PyTorch.
    """
    if model is None:
        # Retorna um vetor de zeros com a dimensão esperada se o modelo falhou ao carregar
        return np.zeros(14 * 14 * 512)

    # Converte o array numpy para uma imagem PIL
    img_pil = Image.fromarray(img_array.astype('uint8'), 'RGB')

    # Aplica as transformações de pré-processamento
    img_tensor = preprocess(img_pil)

    # Adiciona uma dimensão de batch (o modelo espera um batch de imagens)
    batch_tensor = img_tensor.unsqueeze(0).to(device)

    # Desativa o cálculo de gradientes para acelerar a inferência
    with torch.no_grad():
        features = model(batch_tensor)

    # Move as características para a CPU (se estiver na GPU), remove a dimensão do batch,
    # aplaina o tensor e o converte para um array numpy.
    return features.cpu().squeeze(0).flatten().numpy()

