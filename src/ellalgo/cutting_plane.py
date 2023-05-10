# from .ell_config import CutStatus, Options
from .ell_config import CutStatus, Options
import copy

from abc import abstractmethod
from typing import Optional, Tuple, Union
from typing import Generic, TypeVar
from collections.abc import MutableSequence

T = TypeVar('T')


CutChoice = Union[float, MutableSequence]  # single or parallel
ArrayType = TypeVar("ArrayType")
Cut = Tuple[ArrayType, CutChoice]
Num = Union[float, int]


class OracleFeas(Generic[ArrayType]):
    @abstractmethod
    def assess_feas(self, xc: ArrayType) -> Optional[Cut]:
        pass


class OracleFeas2(OracleFeas[ArrayType]):
    @abstractmethod
    def update(self, tea: Num) -> None:
        pass


class OracleOptim(Generic[ArrayType]):
    @abstractmethod
    def assess_optim(
        self, xc: ArrayType, tea: float  # what?
    ) -> Tuple[Cut, Optional[float]]:
        pass


class OracleFeasQ(Generic[ArrayType]):
    @abstractmethod
    def assess_feas_q(
        self, xc: ArrayType, retry: bool
    ) -> Tuple[Optional[Cut], Optional[ArrayType], bool]:
        pass


class OracleOptimQ(Generic[ArrayType]):
    @abstractmethod
    def assess_optim_q(
        self, xc: ArrayType, tea: float, retry: bool
    ) -> Tuple[Cut, ArrayType, Optional[float], bool]:
        pass


class OracleBS(Generic[ArrayType]):
    @abstractmethod
    def assess_bs(self, tea: Num) -> bool:
        pass


class SearchSpace(Generic[ArrayType]):
    @abstractmethod
    def update_dc(self, cut: Cut) -> CutStatus:
        pass

    @abstractmethod
    def update_cc(self, cut: Cut) -> CutStatus:
        pass

    @abstractmethod
    def xc(self) -> ArrayType:
        pass

    @abstractmethod
    def tsq(self) -> float:
        pass


class SearchSpaceQ(Generic[ArrayType]):
    @abstractmethod
    def update_q(self, cut: Cut) -> CutStatus:
        pass

    @abstractmethod
    def xc(self) -> ArrayType:
        pass

    @abstractmethod
    def tsq(self) -> float:
        pass


class SearchSpace2(SearchSpace[ArrayType]):
    @abstractmethod
    def set_xc(self, xc: ArrayType) -> None:
        pass


def cutting_plane_feas(
    omega: OracleFeas[ArrayType], space: SearchSpace[ArrayType], options=Options()
) -> Tuple[Optional[ArrayType], int]:
    """Find a point in a convex set (defined through a cutting-plane oracle).

    Description:
        A function f(x) is *convex* if there always exist a g(x)
        such that f(z) >= f(x) + g(x)' * (z - x), forall z, x in dom f.
        Note that dom f does not need to be a convex set in our definition.
        The affine function g' (x - xc) + beta is called a cutting-plane,
        or a ``cut'' for short.
        This algorithm solves the following feasibility problem:

                find x
                s.t. f(x) <= 0,

        A *separation oracle* asserts that an evalution point x0 is feasible,
        or provide a cut that separates the feasible region and x0.

         ┌────────────┐    ┌───────────┐┌──────────┐
         │CuttingPlane│    │SearchSpace││OracleFeas│
         └─────┬──────┘    └─────┬─────┘└────┬─────┘
               │                 │           │
               │   request xc    │           │
               │────────────────>│           │
               │                 │           │
               │    return xc    │           │
               │<────────────────│           │
               │                 │           │
               │       assess_feas(xc)       │
               │────────────────────────────>│
               │                 │           │
               │         return cut          │
               │<────────────────────────────│
               │                 │           │
               │update by the cut│           │
               │────────────────>│           │
         ┌─────┴──────┐    ┌─────┴─────┐┌────┴─────┐
         │CuttingPlane│    │SearchSpace││OracleFeas│
         └────────────┘    └───────────┘└──────────┘

    Arguments:
        omega (OracleFeas): perform assessment on xinit
        space (SearchSpace): Initial search space known to contain x*

    Keyword Arguments:
        options (Options): [description] (default: {Options()})

    Returns:
        feasible (bool): whether it is feasible
        niter (int): number of iterations performed
        status (CutStatus): cut status
    """
    for niter in range(options.max_iters):
        cut = omega.assess_feas(space.xc())  # query the oracle at space.xc()
        if cut is None:  # feasible sol'n obtained
            return space.xc(), niter
        status = space.update_dc(cut)  # update space
        if status != CutStatus.Success or space.tsq() < options.tol:
            return None, niter
    return None, options.max_iters


