import warnings

import numpy as np

try:
    import dask.array as da
except ImportError:
    da = None  # type: ignore


def _validate_pad_output_shape(input_shape, pad_width, output_shape):
    """Validates the output shape of dask.array.pad, raising a RuntimeError if they do not match.
    In the current versions of dask (2.2/2.4), dask.array.pad with mode='reflect' sometimes returns
    an invalid shape.
    """
    isint = lambda i: isinstance(i, int)

    if isint(pad_width):
        pass
    elif len(pad_width) == 2 and all(map(isint, pad_width)):
        pad_width = sum(pad_width)
    elif (
        len(pad_width) == len(input_shape)
        and all(map(lambda x: len(x) == 2, pad_width))
        and all(isint(i) for p in pad_width for i in p)
    ):
        pad_width = np.sum(pad_width, axis=1)
    else:
        # unreachable: dask.array.pad should already have thrown an error
        raise ValueError("Invalid value for `pad_width`")

    if not np.array_equal(np.array(input_shape) + pad_width, output_shape):
        raise RuntimeError(
            "There seems to be something wrong with the shape of the output of dask.array.pad, "
            "try upgrading Dask, use a different pad mode e.g. mode='constant' or first convert "
            "your DataArray/Dataset to one backed by a numpy array by calling the `compute()` method."
            "See: https://github.com/dask/dask/issues/5303"
        )


def pad(array, pad_width, mode="constant", **kwargs):
    padded = da.pad(array, pad_width, mode=mode, **kwargs)
    # workaround for inconsistency between numpy and dask: https://github.com/dask/dask/issues/5303
    if mode == "mean" and issubclass(array.dtype.type, np.integer):
        warnings.warn(
            'dask.array.pad(mode="mean") converts integers to floats. xarray converts '
            "these floats back to integers to keep the interface consistent. There is a chance that "
            "this introduces rounding errors. If you wish to keep the values as floats, first change "
            "the dtype to a float before calling pad.",
            UserWarning,
        )
        return da.round(padded).astype(array.dtype)
    _validate_pad_output_shape(array.shape, pad_width, padded.shape)
    return padded


if da is not None:
    sliding_window_view = da.lib.stride_tricks.sliding_window_view
else:
    sliding_window_view = None
