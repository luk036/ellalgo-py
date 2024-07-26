"""
Test Quasiconvex (without Round Robin)
"""
from __future__ import print_function

import math

import numpy as np
from pytest import approx

from ellalgo.cutting_plane import OracleOptim, cutting_plane_optim
from ellalgo.ell import Ell


class MyQuasicvxOracle(OracleOptim):
    """
    The `MyQuasicvxOracle` class in Python defines a function `assess_optim` that assesses the
    optimality of a given point based on constraints and an objective function.
    """

    def assess_optim(self, xc, gamma: float):
        """
        This Python function assesses the optimality of a given point based on constraints and an objective
        function.
        
        :param xc: The `xc` parameter in the `assess_optim` function represents a tuple containing two
        values, denoted as `x` and `y`. These values are used in the calculations and constraints within the
        function to assess the optimality of a given solution
        :param gamma: Gamma is a float value representing the best-so-far optimal value in the
        `assess_optim` function
        :type gamma: float
        :return: The `assess_optim` function returns a tuple containing two elements. The first element is a
        tuple containing the gradient vector and the constraint violation value. The second element is
        either `None` or the value of the updated `gamma` parameter.
        """
        x, y = xc

        # constraint 1: exp(x) <= y
        tmp = math.exp(x)
        if (fj := tmp - y) > 0.0:
            return (np.array([tmp, -1.0]), fj), None

        # constraint 2: y > 0
        if y <= 0.0:
            return (np.array([0.0, -1.0]), -y), None

        # constraint 3: x > 0
        if x <= 0.0:
            return (np.array([-1.0, 0.0]), -x), None

        # objective: minimize -sqrt(x) / y
        tmp2 = math.sqrt(x)
        if (fj := -tmp2 - gamma * y) >= 0.0:  # infeasible
            return (np.array([-0.5 / tmp2, -gamma]), fj), None
        gamma = -tmp2 / y
        return (np.array([-0.5 / tmp2, -gamma]), 0), gamma


def test_case_feasible():
    """
    The function `test_case_feasible` tests the feasibility of a specific optimization problem using
    cutting plane optimization.
    """
    xinit = np.array([1.0, 1.0])  # initial xinit
    ellip = Ell(10.0, xinit)
    omega = MyQuasicvxOracle()
    xbest, fbest, _ = cutting_plane_optim(omega, ellip, 0.0)
    assert xbest is not None
    assert fbest == approx(-0.42888194247600586)
    assert xbest[0] == approx(0.5000004646814299)
    assert xbest[1] == approx(1.6487220368468205)


def test_case_infeasible1():
    """
    The function `test_case_infeasible1` tests for infeasibility in an optimization problem.
    """
    xinit = np.array([100.0, 100.0])  # wrong initial guess,
    ellip = Ell(10.0, xinit)  # or ellipsoid is too small
    omega = MyQuasicvxOracle()
    xbest, _, _ = cutting_plane_optim(omega, ellip, 0.0)
    assert xbest is None


def test_case_infeasible2():
    """
    The function `test_case_infeasible2` initializes variables and asserts that the result is None.
    """
    xinit = np.array([1.0, 1.0])  # initial xinit
    ellip = Ell(10.0, xinit)
    omega = MyQuasicvxOracle()
    xbest, _, _ = cutting_plane_optim(omega, ellip, -100)  # wrong init best-so-far
    assert xbest is None
