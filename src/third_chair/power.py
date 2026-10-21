"""Prospective two-sided paired-t power; standard library, no data or APIs.

Integrate over the chi-square denominator of the noncentral t. Effect is the
mean paired difference divided by its SD, NOT an independent-arm Cohen's d.
Missing pairs are binomial and independent of outcome in this planning model.
"""

import math
from functools import lru_cache


def _beta_fraction(a, b, x):
    tiny = 1e-300
    c, d = 1., 1. - (a + b) * x / (a + 1.)
    d = 1. / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 10001):
        for aa in (m * (b - m) * x / ((a + 2*m - 1) * (a + 2*m)),
                   -(a + m) * (a + b + m) * x / ((a + 2*m) * (a + 2*m + 1))):
            d = 1. + aa * d
            c = 1. + aa / c
            d = 1. / (d if abs(d) > tiny else tiny)
            c = c if abs(c) > tiny else tiny
            delta = d * c
            h *= delta
        if abs(delta - 1.) < 2e-14:
            return h
    raise ArithmeticError("Incomplete beta did not converge")


def _beta(a, b, x):
    if x <= 0:
        return 0.
    if x >= 1:
        return 1.
    factor = math.exp(math.lgamma(a+b) - math.lgamma(a) - math.lgamma(b)
                      + a*math.log(x) + b*math.log1p(-x))
    if x < (a+1)/(a+b+2):
        return factor * _beta_fraction(a, b, x) / a
    return 1. - factor * _beta_fraction(b, a, 1.-x) / b


@lru_cache(maxsize=20000)
def t_critical(df, alpha):
    if type(df) is not int or df < 1 or not 0 < alpha < 1:
        raise ValueError("Positive integer df and 0 < alpha < 1 required")
    low, high = 0., 1.
    def two_sided_tail(t):
        return _beta(df / 2., .5, df / (df + t*t))
    while two_sided_tail(high) > alpha:
        high *= 2
    for _ in range(70):
        mid = (low + high) / 2
        if two_sided_tail(mid) > alpha:
            low = mid
        else:
            high = mid
    return (low + high) / 2


@lru_cache(maxsize=20000)
def paired_t_power(n, effect, alpha=.05, steps=1040):
    if (type(n) is not int or n < 2 or not math.isfinite(effect)
            or effect < 0 or not 0 < alpha < 1 or steps < 260 or steps % 2):
        raise ValueError("Invalid paired-t power parameters")
    df = n - 1
    critical = t_critical(df, alpha)
    ncp = effect * math.sqrt(n)
    # z = log(sqrt(V/df))*sqrt(2df), V ~ chi-square(df).
    # This scale resolves the density even at large n; tails beyond bounds
    # contribute < 1e-11 at df >= 1. Simpson convergence is tested separately.
    scale = math.sqrt(2*df)
    constant = (math.log(2) + df/2*math.log(df/2) - math.lgamma(df/2)
                - math.log(scale))
    h = 52. / steps
    total = 0.
    for i in range(steps + 1):
        u = (-40. + i*h) / scale
        density = math.exp(constant + df*u - df/2*math.exp(2*u))
        threshold = critical * math.exp(u)
        reject = .5 * (math.erfc((threshold-ncp)/math.sqrt(2))
                       + math.erfc((threshold+ncp)/math.sqrt(2)))
        total += (1 if i in (0, steps) else 4 if i % 2 else 2) * density * reject
    return min(1., max(0., total * h / 3))


def scheduled_power(n, effect, alpha=.05, completion=1.):
    """Power averaged over K complete pairs among n planned pairs, K ~ Bin(n,p)."""
    if (type(n) is not int or n < 2 or not 0 < completion <= 1
            or not math.isfinite(effect) or effect <= 0 or not 0 < alpha < 1):
        raise ValueError("Invalid scheduled power parameters")
    if completion == 1:
        return paired_t_power(n, effect, alpha)
    total = 0.
    for k in range(2, n+1):
        log_weight = (math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)
                      + k*math.log(completion) + (n-k)*math.log1p(-completion))
        weight = math.exp(log_weight)
        if weight > 1e-16:
            total += weight * paired_t_power(k, effect, alpha)
    return total


def required_repetitions(effect=.5, target=.9, tests=288, completion=.9, family_alpha=.05):
    if (type(tests) is not int or tests < 1 or not 0 < target < 1
            or not 0 < family_alpha < 1):
        raise ValueError("Invalid power target or multiplicity")
    alpha = family_alpha / tests
    low, high = 1, 2
    while scheduled_power(high, effect, alpha, completion) < target:
        high *= 2
        if high > 100000:
            raise ValueError("Required repetitions exceed supported planning range")
    while high - low > 1:
        mid = (low+high) // 2
        if scheduled_power(mid, effect, alpha, completion) >= target:
            high = mid
        else:
            low = mid
    return high
