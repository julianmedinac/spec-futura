"""
Distribution Analyzer Module
Analyzes the statistical distribution of financial returns.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
import warnings


@dataclass
class DistributionStats:
    """Container for distribution statistics."""
    mean: float
    std: float
    variance: float
    skewness: float
    kurtosis: float  # Excess kurtosis (Fisher)
    min: float
    max: float
    median: float
    count: int
    
    # Percentiles
    percentile_1: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    percentile_99: float
    
    # Annualized metrics
    annualized_mean: Optional[float] = None
    annualized_std: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'mean': self.mean,
            'std': self.std,
            'variance': self.variance,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'min': self.min,
            'max': self.max,
            'median': self.median,
            'count': self.count,
            'percentile_1': self.percentile_1,
            'percentile_5': self.percentile_5,
            'percentile_25': self.percentile_25,
            'percentile_75': self.percentile_75,
            'percentile_95': self.percentile_95,
            'percentile_99': self.percentile_99,
            'annualized_mean': self.annualized_mean,
            'annualized_std': self.annualized_std,
        }


@dataclass
class NormalityTest:
    """Container for normality test results."""
    test_name: str
    statistic: float
    p_value: float
    is_normal: bool  # Based on alpha=0.05
    interpretation: str


class DistributionAnalyzer:
    """
    Analyze the statistical distribution of financial returns.
    
    Best Practices Applied:
    ----------------------
    1. Multiple normality tests (single test can be misleading)
    2. Robust estimators for skewness and kurtosis
    3. Value at Risk (VaR) calculations
    4. Fat tail detection and quantification
    5. Annualization of statistics
    """
    
    def __init__(self, returns: pd.Series, periods_per_year: float = 252):
        """
        Initialize analyzer with return data.
        
        Args:
            returns: Series of returns (preferably log returns)
            periods_per_year: Number of periods per year for annualization
        """
        self.returns = returns.dropna()
        self.periods_per_year = periods_per_year
        
        if len(self.returns) < 30:
            warnings.warn("Less than 30 observations. Statistical results may be unreliable.")
    
    def compute_basic_stats(self) -> DistributionStats:
        """
        Compute comprehensive distribution statistics.
        
        Returns:
            DistributionStats object with all statistics
        """
        r = self.returns
        
        # Basic moments
        mean = r.mean()
        std = r.std(ddof=1)  # Sample std with Bessel's correction
        variance = r.var(ddof=1)
        
        # Higher moments
        skewness = stats.skew(r)
        kurtosis = stats.kurtosis(r)  # Excess kurtosis (Fisher)
        
        # Percentiles
        percentiles = np.percentile(r, [1, 5, 25, 50, 75, 95, 99])
        
        # Annualized values
        # Mean: multiply by periods per year
        # Std: multiply by sqrt(periods per year)
        annualized_mean = mean * self.periods_per_year
        annualized_std = std * np.sqrt(self.periods_per_year)
        
        return DistributionStats(
            mean=mean,
            std=std,
            variance=variance,
            skewness=skewness,
            kurtosis=kurtosis,
            min=r.min(),
            max=r.max(),
            median=percentiles[3],
            count=len(r),
            percentile_1=percentiles[0],
            percentile_5=percentiles[1],
            percentile_25=percentiles[2],
            percentile_75=percentiles[4],
            percentile_95=percentiles[5],
            percentile_99=percentiles[6],
            annualized_mean=annualized_mean,
            annualized_std=annualized_std,
        )
    
    def test_normality(self, alpha: float = 0.05) -> Dict[str, NormalityTest]:
        """
        Perform multiple normality tests.
        
        Why multiple tests:
        - Jarque-Bera: Tests skewness and kurtosis
        - Shapiro-Wilk: Most powerful for small samples
        - D'Agostino-Pearson: Omnibus test, good for larger samples
        
        Args:
            alpha: Significance level
            
        Returns:
            Dictionary of test results
        """
        results = {}
        n = len(self.returns)
        
        # Jarque-Bera Test
        try:
            jb_stat, jb_p = stats.jarque_bera(self.returns)
            results['jarque_bera'] = NormalityTest(
                test_name="Jarque-Bera",
                statistic=jb_stat,
                p_value=jb_p,
                is_normal=jb_p > alpha,
                interpretation=self._interpret_normality(jb_p, alpha)
            )
        except Exception as e:
            warnings.warn(f"Jarque-Bera test failed: {e}")
        
        # Shapiro-Wilk Test (for n < 5000)
        if n < 5000:
            try:
                sw_stat, sw_p = stats.shapiro(self.returns)
                results['shapiro_wilk'] = NormalityTest(
                    test_name="Shapiro-Wilk",
                    statistic=sw_stat,
                    p_value=sw_p,
                    is_normal=sw_p > alpha,
                    interpretation=self._interpret_normality(sw_p, alpha)
                )
            except Exception as e:
                warnings.warn(f"Shapiro-Wilk test failed: {e}")
        
        # D'Agostino-Pearson Test (requires n >= 20)
        if n >= 20:
            try:
                da_stat, da_p = stats.normaltest(self.returns)
                results['dagostino_pearson'] = NormalityTest(
                    test_name="D'Agostino-Pearson",
                    statistic=da_stat,
                    p_value=da_p,
                    is_normal=da_p > alpha,
                    interpretation=self._interpret_normality(da_p, alpha)
                )
            except Exception as e:
                warnings.warn(f"D'Agostino-Pearson test failed: {e}")
        
        # Anderson-Darling Test
        try:
            ad_result = stats.anderson(self.returns, dist='norm')
            # Use 5% significance level
            idx = list(ad_result.significance_level).index(5.0)
            is_normal = ad_result.statistic < ad_result.critical_values[idx]
            results['anderson_darling'] = NormalityTest(
                test_name="Anderson-Darling",
                statistic=ad_result.statistic,
                p_value=np.nan,  # AD test doesn't provide p-value directly
                is_normal=is_normal,
                interpretation=f"Statistic {ad_result.statistic:.4f} vs critical value {ad_result.critical_values[idx]:.4f} at 5%"
            )
        except Exception as e:
            warnings.warn(f"Anderson-Darling test failed: {e}")
        
        return results
    
    def _interpret_normality(self, p_value: float, alpha: float) -> str:
        """Interpret normality test p-value."""
        if p_value > alpha:
            return f"Cannot reject normality (p={p_value:.4f} > α={alpha})"
        else:
            return f"Reject normality (p={p_value:.4f} ≤ α={alpha})"
    
    def compute_var(
        self,
        confidence_levels: list = [0.95, 0.99],
        method: str = 'historical'
    ) -> Dict[float, float]:
        """
        Compute Value at Risk.
        
        Methods:
        - historical: Non-parametric, uses actual percentiles
        - parametric: Assumes normal distribution
        - cornish_fisher: Adjusts for skewness and kurtosis
        
        Args:
            confidence_levels: List of confidence levels
            method: VaR calculation method
            
        Returns:
            Dictionary of confidence level to VaR value
        """
        results = {}
        
        for cl in confidence_levels:
            if method == 'historical':
                var = np.percentile(self.returns, (1 - cl) * 100)
            elif method == 'parametric':
                z = stats.norm.ppf(1 - cl)
                var = self.returns.mean() + z * self.returns.std()
            elif method == 'cornish_fisher':
                var = self._cornish_fisher_var(cl)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            results[cl] = var
        
        return results
    
    def _cornish_fisher_var(self, confidence_level: float) -> float:
        """
        Compute Cornish-Fisher VaR adjustment for non-normality.
        
        This adjusts the normal VaR for skewness and kurtosis.
        """
        z = stats.norm.ppf(1 - confidence_level)
        s = stats.skew(self.returns)
        k = stats.kurtosis(self.returns)  # Excess kurtosis
        
        # Cornish-Fisher expansion
        z_cf = (z + 
                (z**2 - 1) * s / 6 + 
                (z**3 - 3*z) * k / 24 - 
                (2*z**3 - 5*z) * s**2 / 36)
        
        return self.returns.mean() + z_cf * self.returns.std()
    
    def fit_distributions(self) -> Dict[str, Dict[str, Any]]:
        """
        Fit various distributions to the return data.
        
        Returns:
            Dictionary with fitted distribution parameters and goodness-of-fit
        """
        results = {}
        
        # Normal distribution
        norm_params = stats.norm.fit(self.returns)
        norm_ks = stats.kstest(self.returns, 'norm', args=norm_params)
        results['normal'] = {
            'params': {'loc': norm_params[0], 'scale': norm_params[1]},
            'ks_statistic': norm_ks.statistic,
            'ks_pvalue': norm_ks.pvalue
        }
        
        # Student's t distribution (better for fat tails)
        try:
            t_params = stats.t.fit(self.returns)
            t_ks = stats.kstest(self.returns, 't', args=t_params)
            results['student_t'] = {
                'params': {'df': t_params[0], 'loc': t_params[1], 'scale': t_params[2]},
                'ks_statistic': t_ks.statistic,
                'ks_pvalue': t_ks.pvalue
            }
        except Exception as e:
            warnings.warn(f"Student's t fit failed: {e}")
        
        # Generalized Error Distribution (for heavy tails)
        try:
            gennorm_params = stats.gennorm.fit(self.returns)
            gennorm_ks = stats.kstest(self.returns, 'gennorm', args=gennorm_params)
            results['generalized_normal'] = {
                'params': {'beta': gennorm_params[0], 'loc': gennorm_params[1], 'scale': gennorm_params[2]},
                'ks_statistic': gennorm_ks.statistic,
                'ks_pvalue': gennorm_ks.pvalue
            }
        except Exception as e:
            warnings.warn(f"Generalized normal fit failed: {e}")
        
        return results
    
    def get_tail_analysis(self) -> Dict[str, Any]:
        """
        Analyze the tails of the distribution.
        
        Returns:
            Dictionary with tail analysis metrics
        """
        stats_obj = self.compute_basic_stats()
        
        # Tail ratio: ratio of extreme observations to what's expected under normal
        expected_beyond_2std = 0.0455  # ~4.55% for normal
        expected_beyond_3std = 0.0027  # ~0.27% for normal
        
        actual_beyond_2std = (
            (self.returns < self.returns.mean() - 2 * self.returns.std()).sum() +
            (self.returns > self.returns.mean() + 2 * self.returns.std()).sum()
        ) / len(self.returns)
        
        actual_beyond_3std = (
            (self.returns < self.returns.mean() - 3 * self.returns.std()).sum() +
            (self.returns > self.returns.mean() + 3 * self.returns.std()).sum()
        ) / len(self.returns)
        
        return {
            'kurtosis': stats_obj.kurtosis,
            'kurtosis_interpretation': self._interpret_kurtosis(stats_obj.kurtosis),
            'skewness': stats_obj.skewness,
            'skewness_interpretation': self._interpret_skewness(stats_obj.skewness),
            'tail_ratio_2std': actual_beyond_2std / expected_beyond_2std if expected_beyond_2std > 0 else np.nan,
            'tail_ratio_3std': actual_beyond_3std / expected_beyond_3std if expected_beyond_3std > 0 else np.nan,
            'pct_beyond_2std': actual_beyond_2std * 100,
            'pct_beyond_3std': actual_beyond_3std * 100,
            'expected_pct_beyond_2std': expected_beyond_2std * 100,
            'expected_pct_beyond_3std': expected_beyond_3std * 100,
        }
    
    def _interpret_kurtosis(self, kurtosis: float) -> str:
        """Interpret excess kurtosis value."""
        if kurtosis > 1:
            return f"Leptokurtic (fat tails, k={kurtosis:.2f}). Higher probability of extreme events than normal."
        elif kurtosis < -1:
            return f"Platykurtic (thin tails, k={kurtosis:.2f}). Lower probability of extreme events than normal."
        else:
            return f"Approximately mesokurtic (k={kurtosis:.2f}). Similar tail behavior to normal."
    
    def _interpret_skewness(self, skewness: float) -> str:
        """Interpret skewness value."""
        if skewness > 0.5:
            return f"Positively skewed (s={skewness:.2f}). Right tail is longer/fatter."
        elif skewness < -0.5:
            return f"Negatively skewed (s={skewness:.2f}). Left tail is longer/fatter."
        else:
            return f"Approximately symmetric (s={skewness:.2f})."


def analyze_distribution(
    returns: pd.Series,
    periods_per_year: float = 252
) -> Dict[str, Any]:
    """
    Convenience function to perform full distribution analysis.
    
    Args:
        returns: Series of returns
        periods_per_year: Periods per year for annualization
        
    Returns:
        Dictionary with complete analysis results
    """
    analyzer = DistributionAnalyzer(returns, periods_per_year)
    
    return {
        'basic_stats': analyzer.compute_basic_stats().to_dict(),
        'normality_tests': {k: v.__dict__ for k, v in analyzer.test_normality().items()},
        'var': analyzer.compute_var(),
        'tail_analysis': analyzer.get_tail_analysis(),
        'fitted_distributions': analyzer.fit_distributions()
    }
