import argparse
import os
import sys
import tarfile
import time
from compression import bz2, zstd  


def get_compression_mode(archive_path: str) -> str:
    """Автоматически определяет формат по расширению целевого файла."""
    if archive_path.endswith('.zst'):
        return 'zstd'
    elif archive_path.endswith('.bz2'):
        return 'bz2'
    else:
        print(f"Ошибка: Неподдерживаемый формат архива '{archive_path}'. Используйте .zst или .bz2")
        sys.exit(1)


def compress(source: str, archive: str):
    """Архивирует файл или директорию."""
    if not os.path.exists(source):
        print(f"Ошибка: Источник '{source}' не существует.")
        sys.exit(1)

    mode = get_compression_mode(archive)
    start_time = time.perf_counter()

    is_dir = os.path.isdir(source)
    temp_tar = None

    try:
        
        if is_dir:
            print(f"[1/2] Сборка директории '{source}' в промежуточный TAR...")
            temp_tar = archive + ".tmp.tar"
            with tarfile.open(temp_tar, "w") as tar:
                tar.add(source, arcname=os.path.basename(source))
            input_file = temp_tar
        else:
            input_file = source

        print(f"[2/2] Сжатие методом {mode} -> '{archive}'...")
        
        
        open_func = zstd.open if mode == 'zstd' else bz2.open

        with open(input_file, 'rb') as f_in:
            with open_func(archive, 'wb') as f_out:
                
                while chunk := f_in.read(64 * 1024):
                    f_out.write(chunk)

        end_time = time.perf_counter()
        print(f"Успешно заархивировано за {end_time - start_time:.4f} сек.")

    except Exception as e:
        print(f"Произошла ошибка при архивации: {e}")
        if os.path.exists(archive):
            os.remove(archive)
        sys.exit(1)
    finally:
        
        if temp_tar and os.path.exists(temp_tar):
            os.remove(temp_tar)


def decompress(archive: str, dest_dir: str):
    """Распаковывает файл или tar-архив."""
    if not os.path.exists(archive):
        print(f"Ошибка: Архив '{archive}' не найден.")
        sys.exit(1)

    mode = get_compression_mode(archive)
    start_time = time.perf_counter()

    os.makedirs(dest_dir, exist_ok=True)
    temp_decompressed = archive + ".tmp.extracted"

    try:
        print(f"[1/2] Распаковка слоя сжатия {mode}...")
        open_func = zstd.open if mode == 'zstd' else bz2.open

        with open_func(archive, 'rb') as f_in:
            with open(temp_decompressed, 'wb') as f_out:
                while chunk := f_in.read(64 * 1024):
                    f_out.write(chunk)

        
        if tarfile.is_tarfile(temp_decompressed):
            print(f"[2/2] Извлечение директории из TAR в '{dest_dir}'...")
            with tarfile.open(temp_decompressed, "r") as tar:
                tar.extractall(path=dest_dir)
            os.remove(temp_decompressed)
        else:
            
            print(f"[2/2] Извлечение одиночного файла в '{dest_dir}'...")
            out_filename = os.path.basename(archive).rsplit('.', 1)[0]
            final_path = os.path.join(dest_dir, out_filename)
            os.replace(temp_decompressed, final_path)

        end_time = time.perf_counter()
        print(f"Успешно распаковано в '{dest_dir}' за {end_time - start_time:.4f} сек.")

    except Exception as e:
        print(f"Произошла ошибка при распаковке: {e}")
        if os.path.exists(temp_decompressed):
            os.remove(temp_decompressed)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Консольный архиватор/распаковщик (.zst / .bz2) на Python 3.14"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Режим работы")

    
    pack_parser = subparsers.add_parser("c", help="Заархивировать файл или папку")
    pack_parser.add_argument("source", help="Путь к исходному файлу или директории")
    pack_parser.add_argument("archive", help="Путь к создаваемому архиву (с расширением .zst или .bz2)")

    
    unpack_parser = subparsers.add_parser("x", help="Распаковать архив")
    unpack_parser.add_argument("archive", help="Путь к архиву (.zst или .bz2)")
    unpack_parser.add_argument("dest", help="Путь к папке назначения для распаковки")

    args = parser.parse_args()

    if args.command == "c":
        compress(args.source, args.archive)
    elif args.command == "x":
        decompress(args.archive, args.dest)


if __name__ == "__main__":
    main()
