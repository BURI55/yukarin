"""
extract acoustic params.
"""

import argparse
import glob
import multiprocessing
from pathlib import Path
from pprint import pprint

import tqdm

from yukarin.acoustic_feature import AcousticFeature
from yukarin.param import AcousticParam
from yukarin.utility.json_utility import save_arguments
from yukarin.wave import Wave

base_acoustic_param = AcousticParam()

parser = argparse.ArgumentParser()
parser.add_argument('--input_glob', '-i')
parser.add_argument('--output', '-o', type=Path)
parser.add_argument('--sampling_rate', type=int, default=base_acoustic_param.sampling_rate)
parser.add_argument('--pad_second', type=float, default=base_acoustic_param.pad_second)
parser.add_argument('--threshold_db', type=float, default=base_acoustic_param.threshold_db)
parser.add_argument('--frame_period', type=float, default=base_acoustic_param.frame_period)
parser.add_argument('--order', type=int, default=base_acoustic_param.order)
parser.add_argument('--alpha', type=float, default=base_acoustic_param.alpha)
parser.add_argument('--f0_floor', type=float, default=base_acoustic_param.f0_floor)
parser.add_argument('--f0_ceil', type=float, default=base_acoustic_param.f0_ceil)
parser.add_argument('--fft_length', type=int, default=base_acoustic_param.fft_length)
parser.add_argument('--dtype', type=str, default=base_acoustic_param.dtype)
parser.add_argument('--ignore_feature', nargs='+', default=['sp', 'ap'])
parser.add_argument('--enable_overwrite', action='store_true')
arguments = parser.parse_args()
pprint(vars(arguments))


def generate_feature(path: Path):
    out = Path(arguments.output, path.stem + '.npy')
    if out.exists() and not arguments.enable_overwrite:
        return

    # load wave and padding
    wave = Wave.load(path=path, sampling_rate=arguments.sampling_rate)
    wave = wave.pad(pre_second=arguments.pad_second, post_second=arguments.pad_second)

    # make acoustic feature
    feature = AcousticFeature.extract(
        wave=wave,
        frame_period=arguments.frame_period,
        f0_floor=arguments.f0_floor,
        f0_ceil=arguments.f0_ceil,
        fft_length=arguments.fft_length,
        order=arguments.order,
        alpha=arguments.alpha,
        dtype=arguments.dtype,
    )

    if arguments.threshold_db is not None:
        index = wave.get_effective_frame(
            threshold_db=arguments.threshold_db,
            fft_length=arguments.fft_length,
            frame_period=arguments.frame_period,
        )
        feature = feature.indexing(index)

    # save
    feature.save(path=out, validate=True, ignores=arguments.ignore_feature)


def main():
    arguments.output.mkdir(exist_ok=True)
    save_arguments(arguments, arguments.output / 'arguments.json')

    paths = [Path(p) for p in glob.glob(arguments.input_glob)]

    pool = multiprocessing.Pool()
    it = pool.imap(generate_feature, paths)
    list(tqdm.tqdm(it, total=len(paths)))


if __name__ == '__main__':
    main()
