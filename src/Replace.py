import numpy as np
from numba import prange, njit, cuda
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm

from src.Features.Color import comp_imgs_dif, covert_to_YUV, cu_comp_imgs_dif
from src.Features.VGG import extract_features  # Importando a nova função
from src.Fragmentos import Image, FragmentGrid


def replace(
        fragmentos_1: FragmentGrid,
        fragmentos_2: FragmentGrid,
        weights: tuple[float, float] = (1.0, 0.0),
        yuv: bool = False
) -> Image:
    """
    Substitui fragmentos de forma otimizada, detectando automaticamente o hardware
    disponível (GPU com CUDA ou CPU).
    """
    h, w, fh, fw, _ = fragmentos_1.shape
    n = h * w
    peso_cor, peso_vgg = weights

    frag1_flat = fragmentos_1.reshape((n, fh, fw, 3))
    frag2_flat = fragmentos_2.reshape((n, fh, fw, 3))

    features1_vgg = np.zeros((n, 1), dtype=np.float32)  # Dummy para evitar erro se peso_vgg=0
    features2_vgg = np.zeros((n, 1), dtype=np.float32)  # Dummy para evitar erro se peso_vgg=0
    if peso_vgg > 0:
        print("Extraindo características VGG do conjunto 1...")
        features1_vgg = np.array([extract_features(f) for f in tqdm(frag1_flat)])
        print("Extraindo características VGG do conjunto 2...")
        features2_vgg = np.array([extract_features(f) for f in tqdm(frag2_flat)])

        norm1 = np.linalg.norm(features1_vgg, axis=1, keepdims=True)
        norm2 = np.linalg.norm(features2_vgg, axis=1, keepdims=True)
        features1_vgg = np.divide(features1_vgg, norm1, out=np.zeros_like(features1_vgg), where=norm1 != 0)
        features2_vgg = np.divide(features2_vgg, norm2, out=np.zeros_like(features2_vgg), where=norm2 != 0)

    frag1_proc_color = frag1_flat.astype(np.uint8)
    frag2_proc_color = frag2_flat.astype(np.uint8)
    if yuv:
        print("Convertendo imagens para YUV...")
        frag1_proc_color = np.array([covert_to_YUV(f) for f in frag1_flat])
        frag2_proc_color = np.array([covert_to_YUV(f) for f in frag2_flat])

    cost_matrix = None
    if cuda.is_available():
        print("\n==> GPU com suporte a CUDA detectada. Usando GPU para cálculo. <==\n")
        cost_matrix = calc_cost_matrix_cuda(
            features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, n, peso_cor, peso_vgg
        )
    else:
        print("\n==> GPU com CUDA não encontrada. Usando CPU para cálculo. <==\n")
        cost_matrix = calc_cost_matrix(
            features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, n, peso_cor, peso_vgg
        )
    # ----------------------------------------

    print("Resolvendo atribuição com Algoritmo Húngaro...")
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    print("Reconstruindo a imagem final...")
    output_array = np.zeros((h * fh, w * fw, 3), dtype=np.uint8)
    for idx, frag_idx in zip(row_ind, col_ind):
        i, j = divmod(idx, w)
        output_array[i * fh:(i + 1) * fh, j * fw:(j + 1) * fw] = frag2_flat[frag_idx]

    print("Processo finalizado.")
    return output_array


@njit(parallel=True)
def calc_cost_matrix(features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, n, peso_cor, peso_vgg):
    cost_matrix = np.zeros((n, n), dtype=np.float32)
    print("Calculando matriz de custo combinada...")
    for i in prange(n):
        for j in prange(n):
            # Calcula a similaridade de cor se o peso for maior que zero
            if peso_cor > 0:
                sim_cor = comp_imgs_dif(frag1_proc_color[i], frag2_proc_color[j])
            else:
                sim_cor = 0.0

            # Calcula a similaridade VGG (cosseno) se o peso for maior que zero
            if peso_vgg > 0:
                sim_vgg = np.dot(features1_vgg[i], features2_vgg[j])
            else:
                sim_vgg = 0.0

            # Calcula a similaridade final ponderada
            final_similarity = (sim_cor * peso_cor) + (sim_vgg * peso_vgg)

            # O custo é o inverso da similaridade (1 - similaridade)
            cost_matrix[i, j] = 1.0 - final_similarity
    return cost_matrix


