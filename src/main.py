import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from src.Features.Color import replace
from src.Fragmentos import LoadImage, get_fragmentos, SaveImage


def get_process_count():
    max_cpus = cpu_count()
    print(f"\nSeu sistema tem {max_cpus} núcleos de CPU disponíveis")

    while True:
        try:
            num_processes = int(input(f"Quantos processos deseja utilizar (1-{max_cpus})? "))
            if 1 <= num_processes <= max_cpus:
                return num_processes
            print(f"Por favor, insira um número entre 1 e {max_cpus}")
        except ValueError:
            print("Por favor, insira um número válido")


def process_frame(args):
    i, yuv_flag = args
    try:
        img_2 = LoadImage(f"imgs/frierin_bad_apple.png")
        img_1 = LoadImage(f"imgs/frames_bad_apple/{i + 1:03d}.jpg")

        fragmentos_1 = get_fragmentos(img_1, 10)
        fragmentos_2 = get_fragmentos(img_2, 10)

        replaced_img = replace(fragmentos_1, fragmentos_2, yuv=yuv_flag)
        SaveImage(replaced_img, f"imgs/frames_bad_apple_replaced/{i + 1:03d}.jpg")

        return True
    except Exception as e:
        print(f"\nErro ao processar frame {i}: {str(e)}")
        return False


def process_chunk(start, end, num_processes, yuv=False):
    tasks = [(i, yuv) for i in range(start, end)]

    with Pool(processes=num_processes) as pool:
        with tqdm(total=len(tasks), desc=f"Processando {start}-{end}", unit='frame') as pbar:
            results = []
            for result in pool.imap_unordered(process_frame, tasks):
                pbar.update(1)
                results.append(result)

            success_rate = (sum(results) / len(results)) * 100
            print(f"\nIntervalo {start}-{end} concluído com {success_rate:.2f}% de sucesso")


def main():
    # Configuração inicial
    full_end = len(os.listdir("imgs/frames_bad_apple/"))

    # Obter número de processos desejado
    num_processes = get_process_count()
    print(f"\nIniciando processamento com {num_processes} processos...")

    # Dividir o trabalho em partes
    chunk_size = max(1, full_end // num_processes)
    ranges = []
    for i in range(num_processes):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_processes - 1 else full_end
        ranges.append((start, end))

    # Processar cada parte
    for start, end in ranges:
        process_chunk(start, end, num_processes)

    print("\nProcessamento concluído!")


if __name__ == "__main__":
    main()