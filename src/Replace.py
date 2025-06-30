import numpy as np
from numba import prange, njit, cuda
import lap
from tqdm import tqdm

from src.Features.Dif import comp_imgs_dif, covert_to_YUV, cu_comp_imgs_dif
from src.Features.Edge import sobel, comp_sobel_dif, cu_comp_sobel_dif
from src.Features.VGG import extract_features
from src.Fragmentos import Image, FragmentGrid


def replace(
        fragmentos_1: FragmentGrid,
        fragmentos_2: FragmentGrid,
        weights: tuple[float, float, float] = (1.0, 0.0, 0.0),
        yuv: bool = False
) -> Image:
    """
    Substitui fragmentos de forma otimizada, usando uma combinação ponderada de
    similaridade de cor, VGG e bordas Sobel. Detecta automaticamente o hardware
    disponível (GPU com CUDA ou CPU).
    """
    h, w, fh, fw, _ = fragmentos_1.shape
    n = h * w
    peso_cor, peso_vgg, peso_sobel = weights

    frag1_flat = fragmentos_1.reshape((n, fh, fw, 3))
    frag2_flat = fragmentos_2.reshape((n, fh, fw, 3))

    # Extração de características VGG (se o peso for maior que zero)
    features1_vgg = np.zeros((n, 1), dtype=np.float32)
    features2_vgg = np.zeros((n, 1), dtype=np.float32)
    if peso_vgg > 0:
        print("Extraindo características VGG do conjunto 1...")
        features1_vgg = np.array([extract_features(f) for f in tqdm(frag1_flat)])
        print("Extraindo características VGG do conjunto 2...")
        features2_vgg = np.array([extract_features(f) for f in tqdm(frag2_flat)])

        # Normalização dos vetores de características VGG
        norm1 = np.linalg.norm(features1_vgg, axis=1, keepdims=True)
        norm2 = np.linalg.norm(features2_vgg, axis=1, keepdims=True)
        features1_vgg = np.divide(features1_vgg, norm1, out=np.zeros_like(features1_vgg), where=norm1 != 0)
        features2_vgg = np.divide(features2_vgg, norm2, out=np.zeros_like(features2_vgg), where=norm2 != 0)

    # Processamento de cor (conversão para YUV se solicitado)
    frag1_proc_color = frag1_flat.astype(np.uint8)
    frag2_proc_color = frag2_flat.astype(np.uint8)
    if yuv:
        print("Convertendo imagens para YUV...")
        frag1_proc_color = np.array([covert_to_YUV(f) for f in frag1_flat])
        frag2_proc_color = np.array([covert_to_YUV(f) for f in frag2_flat])

    # Cálculo das características Sobel (se o peso for maior que zero)
    sobel1 = np.zeros_like(frag1_flat, dtype=np.uint8)
    sobel2 = np.zeros_like(frag2_flat, dtype=np.uint8)
    if peso_sobel > 0:
        print("Calculando características Sobel para o conjunto 1...")
        sobel1 = np.array([sobel(f) for f in tqdm(frag1_flat)])
        print("Calculando características Sobel para o conjunto 2...")
        sobel2 = np.array([sobel(f) for f in tqdm(frag2_flat)])

    # Cálculo da matriz de custo (GPU ou CPU)
    cost_matrix = None
    if cuda.is_available():
        print("\n==> GPU com suporte a CUDA detectada. Usando GPU para cálculo. <==\n")
        cost_matrix = calc_cost_matrix_cuda(
            features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, sobel1, sobel2,
            n, peso_cor, peso_vgg, peso_sobel
        )
    else:
        print("\n==> GPU com CUDA não encontrada. Usando CPU para cálculo. <==\n")
        cost_matrix = calc_cost_matrix(
            features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, sobel1, sobel2,
            n, peso_cor, peso_vgg, peso_sobel
        )

    # Resolução do problema de atribuição
    print("Resolvendo atribuição com Algoritmo do Jonker-Volgenant (lap.lapjv)...")
    cost, col_ind, _ = lap.lapjv(cost_matrix.astype(np.float32))
    print(f"Custo total da atribuição: {cost}")

    # Reconstrução da imagem final
    print("Reconstruindo a imagem final...")
    output_array = np.zeros((h * fh, w * fw, 3), dtype=np.uint8)
    for idx, frag_idx in enumerate(col_ind):
        i, j = divmod(idx, w)
        output_array[i * fh:(i + 1) * fh, j * fw:(j + 1) * fw] = frag2_flat[frag_idx]

    print("Processo finalizado.")
    return output_array


