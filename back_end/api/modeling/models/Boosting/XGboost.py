import numpy as np
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler, Binarizer, FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from xgboost import XGBClassifier
import pandas as pd

def bin_shared(X_input):
    
    data_series = None
    if isinstance(X_input, pd.DataFrame):
        data_series = X_input.iloc[:, 0]
    elif isinstance(X_input, pd.Series):
        data_series = X_input
    elif isinstance(X_input, np.ndarray):
        data_series = pd.Series(X_input.ravel())
    else:
        raise TypeError(f"Tipo de entrada inesperado: {type(X_input)}")

    arr_for_cut = data_series.to_numpy()
    bins = [-0.1, 0, 10, 1424] # Seus bins

    binned_codes = pd.cut(
        arr_for_cut,
        bins=bins,
        labels=False, # Importante!
        include_lowest=True,
        right=True
    )

    binned_series = pd.Series(binned_codes).fillna(-1).astype(int)

    return binned_series.to_numpy().reshape(-1, 1)


def Xgboost_model(cat_cols, num_cols):
    # ... (resto da sua função Xgboost_model como estava, pois ela estava correta)
    params={'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'eta': 0.12557802707926835,
            'max_depth': 4,
            'min_child_weight': 8,
            'subsample': 0.5441162712748117,
            'colsample_bytree': 0.998115303479888,
            'colsample_bylevel': 0.6752294725537221,
            'gamma': 5.257626815272782,
            'reg_alpha': 0.012368912172746478,
            'reg_lambda': 2.645956310073522,
            'scale_pos_weight': 3.660210661964211}

    bin_target_feats = [
        'avg_speed_between_txs',
        'shared_terminal_with_frauds_prior',
        'card_fraud_count_last_1d',
        'card_fraud_count_last_7d'
    ]
    eff_other_cols = [c for c in num_cols if c not in bin_target_feats]
    transformers_list = []

    if cat_cols:
        transformers_list.append(
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=True), cat_cols)
        )
    if eff_other_cols:
        transformers_list.append((
            'num_other',
            Pipeline([
                ('poly',  PolynomialFeatures(degree=2, include_bias=False)),
                ('scale', StandardScaler(with_mean=False))
            ]),
            eff_other_cols
        ))
    if 'avg_speed_between_txs' in num_cols:
        transformers_list.append(
            ('bin_speed', Binarizer(threshold=100), ['avg_speed_between_txs'])
        )
    if 'shared_terminal_with_frauds_prior' in num_cols:
        transformers_list.append(
            ('disc_shared', FunctionTransformer(bin_shared, validate=False), ['shared_terminal_with_frauds_prior'])
        )
    if 'card_fraud_count_last_1d' in num_cols:
        transformers_list.append(
            ('bin_cf1d', Binarizer(threshold=0.0), ['card_fraud_count_last_1d'])
        )
    if 'card_fraud_count_last_7d' in num_cols:
        transformers_list.append(
            ('bin_cf7d', Binarizer(threshold=0.0), ['card_fraud_count_last_7d'])
        )

    prepro = ColumnTransformer(transformers_list, remainder='passthrough', sparse_threshold=0.0)
    # Ajuste sampling_ratio conforme sua estratégia original ou um valor fixo
    # p_major, p_minor = 0.80, 0.20
    # sampling_strategy_val   = p_minor / p_major # Isso é 0.25
    sampling_strategy_val = 0.25 # Ou o valor que você decidiu usar

    rus = RandomUnderSampler(
            sampling_strategy=sampling_strategy_val,
            random_state=42
        )
    model_pipe = ImbPipeline([
            ('prepro',     prepro),
            ('undersample', rus),
            ('clf',        XGBClassifier(**params, random_state=42))
        ])
    return model_pipe


# 'threshold': 0.804907749976376

#                 confusion_matrix  total_gain_amount  best_case_amount  \
# 0    [[565542, 1432], [705, 953]]         1227224.75       1277082.750
# 1  [[534659, 31765], [202, 2006]]         1021534.50       1282018.125
# 2  [[560247, 4324], [2173, 1888]]         1093723.75       1273898.875
# 3   [[564882, 1376], [105, 2269]]         1269404.50       1279997.250
# 4    [[565060, 747], [148, 2677]]         1273127.50       1282444.875

#    gain_per_transaction  portion_of_max    amount_loss  fold  threshold
# 0              0.028766        0.960959   45829.441406     1   0.804908
# 1              0.023836        0.796818   11210.660156     2   0.804908
# 2              0.025604        0.858564  162512.968750     3   0.804908
# 3              0.029664        0.991724    7066.040039     4   0.804908
# 4              0.029678        0.992735    7416.240234     5   0.804908
