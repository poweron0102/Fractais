import numpy as np
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm

from src.Features.Color import comp_imgs, covert_to_YUV
from src.Features.VGG import extract_features  # Importando a nova função
from src.Fragmentos import Image, FragmentGrid


def replace(
        fragmentos_1: FragmentGrid,
        fragmentos_2: FragmentGrid,
        weights: tuple[float, float] = (1.0, 0.0),  # (peso_cor, peso_vgg)
        yuv: bool = False
) -> Image:
    """
    Substitui cada fragmento de fragmentos_1 pelo fragmento mais semelhante
    usando uma combinação ponderada de similaridade de cor e VGG.
    O emparelhamento ótimo é feito via Hungarian Algorithm para evitar repetições.
    """
    h, w, fh, fw, _ = fragmentos_1.shape
    n = h * w
    peso_cor, peso_vgg = weights

    # Achata os grids para facilitar a iteração
    frag1_flat = fragmentos_1.reshape((n, fh, fw, 3))
    frag2_flat = fragmentos_2.reshape((n, fh, fw, 3))

    # Pré-calcula características VGG para todos os fragmentos se o peso VGG for maior que zero
    # Isso é muito mais eficiente do que extrair características dentro do loop.
    features1_vgg = None
    features2_vgg = None
    if peso_vgg > 0:
        print("Extraindo características VGG do conjunto 1...")
        features1_vgg = np.array([extract_features(f) for f in tqdm(frag1_flat)])

        print("Extraindo características VGG do conjunto 2...")
        features2_vgg = np.array([extract_features(f) for f in tqdm(frag2_flat)])

        # Normaliza todos os vetores de características de uma vez para o cálculo da similaridade de cosseno
        norm1 = np.linalg.norm(features1_vgg, axis=1, keepdims=True)
        norm2 = np.linalg.norm(features2_vgg, axis=1, keepdims=True)
        # Evita divisão por zero para vetores nulos
        features1_vgg = np.divide(features1_vgg, norm1, out=np.zeros_like(features1_vgg), where=norm1 != 0)
        features2_vgg = np.divide(features2_vgg, norm2, out=np.zeros_like(features2_vgg), where=norm2 != 0)

    # Converte os fragmentos para o espaço de cor YUV se a opção estiver ativa
    frag1_proc_color = frag1_flat
    frag2_proc_color = frag2_flat
    if yuv:
        print("Convertendo imagens para YUV...")
        frag1_proc_color = np.array([covert_to_YUV(f) for f in frag1_flat])
        frag2_proc_color = np.array([covert_to_YUV(f) for f in frag2_flat])

    # Monta a matriz de custo (n x n)
    cost_matrix = np.zeros((n, n), dtype=np.float32)
    print("Calculando matriz de custo combinada...")
    for i in tqdm(range(n)):
        for j in range(n):
            # Calcula a similaridade de cor se o peso for maior que zero
            sim_cor = comp_imgs(frag1_proc_color[i], frag2_proc_color[j]) if peso_cor > 0 else 0.0

            # Calcula a similaridade VGG (cosseno) se o peso for maior que zero
            sim_vgg = np.dot(features1_vgg[i], features2_vgg[j]) if peso_vgg > 0 else 0.0

            # Calcula a similaridade final ponderada
            final_similarity = (sim_cor * peso_cor) + (sim_vgg * peso_vgg)

            # O custo é o inverso da similaridade (1 - similaridade)
            cost_matrix[i, j] = 1.0 - final_similarity

    # Resolve o problema de atribuição com o algoritmo Húngaro para encontrar o menor custo total
    print("Resolvendo atribuição com Algoritmo Húngaro...")
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Reconstrói a imagem final com os fragmentos de melhor correspondência
    output = np.zeros((h * fh, w * fw, 3), dtype=np.uint8)
    for idx, frag_idx in zip(row_ind, col_ind):
        i, j = divmod(idx, w)
        output[i * fh:(i + 1) * fh, j * fw:(j + 1) * fw] = frag2_flat[frag_idx]

    return output