def cutting_plane_optim(
    omega: OracleOptim[ArrayType], space: SearchSpace[ArrayType], tea: float, options=Options()
) -> Tuple[Optional[ArrayType], float, int]:
    """Cutting-plane method for solving convex optimization problem

    Arguments:
        omega (OracleOptim): perform assessment on xinit
        space (SearchSpace): Search Space containing x*
        tea (float): initial best-so-far value

    Keyword Arguments:
        options ([type]): [description] (default: {Options()})

    Returns:
        x_best (Any): solution vector
        tea: final best-so-far value
        ret {CInfo}
    """
    x_best = None
    for niter in range(options.max_iters):
        cut, t1 = omega.assess_optim(space.xc(), tea)
        if t1 is not None:  # better t obtained
            tea = t1
            x_best = copy.copy(space.xc())
            status = space.update_cc(cut)
        else:
            status = space.update_dc(cut)
        if status != CutStatus.Success or space.tsq() < options.tol:
            return x_best, tea, niter
    return x_best, tea, options.max_iters


def cutting_plane_feas_q(
        omega: OracleFeasQ[ArrayType], space_q: SearchSpaceQ[ArrayType], options=Options()
) -> Tuple[Optional[ArrayType], int]:
    """Cutting-plane method for solving convex discrete optimization problem

    Arguments:
        omega (OracleFeasQ): perform assessment on xinit
        space ([type]): Search Space containing x*

    Keyword Arguments:
        options ([type]): [description] (default: {Options()})

    Returns:
        x_best (float): solution vector
        niter ([type]): number of iterations performed
    """
    # x_last = space.xc()
    retry = False
    for niter in range(options.max_iters):
        cut, x_q, more_alt = omega.assess_feas_q(space_q.xc(), retry)
        if cut is None:  # better t obtained
            return x_q, niter
        status = space_q.update_q(cut)
        if status == CutStatus.Success:
            retry = False
        elif status == CutStatus.NoSoln:
            return None, niter
        elif status == CutStatus.NoEffect:
            if not more_alt:  # no more alternative cut
                return None, niter
            retry = True
        if space_q.tsq() < options.tol:
            return None, niter
    return None, options.max_iters


def cutting_plane_optim_q(
        omega: OracleOptimQ[ArrayType], space_q: SearchSpaceQ[ArrayType], tea: float, options=Options()
) -> Tuple[Optional[ArrayType], float, int]:
    """Cutting-plane method for solving convex discrete optimization problem

    Arguments:
        omega (OracleOptimQ): perform assessment on xinit
        space ([type]): Search Space containing x*
        tea (float): initial best-so-far value

    Keyword Arguments:
        options ([type]): [description] (default: {Options()})

    Returns:
        x_best (float): solution vector
        tea (float): best-so-far optimal value
        niter ([type]): number of iterations performed
    """
    # x_last = space.xc()
    x_best = None
    retry = False
    for niter in range(options.max_iters):
        cut, x_q, t1, more_alt = omega.assess_optim_q(space_q.xc(), tea, retry)
        if t1 is not None:  # better t obtained
            tea = t1
            x_best = x_q
        status = space_q.update_q(cut)
        if status == CutStatus.Success:
            retry = False
        elif status == CutStatus.NoSoln:
            return x_best, tea, niter
        elif status == CutStatus.NoEffect:
            if not more_alt:  # no more alternative cut
                return x_best, tea, niter
            retry = True
        if space_q.tsq() < options.tol:
            return x_best, tea, niter
    return x_best, tea, options.max_iters


def bsearch(
    omega: OracleBS, intrvl: Tuple[Num, Num], options=Options()
) -> Tuple[Num, int]:
    """[summary]

    Arguments:
        omega ([type]): [description]
        I ([type]): interval (initial search space)

    Keyword Arguments:
        options ([type]): [description] (default: {Options()})

    Returns:
        [type]: [description]
    """
    # assume monotone
    lower, upper = intrvl
    T = type(upper)  # T could be `int`
    for niter in range(options.max_iters):
        tau = (upper - lower) / 2
        if tau < options.tol:
            return upper, niter
        tea = T(lower + tau)
        if omega.assess_bs(tea):  # feasible sol'n obtained
            upper = tea
        else:
            lower = tea
    return upper, options.max_iters


class BSearchAdaptor(Generic[ArrayType]):
    def __init__(
        self, omega: OracleFeas2[ArrayType], space: SearchSpace2[ArrayType], options=Options()
    ) -> None:
        """[summary]

        Arguments:
            omega ([type]): [description]
            space ([type]): [description]

        Keyword Arguments:
            options ([type]): [description] (default: {Options()})
        """
        self.omega = omega
        self.space = space
        self.options = options

    @property
    def x_best(self) -> ArrayType:
        """[summary]

        Returns:
            [type]: [description]
        """
        return self.space.xc()

    def assess_bs(self, tea: Num) -> bool:
        """[summary]

        Arguments:
            t (float): the best-so-far optimal value

        Returns:
            [type]: [description]
        """
        space = copy.deepcopy(self.space)
        self.omega.update(tea)
        x_feas, _ = cutting_plane_feas(self.omega, space, self.options)
        if x_feas is not None:
            self.space.set_xc(x_feas)
            return True
        return False
