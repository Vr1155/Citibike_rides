class _StaticLagModel:
    def __init__(self, lag_col: str):
        self.lag_col = lag_col
    def fit(self, X, y=None):   # nothing to fit
        return self
    def predict(self, X):
        return X[self.lag_col].to_numpy()

LastHourBaseline = lambda lag_col="rides_t-1": _StaticLagModel(lag_col)
LastDayBaseline  = lambda lag_col="rides_t-24": _StaticLagModel(lag_col)
LastWeekBaseline = lambda lag_col="rides_t-168": _StaticLagModel(lag_col)
