from .ell_config import CutStatus
from math import sqrt
from typing import Tuple


class EllCalc:
    """The `EllCalc` class is used for calculating ellipsoid parameters and has attributes
    for storing constants and configuration options.

    Examples:
        >>> from ellalgo.ell_calc import EllCalc
        >>> calc = EllCalc(3)
    """

    use_parallel_cut: bool = True

    _n_f: float
    _half_n: float
    _cst0: float
    _cst1: float
    _cst2: float
    _cst3: float

    def __init__(self, n: int) -> None:
        """
        The function initializes several variables based on the input value.

        :param n: The parameter `n` represents an integer value. It is used to initialize the `EllCalc`
        object
        :type n: int

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
            >>> calc._n_f
            3.0
            >>> calc._half_n
            1.5
            >>> calc._cst0
            0.25
            >>> calc._cst1
            1.125
            >>> calc._cst2
            0.5
            >>> calc._cst3
            0.75
        """
        self._n_f = float(n)
        self._half_n = self._n_f / 2.0
        self._cst0 = 1.0 / (self._n_f + 1.0)
        self._cst1 = self._n_f**2 / (self._n_f**2 - 1.0)
        self._cst2 = 2.0 * self._cst0
        self._cst3 = self._n_f * self._cst0

    def calc_single_or_ll(
        self, beta, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """single deep cut or parallel cut

        The `calc_single_or_ll` function calculates either a single deep cut or a parallel cut based on
        the input parameters.

        :param beta: The parameter `beta` can be of type `int`, `float`, or a list of two elements
        :param tsq: The `tsq` parameter is a floating-point number that represents the square of the
        tolerance for the ellipsoid algorithm. It is used in the calculations performed by the
        `calc_single_or_ll` method
        :type tsq: float
        :return: The function `calc_single_or_ll` returns a tuple containing the following elements:

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
        """
        if isinstance(beta, (int, float)):
            return self.calc_dc(beta, tsq)
        elif len(beta) < 2 or not self.use_parallel_cut:  # unlikely
            return self.calc_dc(beta[0], tsq)
        return self.calc_ll(beta[0], beta[1], tsq)

    def calc_single_or_ll_cc(
        self, beta, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """single central cut or parallel cut

        The function `calc_single_or_ll_cc` calculates either a single central cut or a parallel cut
        based on the input parameters.

        :param beta: The parameter `beta` is of type `_type_` and represents some value. The specific
        details of its purpose and usage are not provided in the code snippet
        :param tsq: tsq is a float value representing the squared t-value
        :type tsq: float
        :return: a tuple containing the following elements:
        1. CutStatus: The status of the cut calculation.
        2. float: The calculated value.
        3. float: The calculated value.
        4. float: The calculated value.

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(4)
            >>> calc.calc_single_or_ll_cc([0, 0.11], 0.01)
            (<CutStatus.Success: 0>, 0.020000000000000004, 0.4, 1.0666666666666667)
            >>> calc.calc_single_or_ll_cc([0, -1], 0.01)
            (<CutStatus.NoSoln: 1>, 0.0, 0.0, 0.0)
        """
        if isinstance(beta, (int, float)) or len(beta) < 2 or not self.use_parallel_cut:
            return self.calc_cc(tsq)
        return self.calc_ll_cc(beta[1], tsq)

    #
    #             ⎛                      ╱     ╱    ⎞
    #            -τ                0    β0    β1    +τ
    #             ⎝                    ╱     ╱      ⎠
    def calc_ll(
        self, b0: float, b1: float, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """parallel deep cut

        The function `calc_ll` calculates the parallel deep cut based on the given parameters.

        :param b0: The parameter `b0` represents a float value
        :type b0: float
        :param b1: The parameter `b1` represents a float value
        :type b1: float
        :param tsq: tsq is a float representing the value of tsq
        :type tsq: float
        :return: The function `calc_ll` returns a tuple of type `Tuple[CutStatus, float, float, float]`.
        """
        if b1 < b0:
            return (CutStatus.NoSoln, 0.0, 0.0, 0.0)  # no sol'n
        # if b0 == 0.0:
        #     return self.calc_ll_cc(b1)
        b1sq = b1 * b1
        if b1 > 0.0 and tsq < b1sq:
            return self.calc_dc(b0, tsq)
        b0b1 = b0 * b1
        return self.calc_ll_core(b0, b1, b1sq, b0b1, tsq)

    #                  2    2
    #            ζ  = τ  - β
    #             0         0
    #
    #                  2    2
    #            ζ  = τ  - β
    #             1         1
    #                       __________________________
    #                      ╱                         2
    #                     ╱           ⎛    ⎛ 2    2⎞⎞
    #                    ╱            ⎜n ⋅ ⎜β  - β ⎟⎟
    #                   ╱             ⎜    ⎝ 1    0⎠⎟
    #            ξ =   ╱    ζ  ⋅ ζ  + ⎜─────────────⎟
    #                ╲╱      0    1   ⎝      2      ⎠
    #
    #                            ⎛ 2              ⎞
    #                        2 ⋅ ⎜τ  + β  ⋅ β  - ξ⎟
    #                  n         ⎝      0    1    ⎠
    #            σ = ───── + ──────────────────────
    #                n + 1                       2
    #                         (n + 1) ⋅ ⎛β  + β ⎞
    #                                   ⎝ 0    1⎠
    #
    #                σ ⋅ ⎛β  + β ⎞
    #                    ⎝ 0    1⎠
    #            ϱ = ─────────────
    #                      2
    #
    #                     ⎛ζ  + ζ     ⎞
    #                 2   ⎜ 0    1   ξ⎟
    #                n  ⋅ ⎜─────── + ─⎟
    #                     ⎝   2      n⎠
    #            δ = ──────────────────
    #                   ⎛ 2    ⎞    2
    #                   ⎝n  - 1⎠ ⋅ τ
    #
    def calc_ll_core(
        self, b0: float, b1: float, b1sq: float, b0b1: float, tsq
    ) -> Tuple[CutStatus, float, float, float]:
        """Parallel deep cut core

        The `calc_ll_core` function calculates various values based on the input parameters and returns
        them as a tuple.

        :param b0: The parameter `b0` represents a float value
        :type b0: float
        :param b1: The parameter `b1` represents a float value
        :type b1: float
        :param b1sq: b1sq is the square of the value of b1
        :type b1sq: float
        :param b0b1: The parameter `b0b1` represents the product of `b0` and `b1`
        :type b0b1: float
        :param tsq: tsq is a float representing the square of the value t
        :return: a tuple with four elements. The first element is of type `CutStatus`, the second
        element is of type `float`, the third element is of type `float`, and the fourth element is of
        type `float`.
        """
        b0sq = b0 * b0
        t0 = tsq - b0sq
        t1 = tsq - b1sq
        xi = sqrt(t0 * t1 + (self._half_n * (b1sq - b0sq)) ** 2)
        bsumsq = b0sq + 2.0 * b0b1 + b1sq
        sigma = self._cst3 + self._cst2 * (tsq + b0b1 - xi) / bsumsq
        rho = sigma * (b0 + b1) / 2.0
        delta = self._cst1 * ((t0 + t1) / 2.0 + xi / self._n_f) / tsq
        return (CutStatus.Success, rho, sigma, delta)

    #                        __________________________
    #                       ╱                         2
    #                      ╱                  ⎛     2⎞
    #                     ╱                   ⎜n ⋅ β ⎟
    #                    ╱   ⎛ 2    2⎞    2   ⎜     1⎟
    #             ξ =   ╱    ⎜τ  - β ⎟ ⋅ τ  + ⎜──────⎟
    #                 ╲╱     ⎝      1⎠        ⎝   2  ⎠
    #
    #                             ⎛ 2    ⎞
    #                   n     2 ⋅ ⎝τ  - ξ⎠
    #             σ = ───── + ────────────
    #                 n + 1              2
    #                         (n + 1) ⋅ β
    #                                    1
    #
    #                 σ ⋅ β
    #                      1
    #             ϱ = ──────
    #                    2
    #
    #                      ⎛      2    ⎞
    #                      ⎜     β     ⎟
    #                  2   ⎜ 2    1   ξ⎟
    #                 n  ⋅ ⎜τ  - ── + ─⎟
    #                      ⎝      2   n⎠
    #             δ = ──────────────────
    #                    ⎛ 2    ⎞    2
    #                    ⎝n  - 1⎠ ⋅ τ
    #
    def calc_ll_cc(
        self, b1: float, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """Parallel central cut

        The function `calc_ll_cc` calculates the parallel central cut for given values of `b1` and
        `tsq`.

        :param b1: The parameter `b1` represents a float value. It is used in the calculation of the
        central cut
        :type b1: float
        :param tsq: The parameter `tsq` represents the square of a value
        :type tsq: float
        :return: The function `calc_ll_cc` returns a tuple of four values: `CutStatus`, `float`,
        `float`, `float`.

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(4)
            >>> calc.calc_ll_cc(0.11, 0.01)
            (<CutStatus.Success: 0>, 0.020000000000000004, 0.4, 1.0666666666666667)
            >>> calc.calc_ll_cc(-1.0, 0.01)
            (<CutStatus.NoSoln: 1>, 0.0, 0.0, 0.0)
        """
        if b1 < 0.0:
            return (CutStatus.NoSoln, 0.0, 0.0, 0.0)  # no sol'n
        b1sq = b1 * b1
        if tsq < b1sq or not self.use_parallel_cut:
            return self.calc_cc(tsq)
        # Core calculation
        a1sq = b1sq / tsq
        xi = sqrt(1.0 - a1sq + (self._half_n * a1sq) ** 2)
        sigma = self._cst3 + self._cst2 * (1.0 - xi) / a1sq
        rho = sigma * b1 / 2.0
        # temp = 1.0 - a1sq / 2 + xi / self._n_f
        delta = self._cst1 * (1.0 - a1sq / 2.0 + xi / self._n_f)
        return (CutStatus.Success, rho, sigma, delta)

    #             γ = τ + n ⋅ β
    #
    #                   γ
    #             ϱ = ─────
    #                 n + 1
    #
    #                 2 ⋅ ϱ
    #             σ = ─────
    #                 τ + β
    #
    #                  2   ⎛ 2    2⎞
    #                 n  ⋅ ⎝τ  - β ⎠
    #             δ = ──────────────
    #                  ⎛ 2    ⎞    2
    #                  ⎝n  - 1⎠ ⋅ τ
    #
    def calc_dc(self, beta: float, tsq: float) -> Tuple[CutStatus, float, float, float]:
        """Deep Cut

        The function calculates the deep cut based on the given beta and tsq values.

        :param beta: The parameter `beta` represents a float value
        :type beta: float
        :param tsq: tsq is the square of the value of tau
        :type tsq: float
        :return: The function `calc_dc` returns a tuple of four values: `CutStatus`, `float`, `float`, `float`.

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
            >>> calc.calc_dc(1.0, 4.0)
            (<CutStatus.Success: 0>, 1.25, 0.8333333333333334, 0.84375)
            >>> calc.calc_dc(0.0, 4.0)
            (<CutStatus.Success: 0>, 0.5, 0.5, 1.125)
            >>> calc.calc_dc(1.5, 2.0)
            (<CutStatus.NoSoln: 1>, 0.0, 0.0, 0.0)
        """
        assert beta >= 0.0
        bsq = beta * beta
        if tsq < bsq:
            return (CutStatus.NoSoln, 0.0, 0.0, 0.0)  # no sol'n
        tau = sqrt(tsq)
        return self.calc_dc_core(beta, tau, tau + self._n_f * beta)

    #             γ = τ + n ⋅ β
    #
    #                   γ
    #             ϱ = ─────
    #                 n + 1
    #
    #                 2 ⋅ ϱ
    #             σ = ─────
    #                 τ + β
    #
    #                  2   ⎛ 2    2⎞
    #                 n  ⋅ ⎝τ  - β ⎠
    #             δ = ──────────────
    #                  ⎛ 2    ⎞    2
    #                  ⎝n  - 1⎠ ⋅ τ
    #
    def calc_dc_core(
        self, beta: float, tau: float, gamma: float
    ) -> Tuple[CutStatus, float, float, float]:
        """Deep cut core

        The `calc_dc_core` function calculates the values of `rho`, `sigma`, and `delta` based on the
        given `beta`, `tau`, and `gamma` parameters.

        :param beta: The parameter `beta` represents a value used in the calculation. It is a float
        value
        :type beta: float
        :param tau: The parameter `tau` represents a value used in the calculation of `sigma` and
        `delta`. It is a float value
        :type tau: float
        :param gamma: The parameter `gamma` represents a scaling factor that is multiplied with the
        constant `_cst0` in the calculation
        :type gamma: float
        :return: The function `calc_dc_core` returns a tuple containing the following elements:

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
            >>> calc.calc_dc_core(1.0, 2.0, 2.0 + 3 * 1.0)
            (<CutStatus.Success: 0>, 1.25, 0.8333333333333334, 0.84375)
            >>> calc.calc_dc_core(0.0, 2.0, 2.0)
            (<CutStatus.Success: 0>, 0.5, 0.5, 1.125)

        """
        rho = self._cst0 * gamma
        sigma = self._cst2 * gamma / (tau + beta)
        delta = self._cst1 * (1.0 - (beta / tau) ** 2)
        return (CutStatus.Success, rho, sigma, delta)

    #                  2
    #            σ = ─────
    #                n + 1
    #
    #                  τ
    #            ϱ = ─────
    #                n + 1
    #
    #                   2
    #                  n
    #            δ = ──────
    #                 2
    #                n  - 1
    #
    def calc_cc(self, tsq: float) -> Tuple[CutStatus, float, float, float]:
        """Central Cut

        The `calc_cc` function calculates the central cut values based on the given input.

        :param tsq: tsq is a float representing the value of tau squared
        :type tsq: float
        :return: The function `calc_cc` returns a tuple containing the following elements:

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
            >>> calc.calc_cc(4.0)
            (<CutStatus.Success: 0>, 0.5, 0.5, 1.125)
        """
        rho = self._cst0 * sqrt(tsq)
        sigma = self._cst2
        delta = self._cst1
        return (CutStatus.Success, rho, sigma, delta)

    def calc_single_or_ll_q(
        self, beta, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """single deep cut or parallel cut (discrete)

        The function `calc_single_or_ll_q` calculates the deep cut or parallel cut based on the input
        parameters `beta` and `tsq`.

        :param beta: The parameter `beta` can be either a single value (int or float) or a list of two
        values
        :param tsq: tsq is a float value representing the square of the threshold value
        :type tsq: float
        :return: The function `calc_single_or_ll_q` returns a tuple containing four elements:
        `CutStatus`, `float`, `float`, and `float`.
        """
        if isinstance(beta, (int, float)):
            return self.calc_dc_q(beta, tsq)
        elif len(beta) < 2 or not self.use_parallel_cut:  # unlikely
            return self.calc_dc_q(beta[0], tsq)
        return self.calc_ll_q(beta[0], beta[1], tsq)

    #
    #             ⎛                      ╱     ╱    ⎞
    #            -τ                0    β0    β1    +τ
    #             ⎝                    ╱     ╱      ⎠
    #
    def calc_ll_q(
        self, b0: float, b1: float, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """Parallel deep cut (discrete)

        The function `calc_ll_q` calculates the parallel deep cut for a given set of parameters.

        :param b0: The parameter `b0` represents a float value
        :type b0: float
        :param b1: The parameter `b1` represents a float value
        :type b1: float
        :param tsq: tsq is a float value that represents the square of a variable
        :type tsq: float
        :return: The function `calc_ll_q` returns a tuple of type `Tuple[CutStatus, float, float,
        float]`.
        """
        if b1 < b0:
            return (CutStatus.NoSoln, 0.0, 0.0, 0.0)  # no sol'n
        # if b0 == 0.0:
        #     return self.calc_ll_cc(b1)
        b1sq = b1 * b1
        if b1 > 0.0 and tsq < b1sq:
            return self.calc_dc_q(b0, tsq)
        b0b1 = b0 * b1
        if self._n_f * b0b1 < -tsq:  # for discrete optimization
            return (CutStatus.NoEffect, 0.0, 0.0, 0.0)  # no effect
        # TODO: check b0 + b1 == 0
        return self.calc_ll_core(b0, b1, b1sq, b0b1, tsq)

    def calc_dc_q(
        self, beta: float, tsq: float
    ) -> Tuple[CutStatus, float, float, float]:
        """Deep Cut (discrete)

        The function `calc_dc_q` calculates the deep cut for a given beta and tsq value.

        :param beta: The parameter `beta` represents a float value
        :type beta: float
        :param tsq: tsq is the square of the threshold value. It is a float value that represents the
        threshold squared
        :type tsq: float
        :return: The function `calc_dc_q` returns a tuple of four values: `CutStatus`, `float`, `float`,
        `float`.

        Examples:
            >>> from ellalgo.ell_calc import EllCalc
            >>> calc = EllCalc(3)
            >>> calc.calc_dc_q(0.0, 4.0)
            (<CutStatus.Success: 0>, 0.5, 0.5, 1.125)
            >>> calc.calc_dc_q(1.5, 2.0)
            (<CutStatus.NoSoln: 1>, 0.0, 0.0, 0.0)
            >>> calc.calc_dc_q(-1.5, 4.0)
            (<CutStatus.NoEffect: 2>, 0.0, 0.0, 0.0)
        """
        tau = sqrt(tsq)
        if tau < beta:
            return (CutStatus.NoSoln, 0.0, 0.0, 0.0)  # no sol'n
        gamma = tau + self._n_f * beta
        if gamma <= 0.0:
            return (CutStatus.NoEffect, 0.0, 0.0, 0.0)
        return self.calc_dc_core(beta, tau, gamma)


if __name__ == "__main__":
    from pytest import approx

    ell_calc = EllCalc(4)
    status, rho, sigma, delta = ell_calc.calc_ll_q(0.07, 0.03, 0.01)
    assert status == CutStatus.NoSoln

    status, rho, sigma, delta = ell_calc.calc_ll_q(0.0, 0.05, 0.01)
    assert status == (CutStatus.Success, rho, sigma, delta)
    assert sigma == approx(0.8)
    assert rho == approx(0.02)
    assert delta == approx(1.2)

    status, rho, sigma, delta = ell_calc.calc_ll_q(0.05, 0.11, 0.01)
    assert status == (CutStatus.Success, rho, sigma, delta)
    assert sigma == approx(0.8)
    assert rho == approx(0.06)
    assert delta == approx(0.8)

    # status, rho, sigma, delta = ell_calc.calc_ll(-0.07, 0.07)
    # assert status == CutStatus.NoEffect

    status, rho, sigma, delta = ell_calc.calc_ll_q(0.01, 0.04, 0.01)
    assert status == (CutStatus.Success, rho, sigma, delta)
    assert sigma == approx(0.928)
    assert rho == approx(0.0232)
    assert delta == approx(1.232)

    ell_calc = EllCalc(4)
    assert ell_calc.use_parallel_cut is True
    assert ell_calc._n_f == 4.0
    assert ell_calc._half_n == 2.0
    assert ell_calc._cst0 == 0.2
    # assert ell_calc._cst1 == approx(16.0 / 15.0)
    assert ell_calc._cst2 == 0.4
    assert ell_calc._cst3 == 0.8
    print(ell_calc._cst1)
