def train_test_split_unbalanced(df):
    train = df[(df['tx_date'] >= '2018-01-01') & (df['tx_date'] <= '2018-04-30')]
    test   = df[(df['tx_date'] > '2018-05-01') & (df['tx_date'] <= '2018-05-31')]

    X_train = train.drop(columns=['tx_date','is_fraud','merchant'])
    y_train = train['is_fraud']
    X_val   = test.drop(columns=['tx_date','is_fraud','merchant'])
    y_val   = test['is_fraud']
    return X_train, y_train, X_val, y_val