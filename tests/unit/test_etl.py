def test_imports():
    import src.data_engine.etl as etl
    import src.data_engine.storage as storage
    assert hasattr(etl, 'run_etl')
    assert hasattr(storage, 'save_df_to_table')