@njit(parallel=True)
def calc_cost_matrix(features1_vgg, features2_vgg, frag1_proc_color, frag2_proc_color, sobel1, sobel2, n, peso_cor,
                       peso_vgg, peso_sobel):
    """Calcula a matriz de custo na CPU."""
    cost_matrix = np.zeros((n, n), dtype=np.float32)
    print("Calculando matriz de custo combinada na CPU...")
    for i in prange(n):
        for j in prange(n):
            # Similaridade de cor
            sim_cor = comp_imgs_dif(frag1_proc_color[i], frag2_proc_color[j]) if peso_cor > 0 else 0.0
            # Similaridade VGG
            sim_vgg = np.dot(features1_vgg[i], features2_vgg[j]) if peso_vgg > 0 else 0.0
            # Similaridade Sobel
            sim_sobel = comp_sobel_dif(sobel1[i], sobel2[j]) if peso_sobel > 0 else 0.0

            # Combinação ponderada das similaridades
            final_similarity = (sim_cor * peso_cor) + (sim_vgg * peso_vgg) + (sim_sobel * peso_sobel)
            cost_matrix[i, j] = 1.0 - final_similarity
    return cost_matrix


@cuda.jit
def calc_cost_matrix_kernel(
        features1_vgg, features2_vgg,
        frag1_proc_color, frag2_proc_color,
        sobel1, sobel2,
        cost_matrix,
        peso_cor, peso_vgg, peso_sobel
):
    """Kernel CUDA para calcular a matriz de custo na GPU."""
    i, j = cuda.grid(2)
    if i < cost_matrix.shape[0] and j < cost_matrix.shape[1]:
        # Similaridade de cor
        sim_cor = cu_comp_imgs_dif(frag1_proc_color[i], frag2_proc_color[j]) if peso_cor > 0 else 0.0

        # Similaridade VGG
        sim_vgg = 0.0
        if peso_vgg > 0:
            for k in range(features1_vgg.shape[1]):
                sim_vgg += features1_vgg[i, k] * features2_vgg[j, k]

        # Similaridade Sobel
        sim_sobel = cu_comp_sobel_dif(sobel1[i], sobel2[j]) if peso_sobel > 0 else 0.0

        # Combinação ponderada e custo final
        final_similarity = (sim_cor * peso_cor) + (sim_vgg * peso_vgg) + (sim_sobel * peso_sobel)
        cost_matrix[i, j] = 1.0 - final_similarity


def calc_cost_matrix_cuda(
        features1_vgg, features2_vgg,
        frag1_proc_color, frag2_proc_color,
        sobel1, sobel2,
        n, peso_cor, peso_vgg, peso_sobel
):
    """Orquestra o cálculo da matriz de custo na GPU."""
    print("Iniciando cálculo da matriz de custo na GPU...")

    # Transferir dados do Host (CPU) para o Device (GPU)
    print("Movendo dados para a memória da GPU...")
    d_features1_vgg = cuda.to_device(features1_vgg)
    d_features2_vgg = cuda.to_device(features2_vgg)
    d_frag1_proc_color = cuda.to_device(frag1_proc_color)
    d_frag2_proc_color = cuda.to_device(frag2_proc_color)
    d_sobel1 = cuda.to_device(sobel1)
    d_sobel2 = cuda.to_device(sobel2)
    d_cost_matrix = cuda.device_array((n, n), dtype=np.float32)

    # Configuração de lançamento do Kernel
    threads_per_block = (16, 16)
    blocks_per_grid_x = int(np.ceil(n / threads_per_block[0]))
    blocks_per_grid_y = int(np.ceil(n / threads_per_block[1]))
    blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)

    # Lançar o Kernel
    print(f"Lançando kernel com grade {blocks_per_grid} e blocos {threads_per_block}...")
    calc_cost_matrix_kernel[blocks_per_grid, threads_per_block](
        d_features1_vgg, d_features2_vgg,
        d_frag1_proc_color, d_frag2_proc_color,
        d_sobel1, d_sobel2,
        d_cost_matrix,
        peso_cor, peso_vgg, peso_sobel
    )

    # Copiar o resultado de volta para o Host
    print("Copiando resultado de volta para a memória do CPU...")
    cost_matrix = d_cost_matrix.copy_to_host()

    print("Cálculo na GPU finalizado.")
    return cost_matrix