@cuda.jit
def calc_cost_matrix_kernel(
        features1_vgg,
        features2_vgg,
        frag1_proc_color,
        frag2_proc_color,
        cost_matrix,
        peso_cor,
        peso_vgg
):
    """
    Kernel CUDA para calcular a matriz de custo. Cada thread calcula um elemento (i, j).
    """
    # Determina o índice (i, j) da matriz que esta thread irá calcular
    i, j = cuda.grid(2)

    # Checagem de limites para garantir que a thread não acesse memória fora da matriz
    # (importante se o tamanho da matriz não for um múltiplo exato do tamanho do bloco)
    if i < cost_matrix.shape[0] and j < cost_matrix.shape[1]:
        # --- Cálculo da Similaridade de Cor ---
        sim_cor = 0.0
        if peso_cor > 0:
            # Chama a device function para comparar os fragmentos de cor
            sim_cor = cu_comp_imgs_dif(frag1_proc_color[i], frag2_proc_color[j])

        # --- Cálculo da Similaridade VGG (Produto Escalar) ---
        sim_vgg = 0.0
        if peso_vgg > 0:
            # Loop explícito para o produto escalar (dot product)
            # features1_vgg.shape[1] é o comprimento do vetor de features
            for k in range(features1_vgg.shape[1]):
                sim_vgg += features1_vgg[i, k] * features2_vgg[j, k]

        # --- Combinação e Custo Final ---
        final_similarity = (sim_cor * peso_cor) + (sim_vgg * peso_vgg)
        cost_matrix[i, j] = 1.0 - final_similarity


# ==============================================================================
# 3. FUNÇÃO PRINCIPAL (HOST) (executada no CPU para orquestrar a GPU)
# ==============================================================================

def calc_cost_matrix_cuda(
        features1_vgg: np.ndarray,
        features2_vgg: np.ndarray,
        frag1_proc_color: np.ndarray,
        frag2_proc_color: np.ndarray,
        n: int,
        peso_cor: float,
        peso_vgg: float
):
    """
    Orquestra o cálculo da matriz de custo na GPU.
    """
    print("Iniciando cálculo da matriz de custo na GPU...")

    # --- 1. Transferir dados do Host (CPU) para o Device (GPU) ---
    print("Movendo dados para a memória da GPU...")
    d_features1_vgg = cuda.to_device(features1_vgg)
    d_features2_vgg = cuda.to_device(features2_vgg)
    d_frag1_proc_color = cuda.to_device(frag1_proc_color)
    d_frag2_proc_color = cuda.to_device(frag2_proc_color)

    # Criar um array vazio na GPU para armazenar o resultado
    d_cost_matrix = cuda.device_array((n, n), dtype=np.float32)

    # --- 2. Definir a configuração de lançamento do Kernel ---
    # Threads por bloco (um valor comum é 16x16 ou 32x32)
    threads_per_block = (16, 16)

    # Blocos por grade (calculado para cobrir toda a matriz)
    blocks_per_grid_x = int(np.ceil(n / threads_per_block[0]))
    blocks_per_grid_y = int(np.ceil(n / threads_per_block[1]))
    blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)

    # --- 3. Lançar o Kernel na GPU ---
    print(f"Lançando kernel com grade {blocks_per_grid} e blocos {threads_per_block}...")
    calc_cost_matrix_kernel[blocks_per_grid, threads_per_block](
        d_features1_vgg,
        d_features2_vgg,
        d_frag1_proc_color,
        d_frag2_proc_color,
        d_cost_matrix,
        peso_cor,
        peso_vgg
    )
    # O código do host espera aqui até a GPU terminar (sincronização implícita)

    # --- 4. Copiar o resultado do Device (GPU) de volta para o Host (CPU) ---
    print("Copiando resultado de volta para a memória do CPU...")
    cost_matrix = d_cost_matrix.copy_to_host()

    print("Cálculo na GPU finalizado.")
    return cost_matrix
