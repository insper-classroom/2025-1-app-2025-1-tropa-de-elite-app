#!/usr/bin/env python3
"""
feature_pipeline.py

Script único que faz:
  1. Mescla payers, sellers e transactions.
  2. Gera todas as features em sequência.
  3. Salva o resultado final em Parquet.

Uso:
  python feature_pipeline.py \
    --payers PATH_Payers.feather \
    --sellers PATH_Sellers.feather \
    --transactions PATH_Transactions.feather \
    --output PATH_Output.parquet

"""

import argparse
import logging
from pathlib import Path
from scipy.stats import vonmises
import numpy as np
import pandas as pd

# Configuração básica de logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_merge(payers_path: Path, sellers_path: Path, transactions_path: Path) -> pd.DataFrame:
    """Lê e mescla payers, sellers e transactions."""
    logger.info(f"Lendo payers de {payers_path}")
    df_payers = pd.read_feather(payers_path)
    # Ajustes em df_payers
    df_payers['card_id'] = df_payers.get('card_hash', df_payers.get('card_id'))
    df_payers.drop(columns=['card_hash'], inplace=True, errors='ignore')

    logger.info(f"Lendo sellers de {sellers_path}")
    df_sellers = pd.read_feather(sellers_path)

    logger.info(f"Lendo transactions de {transactions_path}")
    df_tx = pd.read_feather(transactions_path)
    df_tx['tx_datetime'] = pd.to_datetime(df_tx['tx_datetime'])

    if 'card_first_transaction' in df_payers.columns:
        df_payers['card_first_transaction'] = pd.to_datetime(df_payers['card_first_transaction'])

    # Merge payers
    df = df_tx.merge(df_payers, on='card_id', how='left')
    # Merge sellers
    df = df.merge(df_sellers, on='terminal_id', how='left')

    # Filtra fraudes transacionais e fraudes gerais
    df = df.query("is_transactional_fraud == 0 or is_fraud == 0").copy()

    return df

def generate_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['tx_amount'] = np.log1p(df['tx_amount'])
    df['tx_hour_of_day'] = df['tx_datetime'].dt.hour
    df['tx_dayofweek']   = df['tx_datetime'].dt.weekday

    def assign_regiao(lat):
        if lat > -10:
            return 'Norte'
        elif lat > -20:
            return 'Centro-Oeste'
        else:
            return 'Sudeste'

    df['regiao'] = df['latitude'].apply(assign_regiao)
    return df

def card_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(['card_id','tx_datetime'])
    df['card_age_days']     = (df['tx_datetime'] - pd.to_datetime(df['card_first_transaction'])).dt.days
    df['tx_time_diff_prev'] = df.groupby('card_id')['tx_datetime'].diff().dt.total_seconds().fillna(0)
    df['tx_time_diff_prev'] = np.log10(df['tx_time_diff_prev'] + 1)
    return df

def terminal_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(['terminal_id','tx_datetime'])
    df['terminal_age_days']      = (df['tx_datetime'] - pd.to_datetime(df['terminal_operation_start'])).dt.days
    # Sobrescreve tx_time_diff_prev com base em terminal
    df['tx_time_diff_prev'] = df.groupby('terminal_id')['tx_datetime'].diff().dt.total_seconds().fillna(0)
    return df

