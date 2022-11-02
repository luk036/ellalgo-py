# -*- coding: utf-8 -*-
from typing import Tuple, Union

import numpy as np

from .cutting_plane import CutStatus, SearchSpace

Arr = Union[np.ndarray]


class ell1d(SearchSpace):
    __slots__ = ("_rd", "_xc")

    def __init__(self, interval: Tuple[float, float]):
        """[summary]

        Arguments:
            I ([type]): [description]
        """
        l, u = interval
        self._rd: float = (u - l) / 2
        self._xc: float = l + self._rd

    def copy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        E = ell1d([self._xc - self._rd, self._xc + self._rd])
        return E

    # @property
    def xc(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return self._xc

    # @xc.setter
    def set_xc(self, x: float):
        """[summary]

        Arguments:
            x (float): [description]
        """
        self._xc = x

    def update(self, cut: Tuple[float, float]) -> Tuple[CutStatus, float]:
        """Update ellipsoid core function using the cut
                grad' * (x - xc) + beta <= 0

        Note: Support single cut only

        Arguments:
            grad (float): gradient
            beta (float): [description]

        Returns:
            status: 0: success
            tau: "volumn" of ellipsoid
        """
        grad, beta = cut
        # TODO handle grad == 0
        tau = abs(self._rd * grad)
        tsq = tau**2
        # TODO: Support parallel cut
        if beta == 0:
            self._rd /= 2
            self._xc += -self._rd if grad > 0 else self._rd
            return CutStatus.Success, tsq
        if beta > tau:
            return CutStatus.NoSoln, tsq  # no sol'n
        if beta < -tau:  # unlikely
            return CutStatus.NoEffect, tsq  # no effect

        bound = self._xc - beta / grad
        upper = bound if grad > 0 else self._xc + self._rd
        lower = self._xc - self._rd if grad > 0 else bound
        self._rd = (upper - lower) / 2
        self._xc = lower + self._rd
        return CutStatus.Success, tsq
