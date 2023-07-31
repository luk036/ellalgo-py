from typing import Callable, Tuple, Union

import numpy as np

from .ell_calc import EllCalc
from .ell_config import CutStatus
from .ell_typing import SearchSpace, SearchSpaceQ

Mat = np.ndarray
ArrayType = np.ndarray
CutChoice = Union[float, ArrayType]  # single or parallel
Cut = Tuple[ArrayType, CutChoice]


# The `Ell` class represents an ellipsoidal search space.
class Ell(SearchSpace, SearchSpaceQ):
    no_defer_trick: bool = False

    _mq: Mat
    _xc: ArrayType
    _kappa: float
    _tsq: float
    _helper: EllCalc

    def __init__(self, val, xc: ArrayType) -> None:
        """
        The function initializes an object with given values and attributes.

        :param val: The parameter `val` can be either an integer, a float, or a list of numbers. If it
        is an integer or a float, it represents the value of kappa. If it is a list of numbers, it
        represents the diagonal elements of a matrix, mq
        :param xc: The parameter `xc` is of type `ArrayType`, which suggests that it is an array-like
        object. It is used to store the values of `xc` in the `__init__` method. The length of `xc` is
        calculated using `len(xc)` and stored in the variable
        :type xc: ArrayType
        """
        ndim = len(xc)
        self._helper = EllCalc(ndim)
        self._xc = xc
        self._tsq = 0.0
        if isinstance(val, (int, float)):
            self._kappa = val
            self._mq = np.eye(ndim)
        else:
            self._kappa = 1.0
            self._mq = np.diag(val)

    def xc(self) -> ArrayType:
        """
        The function `xc` returns the value of the `_xc` attribute.
        :return: The method `xc` is returning the value of the attribute `_xc`.
        """
        return self._xc

    def set_xc(self, xc: ArrayType) -> None:
        """
        The function sets the value of the variable `_xc` to the input `x`.

        :param x: The parameter `x` is of type `ArrayType`
        :type x: ArrayType
        """
        self._xc = xc

    def tsq(self) -> float:
        """
        The function `tsq` returns the measure of the distance between `xc` and `x*`.
        :return: The method is returning a float value, which represents the measure of the distance between xc and x*.
        """
        return self._tsq

    def update_dc(self, cut) -> CutStatus:
        """
        The function `update_dc` is an implementation of the `SearchSpace` interface that updates the
        cut status based on a given cut.

        :param cut: The `cut` parameter is of type `_type_` and it represents some kind of cut
        :return: a `CutStatus` object.
        """
        return self._update_core(cut, self._helper.calc_single_or_ll)

    def update_cc(self, cut) -> CutStatus:
        """
        The function `update_cc` is an implementation of the `SearchSpace` interface that updates the
        cut status based on a given cut.

        :param cut: The `cut` parameter is of type `_type_` and it represents a cut
        :return: a `CutStatus` object.
        """
        return self._update_core(cut, self._helper.calc_single_or_ll_cc)

    def update_q(self, cut) -> CutStatus:
        """
        The function `update_q` is an implementation of the `SearchSpaceQ` interface that updates the
        cut status based on a given cut.

        :param cut: The `cut` parameter is of type `_type_` and it represents the cut that needs to be
        updated
        :return: a `CutStatus` object.
        """
        return self._update_core(cut, self._helper.calc_single_or_ll_q)

    # private:

    def _update_core(self, cut, cut_strategy: Callable) -> CutStatus:
        """
        The `_update_core` function updates an ellipsoid by applying a cut and a cut strategy.

        :param cut: The `cut` parameter is of type `_type_` and represents the cut to be applied to the
        ellipsoid. The specific type of `_type_` is not specified in the code snippet provided
        :param cut_strategy: The `cut_strategy` parameter is a callable object that represents the
        strategy for determining the cut status. It takes two arguments: `beta` and `tsq`. `beta` is a
        scalar value and `tsq` is a scalar value representing the squared norm of the current cut. The `
        :type cut_strategy: Callable
        :return: a `CutStatus` object.

        Examples:
            >>> ell = Ell(1.0, [1.0, 1.0, 1.0, 1.0])
            >>> cut = (np.array([1.0, 1.0, 1.0, 1.0]), 1.0)
            >>> status = ell._update_core(cut, ell._helper.calc_single_or_ll)
            >>> print(status)
            CutStatus.Success

            >>> ell = Ell(1.0, [1.0, 1.0, 1.0, 1.0])
            >>> cut = (np.array([1.0, 1.0, 1.0, 1.0]), 1.0)
            >>> status = ell._update_core(cut, ell._helper.calc_single_or_ll_cc)
            >>> print(status)
            CutStatus.Success
        """
        grad, beta = cut
        grad_t = self._mq @ grad  # n^2 multiplications
        omega = grad.dot(grad_t)  # n multiplications
        self._tsq = self._kappa * omega

        status, rho, sigma, delta = cut_strategy(beta, self._tsq)

        if status != CutStatus.Success:
            return status

        self._xc -= (rho / omega) * grad_t
        self._mq -= (sigma / omega) * np.outer(grad_t, grad_t)
        self._kappa *= delta

        if self.no_defer_trick:
            self._mq *= self._kappa
            self._kappa = 1.0
        return status