def terminal_reuse_ratio(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values(['terminal_id', 'tx_datetime'])
    df['reuse_flag_current']    = df.groupby(['terminal_id','card_id']).cumcount().gt(0).astype(int)
    df['term_reuse_cum_sum']    = df.groupby('terminal_id')['reuse_flag_current'].cumsum()
    df['term_tx_count_prior']   = df.groupby('terminal_id').cumcount()
    df['term_reuse_sum_prior']  = df['term_reuse_cum_sum'] - df['reuse_flag_current']
    df['terminal_card_reuse_ratio_prior'] = (
        df['term_reuse_sum_prior'] / df['term_tx_count_prior'].replace(0, np.nan)
    ).fillna(0)
    df.drop(columns=[
        'reuse_flag_current','term_reuse_cum_sum',
        'term_tx_count_prior','term_reuse_sum_prior'
    ], inplace=True)
    return df

def shared_terminal_with_fraud(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['tx_fraud_report_date'] = pd.to_datetime(df.get('tx_fraud_report_date'), errors='coerce')
    df = df.sort_values(['terminal_id','tx_datetime']).reset_index(drop=True)
    df['shared_terminal_with_frauds_prior'] = 0

    for term, grp in df.groupby('terminal_id', sort=False):
        frauds      = grp[(grp['is_fraud']==1) & grp['tx_fraud_report_date'].notna()].sort_values('tx_fraud_report_date')
        report_dates= frauds['tx_fraud_report_date'].tolist()
        cards       = frauds['card_id'].tolist()
        for idx in grp.index:
            cur_time = df.at[idx, 'tx_datetime']
            seen = {c for rd, c in zip(report_dates, cards) if rd < cur_time}
            df.at[idx, 'shared_terminal_with_frauds_prior'] = len(seen)

    return df

def add_card_fraud_nonfraud_window(df: pd.DataFrame, window_days: int) -> pd.DataFrame:
    df = df.copy()
    df['tx_fraud_report_date'] = pd.to_datetime(df.get('tx_fraud_report_date'), errors='coerce')
    df['tx_fraud_report_date'] = df['tx_fraud_report_date'] + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

    window = pd.Timedelta(days=window_days)
    fraud_counts = pd.Series(0, index=df.index)
    nonfraud_counts = pd.Series(0, index=df.index)

    for card, idx in df.groupby('card_id').groups.items():
        sub = df.loc[idx]
        tx_dates = sub['tx_datetime'].values
        report_dates = np.sort(sub.loc[sub['is_fraud']==1, 'tx_fraud_report_date'].dropna().values)
        nonfraud_dates= np.sort(sub.loc[sub['is_fraud']==0, 'tx_datetime'].values)

        right = np.searchsorted(report_dates, tx_dates, side='left')
        left  = np.searchsorted(report_dates, tx_dates - window, side='left')
        fraud_counts.loc[idx] = (right - left).astype(int)

        right_nf = np.searchsorted(nonfraud_dates, tx_dates, side='left')
        left_nf  = np.searchsorted(nonfraud_dates, tx_dates - window, side='left')
        nonfraud_counts.loc[idx] = (right_nf - left_nf).astype(int)

    df[f'card_fraud_count_last_{window_days}d']    = fraud_counts
    df[f'card_nonfraud_count_last_{window_days}d']= nonfraud_counts
    return df

def generate_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for window in [1, 7]:
        df = add_card_fraud_nonfraud_window(df, window)
    return df

def add_cardbin_fraud_window(df: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    df = df.copy()
    frauds = df.loc[(df['is_fraud']==1) & df['tx_fraud_report_date'].notna(), ['card_bin','tx_fraud_report_date']]
    fraud_map = frauds.groupby('card_bin')['tx_fraud_report_date'].apply(lambda s: np.sort(s.values)).to_dict()

    def count_in_window(times, refs, days):
        start = refs - np.timedelta64(days,'D')
        lo = np.searchsorted(times, start, side='left')
        hi = np.searchsorted(times, refs, side='left')
        return hi - lo

    results = []
    for bin_id, grp in df.groupby('card_bin', sort=False):
        refs = grp['tx_datetime'].values.astype('datetime64[ns]')
        times = fraud_map.get(bin_id, np.array([], dtype='datetime64[ns]'))
        results.append(count_in_window(times, refs, window_days))

    df[f'cardbin_fraud_count_last_{window_days}d'] = np.concatenate(results)
    return df

def generate_card_amount_normalization(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(['card_id','tx_datetime']).reset_index(drop=True)
    df['cum_sum']    = df.groupby('card_id')['tx_amount'].cumsum() - df['tx_amount']
    df['tx_amount_sq']= df['tx_amount']**2
    df['cum_sum2']   = df.groupby('card_id')['tx_amount_sq'].cumsum() - df['tx_amount_sq']
    df['cum_count']  = df.groupby('card_id').cumcount()

    df['mean_prior'] = df['cum_sum']/df['cum_count'].replace(0,np.nan)
    df['var_prior']  = ((df['cum_sum2'] - df['cum_sum']**2/df['cum_count'])/(df['cum_count']-1)).clip(lower=0)
    df['std_prior']  = np.sqrt(df['var_prior'])
    n = df['cum_count'].replace(0,1)
    sigma_min = 100/np.sqrt(n)
    sigma = np.maximum(df['std_prior'].fillna(0), sigma_min)

    df['amount_card_norm_pdf'] = (1/(sigma*np.sqrt(2*np.pi)) * np.exp(-0.5*((df['tx_amount']-df['mean_prior'])/sigma)**2))
    df['amount_card_norm_pdf'] = df['amount_card_norm_pdf'].fillna(0.5).replace([np.inf,-np.inf],0.5)
    df.drop(columns=['cum_sum','cum_sum2','cum_count','tx_amount_sq','mean_prior','var_prior','std_prior'], inplace=True)
    return df

def generate_terminal_amount_normalization(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(['terminal_id','tx_datetime']).reset_index(drop=True)
    df['cum_sum']    = df.groupby('terminal_id')['tx_amount'].cumsum() - df['tx_amount']
    df['tx_amount_sq']= df['tx_amount']**2
    df['cum_sum2']   = df.groupby('terminal_id')['tx_amount_sq'].cumsum() - df['tx_amount_sq']
    df['cum_count']  = df.groupby('terminal_id').cumcount()

    df['mean_prior'] = df['cum_sum']/df['cum_count'].replace(0,np.nan)
    df['var_prior']  = ((df['cum_sum2'] - df['cum_sum']**2/df['cum_count'])/(df['cum_count']-1)).clip(lower=0)
    df['std_prior']  = np.sqrt(df['var_prior'])
    n = df['cum_count'].replace(0,1)
    sigma_min = 100/np.sqrt(n)
    sigma = np.maximum(df['std_prior'].fillna(0), sigma_min)

    df['amount_terminal_norm_pdf'] = (1/(sigma*np.sqrt(2*np.pi)) * np.exp(-0.5*((df['tx_amount']-df['mean_prior'])/sigma)**2))
    df['amount_terminal_norm_pdf'] = df['amount_terminal_norm_pdf'].fillna(0.5).replace([np.inf,-np.inf],0.5)
    df.drop(columns=['cum_sum','cum_sum2','cum_count','tx_amount_sq','mean_prior','var_prior','std_prior'], inplace=True)
    return df

def add_geographical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values(['card_id','tx_datetime'])
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        φ1, λ1 = np.radians(lat1), np.radians(lon1)
        φ2, λ2 = np.radians(lat2), np.radians(lon2)
        dφ = φ2 - φ1
        dλ = λ2 - λ1
        a = np.sin(dφ/2)**2 + np.cos(φ1)*np.cos(φ2)*np.sin(dλ/2)**2
        return R * 2 * np.arcsin(np.sqrt(a))

    df['prev_lat'] = df.groupby('card_id')['latitude'].shift(1)
    df['prev_lon'] = df.groupby('card_id')['longitude'].shift(1)
    df['distancia_entre_transacoes'] = haversine(df['prev_lat'], df['prev_lon'], df['latitude'], df['longitude'])
    df['avg_speed_between_txs'] = (df['distancia_entre_transacoes'] / (df['tx_time_diff_prev']/3600))        .replace([np.inf,-np.inf],800).fillna(0)
    df.drop(columns=['prev_lat','prev_lon','distancia_entre_transacoes'], inplace=True)
    return df

# def soft_redo(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
#     df['merchant'] = df['terminal_soft_descriptor'].str.split().str[0]
#     return df

# def flag_top_merchants(df: pd.DataFrame) -> pd.DataFrame:
#     df = df.copy()
#     top_merchants = ['Prime', 'Physio', 'Ifood', 'Rappi', 'Fusion']
#     df['is_top_merchant'] = df['merchant'].isin(top_merchants).astype(int)
#     return df


def exclude_features(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        'tx_date','tx_fraud_report_date','latitude','longitude',
        'card_id','terminal_id','tx_time',
        'card_first_transaction','terminal_operation_start','terminal_soft_descriptor',
        'is_transactional_fraud', 'merchant','card_bin'
    ]
    return df.drop(columns=cols, errors='ignore')

def process_pipeline(payers_path: Path, sellers_path: Path, transactions_path: Path) -> pd.DataFrame:
    df = run_merge(payers_path, sellers_path, transactions_path)
    logger.info("Gerando basic features...")
    df = generate_basic_features(df)
    logger.info("Gerando card features...")
    df = card_basic_features(df)
    logger.info("Normalizando transações do cartão...")
    df = generate_card_amount_normalization(df)
    logger.info("Gerando terminal features...")
    df = terminal_basic_features(df)
    df = terminal_reuse_ratio(df)
    df = shared_terminal_with_fraud(df)
    logger.info("Gerando temporal features...")
    df = generate_temporal_features(df)
    logger.info("Normalizando transações do terminal...")
    df = generate_terminal_amount_normalization(df)
    logger.info("Gerando features geográficas...")
    df = add_geographical_features(df)
    logger.info("Contando fraudes por card_bin...")
    df = add_cardbin_fraud_window(df)
    logger.info("Ajustando soft descriptor...")
    # df = soft_redo(df)
    # df = flag_top_merchants(df)
    logger.info("Excluindo colunas finais...")
    df = exclude_features(df)
    return df

def main():
    parser = argparse.ArgumentParser(description="Pipeline completo de merge e features")
    parser.add_argument("--payers", required=True, type=Path, help="Feather de payers")
    parser.add_argument("--sellers", required=True, type=Path, help="Feather de sellers")
    parser.add_argument("--transactions", required=True, type=Path, help="Feather de transactions")
    parser.add_argument("--output", required=True, type=Path, help="Caminho de saída Parquet")
    args = parser.parse_args()

    result = process_pipeline(args.payers, args.sellers, args.transactions)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Salvando resultado em {args.output}")
    result.to_parquet(args.output, index=False)

if __name__ == "__main__":
    main()