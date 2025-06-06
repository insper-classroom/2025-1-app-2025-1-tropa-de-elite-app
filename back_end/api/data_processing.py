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

# import argparse
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

def run_merge(
    payers_path: Path,
    sellers_path: Path,
    tx1_path: Path,   # transactions_train (≈ 5M)
    tx2_path: Path    # transactions_test  (≈ 1M)
) -> pd.DataFrame:
    # 1) Lê payers e prepara card_id
    df_payers = pd.read_feather(payers_path)
    if "card_hash" in df_payers.columns:
        df_payers["card_id"] = df_payers["card_hash"]
    df_payers.drop(columns=["card_hash"], inplace=True, errors="ignore")

    # 2) Lê sellers (que NÃO tem card_bin)
    df_sellers = pd.read_feather(sellers_path)

    # 3) Processa tx1_path (train) — Mesmos passos do notebook
    df_tx1 = pd.read_feather(tx1_path)

    df_train = df_tx1.merge(df_sellers, on="terminal_id", how="left")
    df_train = df_train.merge(df_payers, on="card_id", how="left")

    # 4) Processa tx2_path (test) — limpa antes e segue o notebook
    df_tx2 = pd.read_feather(tx2_path)

    # Remove colunas conflitantes que vieram “de fábrica” em tx2
    for c in ["card_bin", "latitude", "longitude"]:
        if c in df_tx2.columns:
            df_tx2 = df_tx2.drop(columns=[c])

    df_test = df_tx2.merge(df_payers, on="card_id", how="left")
    df_test = df_test.merge(df_sellers, on="terminal_id", how="left")

    # 5) Concatena train + test
    df = pd.concat([df_train, df_test], ignore_index=True)

    # 6) Filtra fraudes
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
    """
    Calcula o número de fraudes reportadas para o card_bin de uma transação nos últimos X dias.
    Esta versão é robusta contra NaNs e não depende da ordenação do DataFrame.
    """
    df = df.copy()

    # Etapa 1: Lidar com NaNs na coluna de agrupamento.
    # Preenchemos NaNs com um placeholder para que sejam tratados como um grupo distinto
    # em vez de serem ignorados pelo groupby.
    df['card_bin'] = df['card_bin'].fillna('__NAN_PLACEHOLDER__')

    # Etapa 2: Criar um mapa de fraudes por card_bin (eficiente para consulta).
    # Este mapa contém as datas de reporte de fraude, já ordenadas, para cada card_bin.
    frauds = df.loc[(df['is_fraud']==1) & df['tx_fraud_report_date'].notna(), ['card_bin','tx_fraud_report_date']]
    fraud_map = frauds.groupby('card_bin')['tx_fraud_report_date'].apply(lambda s: np.sort(s.values)).to_dict()

    # Etapa 3: Definir a função que será aplicada a cada grupo do groupby.
    def count_frauds_for_group(group: pd.DataFrame) -> pd.Series:
        bin_id = group.name  # O nome do grupo é o card_bin
        
        # Datas das transações atuais no grupo
        refs = group['tx_datetime'].values.astype('datetime64[ns]')
        
        # Datas de fraude para este card_bin, obtidas do mapa
        fraud_times = fraud_map.get(bin_id, np.array([], dtype='datetime64[ns]'))
        
        # Se não houver fraudes para este bin, o resultado é 0 para todas as transações do grupo.
        if len(fraud_times) == 0:
            return pd.Series(0, index=group.index)

        # Calcula o início da janela de tempo para cada transação
        window_start = refs - np.timedelta64(window_days, 'D')
        
        # Usa searchsorted (muito eficiente) para contar quantas datas de fraude caem na janela [window_start, refs)
        # para cada transação no grupo.
        right_indices = np.searchsorted(fraud_times, refs, side='left')
        left_indices = np.searchsorted(fraud_times, window_start, side='left')
        
        counts = right_indices - left_indices
        
        # Retorna uma Série com as contagens, mantendo o índice original do grupo.
        # Isso é crucial para que o Pandas possa realinhar os resultados corretamente.
        return pd.Series(counts, index=group.index)

    # Etapa 4: Usar groupby().apply() para executar o cálculo.
    # O .apply() itera sobre cada grupo (cada card_bin), chama a função `count_frauds_for_group`,
    # e depois junta os resultados (que são Séries) em uma única Série final, perfeitamente
    # alinhada com o índice original do DataFrame `df`.
    col_name = f'cardbin_fraud_count_last_{window_days}d'
    # group_keys=False evita que a chave de grupo seja adicionada ao índice do resultado.
    fraud_counts_series = df.groupby('card_bin', group_keys=False, sort=False).apply(count_frauds_for_group)
    
    df[col_name] = fraud_counts_series

    # Etapa 5: Restaurar os NaNs originais na coluna, se desejado.
    df['card_bin'] = df['card_bin'].replace('__NAN_PLACEHOLDER__', np.nan)
    
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

def process_pipeline(payers_path: Path, sellers_path: Path, transactions_path_1: Path,transactions_path_2: Path) -> pd.DataFrame:
    df = run_merge(payers_path,sellers_path,transactions_path_1,transactions_path_2)
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

# def main():
#     parser = argparse.ArgumentParser(description="Pipeline completo de merge e features")
#     parser.add_argument("--payers", required=True, type=Path, help="Feather de payers")
#     parser.add_argument("--sellers", required=True, type=Path, help="Feather de sellers")
#     parser.add_argument("--tx1",    required=True, type=Path, help="Primeiro Feather de transações")
#     parser.add_argument("--tx2",    required=True, type=Path, help="Segundo Feather de transações")
#     parser.add_argument("--output", required=True, type=Path, help="Caminho de saída Parquet")
#     args = parser.parse_args()

#     # 1) Merge dos dois datasets de transação + payers + sellers
#     df_merged = process_pipeline(args.payers, args.sellers, args.tx1, args.tx2)

#     # 3) Salva o resultado final
#     args.output.parent.mkdir(parents=True, exist_ok=True)
#     logger.info(f"Salvando resultado em {args.output}")
#     df_merged.to_parquet(args.output, index=False)


# if __name__ == "__main__":
#     main()
