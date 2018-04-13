import zlib, subprocess, os
gzip_compressor = 'gzip'
gzip_decompressor = 'gunzip'
p7z_compressor = '7z'
p7z_decompressor = '7z'

def compress(data_str):
    return zlib.compress(data_str)


def decompress(data_str):
    return zlib.decompress(data_str)


def f1_compress(in_file, compress_type='f1_deflate', decompression=False):
    flag = ''
    ext = ''
    try:
        if 'f1' in compress_type.lower():
            compressor_path = '/Users/radhika/F1-Project/accel/accel-compression/text'
            compressor = compressor_path + '/compressor'
            if compress_type.lower() == 'f1_deflate':
                flag = '-e'
                ext = '.deflate'
            else:
                if compress_type.lower() == 'f1_lzma':
                    flag = '-l'
                    ext = '.lzma-hdr'
                else:
                    if compress_type.lower() == 'f1_gzip_hdr':
                        flag = '-g'
                        ext = '.gz'
                    else:
                        if compress_type.lower() == 'f1_lzma_hdr':
                            flag = '-a'
                            ext = '.7z'
            if decompression:
                flag = flag + ' -d'
                ext = '.plain'
            cmd = '%s %s %s ' % (compressor, flag, in_file)
        else:
            if compress_type.lower() == 'gzip':
                compressor = gzip_compressor
                flag = '-k -f'
                ext = '.gz'
                cmd = '%s %s %s' % (compressor, flag, in_file)
                if decompression:
                    ext = '.plain'
                    cmd = '%s -c % s > %s' % (gzip_decompressor, in_file, in_file + ext)
            else:
                if compress_type.lower() == '7z':
                    compressor = p7z_compressor
                    flag = 'a'
                    ext = '.7z'
                    cmd = '%s %s %s %s' % (compressor, flag, in_file + ext, in_file)
                    if decompression:
                        flag = 'e'
                        ext = '.plain'
                        cmd = '%s -so %s %s > %s' % (compressor, flag, in_file, in_file + ext)
                else:
                    return 'Error: Unrecognized compressor'
        subprocess.check_call(cmd, shell=True)
        return in_file + ext
    except subprocess.CalledProcessError as err:
        return 'Error: %s' % err.message


def test_f1_compress(in_file, compress_type, decompress_type=None):
    result = 'Failure'
    compress_file = f1_compress(in_file, compress_type=compress_type)
    if 'Error' not in compress_file:
        if decompress_type:
            compress_type = decompress_type
        decompress_file = f1_compress(compress_file, compress_type=compress_type, decompression=True)
        if 'Error' not in decompress_file:
            result = compare_results(in_file, compress_file, decompress_file)
    return result


def compare_results(orig_file, compress_file, decompress_file):
    try:
        orig_md5sum = subprocess.check_output(['md5sum %s' % orig_file], shell=True).split()[0]
        decompress_md5sum = subprocess.check_output(['md5sum %s' % decompress_file], shell=True).split()[0]
        if orig_md5sum == decompress_md5sum:
            input_len = os.path.getsize(orig_file)
            compressed_len = os.path.getsize(compress_file)
            if compressed_len < input_len:
                compress_ratio = (input_len - compressed_len) / float(input_len) * 100
                return 'Success, Data compressed by %.2f' % compress_ratio
            return 'Success, Data not compressed'
        else:
            return 'Failure, Original != Uncompressed'
    except subprocess.CalledProcessError as err:
        return 'Error: %s' % err.message
