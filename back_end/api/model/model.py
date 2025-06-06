import pandas as pd
from sklearn.ensemble import VotingClassifier

from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.preprocessing import FunctionTransformer
from imblearn.under_sampling import RandomUnderSampler
from sklearn.ensemble import VotingClassifier
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler, Binarizer, FunctionTransformer
from sklearn.compose import ColumnTransformer
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

import joblib
import numpy as np
import pandas as pd
def bin_shared(X):
        arr = np.asarray(X).ravel()
        binned = pd.cut(
            arr,
            bins=[-0.1, 0, 10, 1424],
            labels=[0, 1, 2],
            include_lowest=True
        ).astype(int)
        return binned.reshape(-1, 1)
     

def lgbm(cat_cols,num_cols):
    params ={'objective': 'tweedie',
 'n_estimators': 250,
 'learning_rate': 0.0099255823164427,
 'max_depth': 6,
 'num_leaves': 57,
 'feature_fraction': 0.8187249687699946,
 'baggin_fraction': 0.5067214069082964,
 'reg_alpha': 0.012659286735004908,
 'reg_lambda': 3.244246362854447e-06,
 'min_child_samples': 26,
 'min_split_gain': 0.9653515585979798,
 'colsample_bytree': 0.6312544465335357,
 'colsample_bylevel': 0.22005799805196546,
 'colsample_bynode': 0.2529270231217465,
 'scale_pos_weight': 3.759044454007167,
 'boosting_type': 'gbdt',
 'drop_rate': 0.3669340989872173,
 'skip_drop': 0.12092826916202082,
         'n_jobs':            -1,
        'verbosity':         -1}
    eff_other_cols = num_cols.copy()
    transformers = [
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=True), cat_cols)
        ]

    if eff_other_cols:
            transformers.append((
                'num_other',
                Pipeline([
                    ('poly',  PolynomialFeatures(degree=2, include_bias=False)),
                    ('scale', StandardScaler(with_mean=False))
                ]),
                eff_other_cols
            ))


    prepro = ColumnTransformer(transformers, remainder='passthrough', sparse_threshold=0.0)
    p_major, p_minor = 0.80, 0.20
    sampling_ratio = p_minor / p_major  # ≃ 0.2857


    rus = RandomUnderSampler(
            sampling_strategy=sampling_ratio,
            random_state=42
        )

        # Montando o pipeline: pré-processamento → TL → RUS → classificador
    model_pipe_lgbm = ImbPipeline([
            ('prepro', prepro),
            ('rus',     rus),
            ('clf', LGBMClassifier(**params))
        ])
    return model_pipe_lgbm

def xgboost(cat_cols, num_cols):
    params={'eval_metric': 'auc',
                'tree_method': 'hist',
        'booster': 'gbtree',
 'eta': 0.12557802707926835,
 'max_depth': 4,
 'min_child_weight': 8,
 'subsample': 0.5441162712748117,
 'colsample_bytree': 0.998115303479888,
 'colsample_bylevel': 0.6752294725537221,
 'gamma': 5.257626815272782,
 'reg_alpha': 0.012368912172746478,
 'reg_lambda': 2.645956310073522,
 'scale_pos_weight': 3.660210661964211,
         'n_jobs':            -1,
        'verbosity':         0}
     
    bin_feats = [
            'avg_speed_between_txs',
            'shared_terminal_with_frauds_prior',
            'card_fraud_count_last_1d',
            'card_fraud_count_last_7d'
        ]


    eff_other_cols = [c for c in num_cols   if c not in bin_feats]

    transformers = [
            ('cat', OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=True), cat_cols)
        ]

    if eff_other_cols:
                transformers.append((
                    'num_other',
                    Pipeline([
                        ('poly',  PolynomialFeatures(degree=2, include_bias=False)),
                        ('scale', StandardScaler(with_mean=False))
                    ]),
                    eff_other_cols
                ))

    transformers += [
                    ('bin_speed',  Binarizer(threshold=100),            ['avg_speed_between_txs']),
            ('disc_shared', FunctionTransformer(bin_shared, validate=False), ['shared_terminal_with_frauds_prior']),
                    ('bin_cf1d',   Binarizer(threshold=0.0),                       ['card_fraud_count_last_1d']),
                    ('bin_cf7d',   Binarizer(threshold=0.0),                       ['card_fraud_count_last_7d']),
                ]

    prepro = ColumnTransformer(transformers, remainder='passthrough', sparse_threshold=0.0)
    p_major, p_minor = 0.80, 0.20
    sampling_ratio   = p_minor / p_major  # ≃ 0.2857

    rus = RandomUnderSampler(
            sampling_strategy=sampling_ratio,
            random_state=42
        )

    model_pipe_xgboost = ImbPipeline([
            ('prepro',     prepro),
            ('undersample', rus),
            ('clf',        XGBClassifier(**params))
        ])
    return model_pipe_xgboost


def voting_class(model_pipe_lgbm, model_pipe_xgboost):
    rus = RandomUnderSampler(sampling_strategy=0.25, random_state=42)

    voting_clf = VotingClassifier(
        estimators=[
            ('lgbm', model_pipe_lgbm),
            ('xgboost', model_pipe_xgboost),
        ],
        voting='soft',
        weights=[1, 1],
        n_jobs=-1
    )

    pipeline_completa = ImbPipeline([
        ('undersampler', rus),
        ('voting',       voting_clf)
    ])
    return pipeline_completa


